#!/usr/bin/env python3
"""Local Discord token inspector and bulk checker.

Serves a small web UI on 127.0.0.1. Tokens are held in memory for the
duration of one request, sent only to discord.com, and are never logged.

Bulk mode mirrors the command-line checker: it accepts one token per line
(or email:password:token combos), reports the same fields, and can
optionally write the categorized lists to the output/ folder.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener, urlopen

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
OUTPUT_DIR = BASE_DIR / "output"
TOKENS_FILE = BASE_DIR / "tokens.txt"
DISCORD_API = "https://discord.com/api/v9"
DISCORD_EPOCH_MS = 1420070400000
TIMEOUT_SECONDS = 10
MAX_BODY_BYTES = 16 * 1024
MAX_BULK_BODY_BYTES = 2 * 1024 * 1024
MAX_BULK_TOKENS = 500
BULK_DELAY_SECONDS = 0.1

PREMIUM_TYPES = {
    0: "None",
    1: "Nitro Classic",
    2: "Nitro",
    3: "Nitro Basic",
}

SUBSCRIPTION_TYPES = {
    1: "Nitro Classic",
    2: "Nitro",
    3: "Nitro Basic",
    4: "Nitro Premium",
    5: "Nitro Boost",
}

CONNECTION_TYPES = {
    1: "Steam",
    2: "Twitch",
    3: "Spotify",
    4: "Xbox",
    5: "GitHub",
    6: "YouTube",
    7: "Battle.net",
    8: "League of Legends",
    9: "Skype",
    10: "Facebook",
    11: "Twitter",
    12: "Reddit",
    13: "Discord",
    14: "Riot Games",
    15: "PlayStation Network",
    16: "Epic Games",
    17: "TikTok",
    18: "Roblox",
}

FLAG_LABELS = {
    1 << 0: "Discord Staff",
    1 << 1: "Partner",
    1 << 2: "HypeSquad Events",
    1 << 3: "Bug Hunter",
    1 << 6: "HypeSquad Bravery",
    1 << 7: "HypeSquad Brilliance",
    1 << 8: "HypeSquad Balance",
    1 << 9: "Early Supporter",
    1 << 10: "Team Pseudo User",
    1 << 14: "Bug Hunter Level 2",
    1 << 16: "Verified Bot",
    1 << 17: "Early Verified Bot Developer",
    1 << 18: "Certified Moderator",
    1 << 19: "HTTP Interactions Bot",
    1 << 22: "Active Developer",
}

OUTPUT_FILES = {
    "nitro": "nitro.txt",
    "email_verified": "email_verified.txt",
    "redeemable": "redeemable.txt",
    "trial_1month": "trial_1month.txt",
    "trial_2week": "trial_2week.txt",
}


class TokenError(ValueError):
    """Raised when the pasted value is not a single, plausible token."""


def normalize_token(raw: object) -> str:
    """Return just the token part of a raw line.

    Accepts a bare token or the email:password:token combos handled by
    main.py. Never returns a line containing account credentials.
    """
    if not isinstance(raw, str):
        raise TokenError("Paste a token first.")

    line = raw.strip()
    if not line:
        raise TokenError("Paste a token first.")
    if ":" in line:
        line = line.rsplit(":", 1)[-1].strip()

    token = line
    if not token:
        raise TokenError("Paste a token first.")
    if any(ch.isspace() for ch in token):
        raise TokenError("The token contains whitespace.")
    if not 50 <= len(token) <= 300:
        raise TokenError("That doesn't look like a Discord token.")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", token):
        raise TokenError("That doesn't look like a Discord token.")
    return token


def mask_token(token: object) -> str:
    if not isinstance(token, str) or len(token) <= 20:
        return "INVALID_FORMAT"
    return token[:15] + "..." + token[-5:]


def discord_request(
    path: str,
    token: str,
    method: str = "GET",
    payload: dict | None = None,
    proxy: str | None = None,
) -> tuple[int | None, object]:
    headers = {
        "Authorization": token,
        "Accept": "application/json",
        "User-Agent": "HackersChecker/2.0",
    }
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(
        DISCORD_API + path,
        data=body,
        headers=headers,
        method=method,
    )
    if proxy:
        opener = build_opener(
            ProxyHandler({"http": proxy, "https": proxy})
        ).open
    else:
        opener = urlopen

    try:
        with opener(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read()
            try:
                return response.status, json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return response.status, None
    except HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return exc.code, None
    except (URLError, TimeoutError, OSError):
        return None, None


def describe_failure(status: int | None, payload: object) -> str:
    if status is None:
        return "Could not reach Discord. Check your connection and try again."

    code = payload.get("code") if isinstance(payload, dict) else None
    if status == 401:
        return "Invalid or expired token."
    if status == 403 and code == 20002:
        return "This account is locked by Discord."
    if status == 403:
        return "Discord refused the request (403). The token may be locked or restricted."
    if status == 429:
        retry_after = payload.get("retry_after") if isinstance(payload, dict) else None
        if isinstance(retry_after, (int, float)):
            return f"Rate limited by Discord. Try again in {retry_after:.1f}s."
        return "Rate limited by Discord. Try again in a moment."
    if status >= 500:
        return "Discord is having trouble right now. Try again shortly."
    return f"Discord returned HTTP {status}."


def describe_short(status: int | None) -> str:
    return "network error" if status is None else f"HTTP {status}"


def note_failure(notes: list[str], label: str, status: int | None) -> None:
    if status != 200:
        notes.append(f"{label} unavailable ({describe_short(status)}).")


def snowflake_created_at(snowflake: object) -> datetime | None:
    try:
        timestamp_ms = (int(snowflake) >> 22) + DISCORD_EPOCH_MS
        return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def flag_labels(flags: object) -> list[str]:
    if not isinstance(flags, int):
        return []
    return [label for bit, label in FLAG_LABELS.items() if flags & bit]


def avatar_url(user: dict) -> str:
    user_id = user.get("id")
    avatar_hash = user.get("avatar")
    if user_id and avatar_hash:
        extension = "gif" if str(avatar_hash).startswith("a_") else "png"
        return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{extension}?size=128"

    try:
        user_id_int = int(user_id)
        discriminator = str(user.get("discriminator") or "0")
        if discriminator.isdigit() and discriminator != "0":
            index = int(discriminator) % 5
        else:
            index = (user_id_int >> 22) % 6
    except (TypeError, ValueError):
        index = 0
    return f"https://cdn.discordapp.com/embed/avatars/{index}.png"


def banner_url(user: dict) -> str | None:
    user_id = user.get("id")
    banner_hash = user.get("banner")
    if not user_id or not banner_hash:
        return None
    extension = "gif" if str(banner_hash).startswith("a_") else "png"
    return f"https://cdn.discordapp.com/banners/{user_id}/{banner_hash}.{extension}?size=600"


def guild_icon_url(guild: dict) -> str | None:
    guild_id = guild.get("id")
    icon_hash = guild.get("icon")
    if not guild_id or not icon_hash:
        return None
    extension = "gif" if str(icon_hash).startswith("a_") else "png"
    return f"https://cdn.discordapp.com/icons/{guild_id}/{icon_hash}.{extension}?size=64"


def mask_phone(phone: object) -> str | None:
    if not isinstance(phone, str) or not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if not digits:
        return None
    if len(digits) <= 4:
        return "\u2022" * len(digits)
    return "\u2022" * (len(digits) - 4) + digits[-4:]


def build_profile(user: dict) -> dict:
    created_at = snowflake_created_at(user.get("id"))
    age_days = None
    if created_at is not None:
        age_days = max(0, (datetime.now(timezone.utc) - created_at).days)

    try:
        premium_type = int(user.get("premium_type") or 0)
    except (TypeError, ValueError):
        premium_type = 0
    accent_color = user.get("accent_color")

    email_verified = bool(user.get("verified"))
    phone_verified = user.get("phone") is not None

    if email_verified and phone_verified:
        verification_key = "fully"
        verification_label = "Fully Verified"
    elif email_verified:
        verification_key = "email"
        verification_label = "Email Verified"
    else:
        verification_key = "unverified"
        verification_label = "Unverified"

    return {
        "id": str(user.get("id") or ""),
        "username": user.get("username") or "",
        "global_name": user.get("global_name") or None,
        "discriminator": str(user.get("discriminator") or "0"),
        "avatar_url": avatar_url(user),
        "banner_url": banner_url(user),
        "accent_color": (
            f"#{accent_color:06x}" if isinstance(accent_color, int) else None
        ),
        "email": user.get("email"),
        "email_verified": email_verified,
        "phone_verified": phone_verified,
        "phone_masked": mask_phone(user.get("phone")),
        "mfa_enabled": bool(user.get("mfa_enabled")),
        "locale": user.get("locale"),
        "premium_type": premium_type,
        "premium_label": PREMIUM_TYPES.get(premium_type, "Unknown"),
        "flags": flag_labels(user.get("public_flags") or user.get("flags") or 0),
        "created_at": created_at.isoformat() if created_at else None,
        "age_days": age_days,
        "bot": bool(user.get("bot")),
        "system": bool(user.get("system")),
        "verification_key": verification_key,
        "verification_label": verification_label,
    }


def parse_iso_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def summarize_subscriptions(
    status: int | None,
    payload: object,
    notes: list[str],
) -> dict:
    result = {
        "has_subscription": False,
        "nitro_type": "No Nitro",
        "nitro_days": 0,
        "subscriptions": [],
    }

    if status != 200 or not isinstance(payload, list):
        note_failure(notes, "Subscriptions", status)
        return result

    for subscription in payload:
        if not isinstance(subscription, dict):
            continue

        subscription_type = subscription.get("type")
        label = SUBSCRIPTION_TYPES.get(
            subscription_type, f"Type {subscription_type}"
        )
        trial_days = 0
        trial_end = parse_iso_datetime(subscription.get("trial_ended_at"))
        if trial_end is not None:
            delta = trial_end - datetime.now(timezone.utc)
            trial_days = max(0, delta.days)
            label = f"{label} {trial_days} Days"

        result["has_subscription"] = True
        result["nitro_type"] = label
        result["nitro_days"] = trial_days
        result["subscriptions"].append(
            {
                "type": subscription_type,
                "label": label,
                "trial_days": trial_days,
                "trial_ends_at": (
                    trial_end.isoformat() if trial_end is not None else None
                ),
            }
        )

    return result


def count_boosts(status: int | None, payload: object, notes: list[str]) -> int:
    if status != 200 or not isinstance(payload, list):
        note_failure(notes, "Boost list", status)
        return 0
    return len(payload)


def count_payment_sources(
    status: int | None,
    payload: object,
    notes: list[str],
) -> int:
    if status != 200 or not isinstance(payload, list):
        note_failure(notes, "Payment sources", status)
        return 0
    return len(payload)


def check_trial(
    token: str,
    notes: list[str],
    proxy: str | None = None,
) -> str:
    """Check for a Nitro trial offer, mirroring main.py."""
    status, payload = discord_request(
        "/users/@me/billing/user-offer",
        token,
        method="POST",
        payload={},
        proxy=proxy,
    )
    if status != 200 or not isinstance(payload, dict):
        note_failure(notes, "Trial offer", status)
        return "No Trial"

    offer = payload.get("user_trial_offer")
    if offer is None and "trial_id" in payload:
        offer = payload

    if isinstance(offer, dict) and "trial_id" in offer:
        trial_id = str(offer["trial_id"])
        if trial_id.startswith("5"):
            return "1 Month"
        if trial_id.startswith("9"):
            return "2 Week"
        return f"Trial ({trial_id[:4]}...)"

    return "No Trial"


def classify_account(profile: dict, billing: dict) -> str:
    """Return the same category buckets used by the checker dashboard.

    nitro_2x / nitro_1x / nitro count Nitro accounts by boost slots.
    Trial buckets are split by FV (fully verified) and EV (email verified).
    """
    verification = profile.get("verification_key")
    trial_status = billing.get("trial_status")
    boosts = int(billing.get("boost_count") or 0)

    if billing.get("has_subscription"):
        if boosts >= 2:
            return "nitro_2x"
        if boosts == 1:
            return "nitro_1x"
        return "nitro"

    if trial_status == "1 Month":
        return "trial_1m_fv" if verification == "fully" else "trial_1m_ev"
    if trial_status == "2 Week":
        return "trial_2w_fv" if verification == "fully" else "trial_2w_ev"
    if verification == "fully":
        return "fv"
    if verification == "email":
        return "ev"
    return "other"


def build_guilds(status: int | None, payload: object, notes: list[str]) -> dict:
    if status != 200 or not isinstance(payload, list):
        notes.append(f"Guild list unavailable ({describe_short(status)}).")
        return {"count": 0, "owned": 0, "admin": 0, "items": []}

    items = []
    for guild in payload:
        if not isinstance(guild, dict):
            continue

        permissions = guild.get("permissions")
        try:
            is_admin = bool(int(permissions) & 0x8) if permissions is not None else False
        except (TypeError, ValueError):
            is_admin = False

        items.append(
            {
                "id": str(guild.get("id") or ""),
                "name": guild.get("name") or "Unknown",
                "icon_url": guild_icon_url(guild),
                "owner": bool(guild.get("owner")),
                "admin": is_admin,
            }
        )

    items.sort(key=lambda item: (not item["owner"], not item["admin"], item["name"].lower()))
    return {
        "count": len(items),
        "owned": sum(1 for item in items if item["owner"]),
        "admin": sum(1 for item in items if item["admin"]),
        "items": items,
    }


def build_connections(status: int | None, payload: object, notes: list[str]) -> dict:
    if status != 200 or not isinstance(payload, list):
        notes.append(f"Connections unavailable ({describe_short(status)}).")
        return {"count": 0, "items": []}

    items = []
    for connection in payload:
        if not isinstance(connection, dict):
            continue

        connection_type = connection.get("type")
        if isinstance(connection_type, str) and connection_type.isdigit():
            connection_type = int(connection_type)

        items.append(
            {
                "type": connection_type,
                "type_label": CONNECTION_TYPES.get(
                    connection_type, f"Type {connection_type}"
                ),
                "name": connection.get("name") or "Unknown",
                "verified": bool(connection.get("verified")),
            }
        )

    items.sort(key=lambda item: item["type_label"])
    return {"count": len(items), "items": items}


def inspect_token(token: str, proxy: str | None = None) -> dict:
    """Check a single normalized token against every endpoint used by main.py."""
    masked = mask_token(token)
    status, user = discord_request("/users/@me", token, proxy=proxy)

    if status == 403 and isinstance(user, dict) and user.get("code") == 20002:
        return {
            "ok": False,
            "status": "Locked",
            "locked": True,
            "token_masked": masked,
            "category": "locked",
            "error": "This account is locked by Discord.",
        }

    if status != 200 or not isinstance(user, dict):
        return {
            "ok": False,
            "status": "Invalid",
            "locked": False,
            "token_masked": masked,
            "category": "invalid",
            "error": describe_failure(status, user),
        }

    notes: list[str] = []
    endpoints = {
        "guilds": "/users/@me/guilds",
        "connections": "/users/@me/connections",
        "subscriptions": "/users/@me/billing/subscriptions",
        "boosts": "/users/@me/guilds/premium/subscriptions",
        "payments": "/users/@me/billing/payment-sources",
    }

    with ThreadPoolExecutor(max_workers=len(endpoints)) as pool:
        futures = {
            name: pool.submit(
                discord_request,
                path,
                token,
                "GET",
                None,
                proxy,
            )
            for name, path in endpoints.items()
        }
        responses = {name: future.result() for name, future in futures.items()}

    guilds_status, guilds_payload = responses["guilds"]
    connections_status, connections_payload = responses["connections"]
    subscriptions_status, subscriptions_payload = responses["subscriptions"]
    boosts_status, boosts_payload = responses["boosts"]
    payments_status, payments_payload = responses["payments"]

    billing = summarize_subscriptions(
        subscriptions_status, subscriptions_payload, notes
    )
    billing["boost_count"] = count_boosts(boosts_status, boosts_payload, notes)
    billing["payment_sources"] = count_payment_sources(
        payments_status, payments_payload, notes
    )
    billing["has_payment"] = billing["payment_sources"] > 0
    billing["redeemable"] = not billing["has_subscription"]
    billing["redeemable_label"] = (
        "Redeemable" if billing["redeemable"] else "Not Redeemable"
    )

    if billing["has_subscription"]:
        billing["trial_status"] = "No Trial"
    else:
        billing["trial_status"] = check_trial(token, notes, proxy)

    profile = build_profile(user)
    return {
        "ok": True,
        "status": "Valid",
        "locked": False,
        "token_masked": masked,
        "category": classify_account(profile, billing),
        "profile": profile,
        "billing": billing,
        "guilds": build_guilds(guilds_status, guilds_payload, notes),
        "connections": build_connections(
            connections_status, connections_payload, notes
        ),
        "notes": notes,
    }


CATEGORY_KEYS = (
    "nitro_2x",
    "nitro_1x",
    "nitro",
    "trial_1m_fv",
    "trial_1m_ev",
    "trial_2w_fv",
    "trial_2w_ev",
    "fv",
    "ev",
    "other",
)


def summarize_bulk(results: list[dict]) -> dict:
    summary = {
        "total": len(results),
        "checked": len(results),
        "locked": 0,
        "invalid": 0,
        "redeemable": 0,
        "boosts": 0,
        **{key: 0 for key in CATEGORY_KEYS},
    }

    for result in results:
        if not result.get("ok"):
            if result.get("locked"):
                summary["locked"] += 1
            else:
                summary["invalid"] += 1
            continue

        category = result.get("category")
        if category in summary:
            summary[category] += 1

        billing = result.get("billing") or {}
        if billing.get("redeemable"):
            summary["redeemable"] += 1
        summary["boosts"] += int(billing.get("boost_count") or 0)

    summary["valid"] = summary["total"] - summary["locked"] - summary["invalid"]
    summary["not_redeemable"] = summary["valid"] - summary["redeemable"]
    summary["nitro_total"] = (
        summary["nitro_2x"] + summary["nitro_1x"] + summary["nitro"]
    )
    summary["trial_1month"] = (
        summary["trial_1m_fv"] + summary["trial_1m_ev"]
    )
    summary["trial_1month_fv"] = summary["trial_1m_fv"]
    summary["trial_1month_ev"] = summary["trial_1m_ev"]
    summary["trial_2week"] = (
        summary["trial_2w_fv"] + summary["trial_2w_ev"]
    )
    summary["trial_2week_fv"] = summary["trial_2w_fv"]
    summary["trial_2week_ev"] = summary["trial_2w_ev"]
    summary["fully_verified"] = summary["fv"]
    summary["email_verified"] = summary["ev"]

    return summary


def save_output_lists(lines: list[str], results: list[dict]) -> dict:
    """Write the same categorized lists as main.py."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    buckets: dict[str, list[str]] = {name: [] for name in OUTPUT_FILES}

    for line, result in zip(lines, results):
        if not result.get("ok"):
            continue

        billing = result.get("billing") or {}
        profile = result.get("profile") or {}
        verification = profile.get("verification_key")

        if verification == "fully" and billing.get("has_subscription"):
            buckets["nitro"].append(line)
        if verification == "email":
            buckets["email_verified"].append(line)
        if billing.get("redeemable"):
            buckets["redeemable"].append(line)

        trial_status = billing.get("trial_status")
        if trial_status == "1 Month":
            buckets["trial_1month"].append(line)
        elif trial_status == "2 Week":
            buckets["trial_2week"].append(line)

    counts = {}
    for name, filename in OUTPUT_FILES.items():
        path = OUTPUT_DIR / filename
        entries = buckets[name]
        path.write_text(
            "".join(f"{entry}\n" for entry in entries),
            encoding="utf-8",
        )
        counts[name] = len(entries)
    return {"ok": True, "directory": "output", "counts": counts}


