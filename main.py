from datetime import datetime
import json
import os
import time
import requests
from colorama import Fore, Style, init

init(autoreset=True)

# Shady colors - Clean Dark Grey mix (No invisible black text)
SHADY_COLORS = [Fore.LIGHTBLACK_EX, Fore.WHITE, Fore.LIGHTBLACK_EX]

def shady(text):
    """Apply shady gradient effect"""
    result = ""
    for i, ch in enumerate(text):
        color = SHADY_COLORS[i % len(SHADY_COLORS)]
        result += color + ch
    return result + Style.RESET_ALL

BANNER = f"""{Fore.LIGHTBLACK_EX}
███████╗███████╗███   ██╗██╗  ██╗ █████╗ ██╗
╚══██╔╝██╔════╝██╔══██╗██║ ██╔╝██╔══██╗██║
    ██║ █████╗  ██████╔╝█████╔╝ ███████║██║
    ██║ ██╔══╝  ██╔══██╗██╔═██╗ ██╔══██║██║
    ██║ ███████╗██║  ██║██║  ██║██║  ██║██║
    ╚═╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝
         Zenkai Token Checker v3.0
{Style.RESET_ALL}"""

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def get_account_age(snowflake_id):
    try:
        timestamp = ((int(snowflake_id) >> 22) + 1420070400000) / 1000
        created_at = datetime.fromtimestamp(timestamp)
        delta = datetime.now() - created_at
        return delta.days
    except:
        return 0

def check_trial(token, headers):
    """Check for Nitro trial (1 month or 2 week)"""
    try:
        r = requests.post(
            "https://discord.com/api/v9/users/@me/billing/user-offer",
            headers=headers,
            json={},
            timeout=5
        )
        
        if r.status_code == 200:
            data = r.json()
            
            # Check if trial offer exists
            offer = data.get('user_trial_offer')
            if offer is None and isinstance(data, dict) and 'trial_id' in data:
                offer = data
                
            if offer and isinstance(offer, dict) and 'trial_id' in offer:
                trial_id = str(offer['trial_id'])
                if trial_id.startswith('5'):
                    return "1 Month"
                elif trial_id.startswith('9'):
                    return "2 Week"
                else:
                    return f"Trial ({trial_id[:4]}...)"
        
        return "No Trial"
    except:
        return "No Trial"