def save_output_buckets(buckets: object) -> dict:
    """Write the categorized lists produced by the browser checker."""
    if not isinstance(buckets, dict):
        buckets = {}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    for name, filename in OUTPUT_FILES.items():
        raw_entries = buckets.get(name)
        entries: list[str] = []
        if isinstance(raw_entries, list):
            for entry in raw_entries[:MAX_BULK_TOKENS]:
                if isinstance(entry, str) and entry.strip():
                    entries.append(entry.strip())

        (OUTPUT_DIR / filename).write_text(
            "".join(f"{entry}\n" for entry in entries),
            encoding="utf-8",
        )
        counts[name] = len(entries)

    return {"ok": True, "directory": "output", "counts": counts}


def inspect_bulk(raw_text: str, save_outputs: bool = False) -> dict:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return {"ok": False, "error": "Paste at least one token."}
    if len(lines) > MAX_BULK_TOKENS:
        return {
            "ok": False,
            "error": (
                f"Too many tokens. The web checker accepts up to "
                f"{MAX_BULK_TOKENS} per run."
            ),
        }

    results: list[dict] = []
    start_time = time.time()

    for index, line in enumerate(lines):
        try:
            token = normalize_token(line)
        except TokenError as exc:
            results.append(
                {
                    "index": index,
                    "ok": False,
                    "status": "Invalid",
                    "locked": False,
                    "token_masked": mask_token(line.rsplit(":", 1)[-1]),
                    "category": "invalid",
                    "error": str(exc),
                }
            )
            continue

        try:
            result = inspect_token(token)
        except Exception:
            result = {
                "ok": False,
                "status": "Invalid",
                "locked": False,
                "token_masked": mask_token(token),
                "error": "The local checker could not finish this token.",
            }

        result["index"] = index
        results.append(result)
        time.sleep(BULK_DELAY_SECONDS)

    saved = None
    if save_outputs:
        try:
            saved = save_output_lists(lines, results)
        except OSError:
            saved = {
                "ok": False,
                "error": "Could not write the output/ files.",
            }

    return {
        "ok": True,
        "results": results,
        "summary": summarize_bulk(results),
        "elapsed": round(time.time() - start_time, 2),
        "saved": saved,
    }