def check_token(raw_line):
    raw_line = raw_line.strip()
    if not raw_line:
        return "Empty", None

    original_line = raw_line
    if ":" in raw_line:
        parts = raw_line.split(":")
        token = parts[-1].strip()
    else:
        token = raw_line

    headers = {"Authorization": token, "Content-Type": "application/json"}
    masked_token = (token[:15] + "..." + token[-5:]) if len(token) > 20 else "INVALID_FORMAT"
    
    current_time = datetime.now().strftime("%H:%M:%S")

    try:
        r_user = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=5)

        if r_user.status_code == 403:
            data = r_user.json()
            if data.get("code") == 20002:
                print(
                    f"[{Fore.LIGHTBLACK_EX}{current_time}{Style.RESET_ALL}] "
                    f"[{Fore.RED}LOCKED{Style.RESET_ALL}] "
                    f"{Fore.LIGHTBLACK_EX}token:{Style.RESET_ALL} {Fore.CYAN}{masked_token}{Style.RESET_ALL}"
                )
                return "Locked", None, None

        if r_user.status_code != 200:
            print(
                f"[{Fore.LIGHTBLACK_EX}{current_time}{Style.RESET_ALL}] "
                f"[{Fore.RED}BAD{Style.RESET_ALL}] "
                f"{Fore.LIGHTBLACK_EX}token:{Style.RESET_ALL} {Fore.CYAN}{masked_token}{Style.RESET_ALL}"
            )
            return "Invalid", None, None

        user_data = r_user.json()
        user_id = user_data.get("id")
        verified = user_data.get("verified", False)
        phone_verified = user_data.get("phone") is not None
        age_days = get_account_age(user_id)

        if verified and phone_verified:
            type_status = f"{Fore.GREEN}Fully Verified{Style.RESET_ALL}"
            type_key = "fully"
        elif verified:
            type_status = f"{Fore.GREEN}Email Verified{Style.RESET_ALL}"
            type_key = "email"
        else:
            type_status = f"{Fore.RED}Unverified{Style.RESET_ALL}"
            type_key = "unverified"

        r_billing = requests.get(
            "https://discord.com/api/v9/users/@me/billing/subscriptions",
            headers=headers,
            timeout=5,
        )
        
        nitro_type = "No Nitro"
        has_subscription = False
        nitro_days = 0
        
        if r_billing.status_code == 200:
            subs = r_billing.json()
            if subs:
                has_subscription = True
                for sub in subs:
                    if sub.get("type") == 1:
                        nitro_type = "Nitro Classic"
                    elif sub.get("type") == 2:
                        nitro_type = "Nitro"
                    elif sub.get("type") == 3:
                        nitro_type = "Nitro Basic"
                    elif sub.get("type") == 4:
                        nitro_type = "Nitro Premium"
                    elif sub.get("type") == 5:
                        nitro_type = "Nitro Boost"
                    else:
                        nitro_type = f"Type {sub.get('type')}"
                    
                    if sub.get("trial_ended_at"):
                        trial_end = datetime.fromisoformat(sub["trial_ended_at"].replace("Z", "+00:00"))
                        delta = trial_end - datetime.now(trial_end.tzinfo)
                        nitro_days = max(0, delta.days)
                        nitro_type = f"{nitro_type} {nitro_days} Days"

        r_boosts = requests.get(
            "https://discord.com/api/v9/users/@me/guilds/premium/subscriptions",
            headers=headers,
            timeout=5,
        )
        
        boost_count = 0
        if r_boosts.status_code == 200:
            boost_count = len(r_boosts.json())

        r_payments = requests.get(
            "https://discord.com/api/v9/users/@me/billing/payment-sources",
            headers=headers,
            timeout=5,
        )
        
        is_redeemable = "Redeemable" if not has_subscription else "Not Redeemable"
        
        has_payment = False
        if r_payments.status_code == 200 and len(r_payments.json()) > 0:
            has_payment = True

        # Check trial if no subscription
        trial_status = "No Trial"
        if not has_subscription:
            trial_status = check_trial(token, headers)

        # Trial status ALWAYS magenta - no shady
        trial_display = f"{Fore.MAGENTA}{trial_status}{Style.RESET_ALL}"

        print(
            f"[{Fore.LIGHTBLACK_EX}{current_time}{Style.RESET_ALL}] "
            f"[{Fore.GREEN}OKAY{Style.RESET_ALL}] "
            f"{Fore.LIGHTBLACK_EX}VALID{Style.RESET_ALL} | "
            f"{Fore.LIGHTBLACK_EX}token:{Style.RESET_ALL} {Fore.CYAN}{masked_token}{Style.RESET_ALL} | "
            f"{Fore.LIGHTBLACK_EX}type:{Style.RESET_ALL} {type_status} | "
            f"{Fore.LIGHTBLACK_EX}age:{Style.RESET_ALL} {Fore.YELLOW}{age_days} Days{Style.RESET_ALL} | "
            f"{Fore.LIGHTBLACK_EX}trial:{Style.RESET_ALL} {trial_display} | "
            f"{Fore.LIGHTBLACK_EX}boosts:{Style.RESET_ALL} {Fore.MAGENTA}{boost_count}{Style.RESET_ALL} | "
            f"{Fore.LIGHTBLACK_EX}nitro:{Style.RESET_ALL} {Fore.MAGENTA}{nitro_type}{Style.RESET_ALL} | "
            f"{Fore.LIGHTBLACK_EX}redeemable:{Style.RESET_ALL} {Fore.GREEN if is_redeemable == 'Redeemable' else Fore.RED}{is_redeemable}{Style.RESET_ALL}"
        )
        
        return "Valid", is_redeemable, type_key, trial_status, original_line

    except Exception as e:
        print(
            f"[{Fore.LIGHTBLACK_EX}{current_time}{Style.RESET_ALL}] "
            f"[{Fore.RED}BAD{Style.RESET_ALL}] "
            f"{Fore.LIGHTBLACK_EX}token:{Style.RESET_ALL} {Fore.CYAN}{masked_token}{Style.RESET_ALL}"
        )
        return "Invalid", None, None, None, None