class AppHandler(BaseHTTPRequestHandler):
    server_version = "HackersChecker/2.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: object) -> None:
        # Keep request details (and anything token-adjacent) out of the console.
        return

    def _common_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Robots-Tag", "noindex, nofollow")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=()",
        )
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; "
            "img-src 'self' https://cdn.discordapp.com data:; "
            "style-src 'self'; "
            "script-src 'self'; "
            "connect-src 'self'; "
            "base-uri 'none'; "
            "form-action 'self'; "
            "frame-ancestors 'none'",
        )

    def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self._common_headers()
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self._send_bytes(status, body, "application/json; charset=utf-8")

    def _serve_web_file(self, filename: str, content_type: str) -> None:
        try:
            body = (WEB_DIR / filename).read_bytes()
        except OSError:
            self._send_json(500, {"ok": False, "error": "Web UI file is missing."})
            return
        self._send_bytes(200, body, content_type)

    def _read_json_body(self, max_bytes: int) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            length = 0

        if length <= 0 or length > max_bytes:
            self.close_connection = True
            self._send_json(400, {"ok": False, "error": "Invalid request."})
            return None

        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"ok": False, "error": "Invalid JSON."})
            return None

        if not isinstance(payload, dict):
            self._send_json(400, {"ok": False, "error": "Invalid request."})
            return None
        return payload

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        routes = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/index.html": ("index.html", "text/html; charset=utf-8"),
            "/style.css": ("style.css", "text/css; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            "/assets/logo.png": ("assets/logo.png", "image/png"),
            "/assets/hero.png": ("assets/hero.png", "image/png"),
            "/assets/texture.png": ("assets/texture.png", "image/png"),
            "/assets/favicon.png": ("assets/favicon.png", "image/png"),
        }

        if path in routes:
            self._serve_web_file(*routes[path])
        elif path == "/api/health":
            self._send_json(200, {"ok": True})
        elif path == "/api/tokens-file":
            try:
                text = TOKENS_FILE.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                self._send_json(404, {"ok": False, "error": "tokens.txt not found."})
            else:
                self._send_json(200, {"ok": True, "tokens": text})
        elif path == "/favicon.ico":
            self._send_bytes(204, b"", "image/x-icon")
        else:
            self._send_json(404, {"ok": False, "error": "Not found."})

    def do_POST(self) -> None:
        path = urlparse(self.path).path

        if path == "/api/check":
            payload = self._read_json_body(MAX_BODY_BYTES)
            if payload is None:
                return

            try:
                token = normalize_token(payload.get("token"))
            except TokenError as exc:
                self._send_json(400, {"ok": False, "error": str(exc)})
                return

            proxy = payload.get("proxy")
            if isinstance(proxy, str):
                proxy = proxy.strip() or None
            else:
                proxy = None
            if proxy is not None and not re.match(r"^https?://", proxy, re.I):
                self._send_json(
                    400,
                    {
                        "ok": False,
                        "error": "Only http:// and https:// proxies are supported.",
                    },
                )
                return

            self._send_json(200, inspect_token(token, proxy))
            return

        if path == "/api/save-output":
            payload = self._read_json_body(MAX_BULK_BODY_BYTES)
            if payload is None:
                return

            try:
                saved = save_output_buckets(payload.get("buckets"))
            except OSError:
                self._send_json(
                    500,
                    {"ok": False, "error": "Could not write the output/ files."},
                )
                return
            self._send_json(200, saved)
            return

        if path == "/api/check-bulk":
            payload = self._read_json_body(MAX_BULK_BODY_BYTES)
            if payload is None:
                return

            raw_tokens = payload.get("tokens")
            if not isinstance(raw_tokens, str):
                self._send_json(
                    400, {"ok": False, "error": "Paste at least one token."}
                )
                return

            result = inspect_bulk(raw_tokens, bool(payload.get("save")))
            self._send_json(200 if result.get("ok") else 400, result)
            return

        self._send_json(404, {"ok": False, "error": "Not found."})


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Local Discord token inspector and bulk checker."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8000")),
        help="Port to listen on (default: 8000 or $PORT).",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the UI in your default browser.",
    )
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), AppHandler)
    url = f"http://127.0.0.1:{args.port}/"

    print(f"Hackers Checker running at {url}", flush=True)
    print(
        "Local only (127.0.0.1). Tokens are never logged. Categorized results are saved to output/ after each run. Press Ctrl+C to stop.",
        flush=True,
    )

    if args.open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