def main():
    clear_screen()
    print(BANNER)

    file_path = "tokens.txt"

    if not os.path.exists(file_path):
        print(f"{Fore.RED}[!] tokens.txt not found!{Style.RESET_ALL}")
        return

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f if line.strip()]

    total = len(lines)
    print(f"{Fore.YELLOW}[INFO] Loaded {total} tokens. Checking...\n{Style.RESET_ALL}")

    valid_count = 0
    invalid_count = 0
    locked_count = 0
    redeem_count = 0
    not_redeem_count = 0
    trial_1month_count = 0
    trial_2week_count = 0

    nitro_file = "output/nitro.txt"
    email_file = "output/email_verified.txt"
    redeem_file = "output/redeemable.txt"
    trial_1month_file = "output/trial_1month.txt"
    trial_2week_file = "output/trial_2week.txt"

    os.makedirs("output", exist_ok=True)

    for f in [nitro_file, email_file, redeem_file, trial_1month_file, trial_2week_file]:
        open(f, "w").close()

    start_time = time.time()

    for line in lines:
        result = check_token(line)
        status = result[0]
        
        if status == "Valid":
            valid_count += 1
            redeem_status = result[1]
            type_key = result[2]
            trial_status = result[3]
            original_line = result[4]
            
            if "No Nitro" not in line and type_key == "fully":
                with open(nitro_file, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            
            if type_key == "email":
                with open(email_file, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            
            if redeem_status == "Redeemable":
                redeem_count += 1
                with open(redeem_file, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            else:
                not_redeem_count += 1
            
            # Save trial tokens
            if trial_status == "1 Month":
                trial_1month_count += 1
                with open(trial_1month_file, "a", encoding="utf-8") as f:
                    f.write(original_line + "\n")
            elif trial_status == "2 Week":
                trial_2week_count += 1
                with open(trial_2week_file, "a", encoding="utf-8") as f:
                    f.write(original_line + "\n")
                
        elif status == "Locked":
            locked_count += 1
        else:
            invalid_count += 1
        time.sleep(0.1)

    elapsed = round(time.time() - start_time, 2)

    # Final summary only (no panel)
    print(f"\n{Fore.GREEN}[INFO]{Style.RESET_ALL} Checked {total} tokens in {elapsed}s")
    print(f"{Fore.LIGHTBLACK_EX}[INFO]{Style.RESET_ALL} Output files:")
    print(f"  {Fore.GREEN}•{Style.RESET_ALL} nitro - {Fore.LIGHTBLACK_EX}{sum(1 for _ in open(nitro_file))}{Style.RESET_ALL} tokens")
    print(f"  {Fore.GREEN}•{Style.RESET_ALL} email verified - {Fore.LIGHTBLACK_EX}{sum(1 for _ in open(email_file))}{Style.RESET_ALL} tokens")
    print(f"  {Fore.GREEN}•{Style.RESET_ALL} redeemable - {Fore.LIGHTBLACK_EX}{sum(1 for _ in open(redeem_file))}{Style.RESET_ALL} tokens")
    print(f"  {Fore.GREEN}•{Style.RESET_ALL} trial 1month - {Fore.LIGHTBLACK_EX}{trial_1month_count}{Style.RESET_ALL} tokens")
    print(f"  {Fore.GREEN}•{Style.RESET_ALL} trial 2week - {Fore.LIGHTBLACK_EX}{trial_2week_count}{Style.RESET_ALL} tokens")
    input(f"\n{Fore.YELLOW}bas cutie ab band karo aur sojao <3{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
