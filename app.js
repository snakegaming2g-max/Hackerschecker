const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const MAX_TOKENS_PER_RUN = 500;

const CATEGORY_LABELS = {
  nitro_2x: "Nitro 2X",
  nitro_1x: "Nitro 1X",
  nitro: "Nitro",
  trial_1m_fv: "1M Trial FV",
  trial_1m_ev: "1M Trial EV",
  trial_2w_fv: "2W Trial FV",
  trial_2w_ev: "2W Trial EV",
  fv: "FV",
  ev: "EV",
  locked: "Locked",
  invalid: "Invalid",
  redeemable: "Redeemable",
  other: "Other",
};

const STAT_DEFS = [
  { key: "total", label: "Total", icon: "box", tone: "gold", filter: "all" },
  { key: "processed", label: "Processed", icon: "check", tone: "green", filter: "all" },
  { key: "nitro_2x", label: "Nitro 2X", icon: "star", tone: "gold" },
  { key: "nitro_1x", label: "Nitro 1X", icon: "diamond", tone: "blue" },
  { key: "nitro", label: "Nitro", icon: "crown", tone: "gold" },
  { key: "trial_1m_fv", label: "1M Trial FV", icon: "gift", tone: "pink" },
  { key: "trial_1m_ev", label: "1M Trial EV", icon: "gift", tone: "cyan" },
  { key: "trial_2w_fv", label: "2W Trial FV", icon: "gift", tone: "blue" },
  { key: "trial_2w_ev", label: "2W Trial EV", icon: "gift", tone: "purple" },
  { key: "fv", label: "FV", icon: "bolt", tone: "gold" },
  { key: "ev", label: "EV", icon: "bolt", tone: "green" },
  { key: "locked", label: "Locked", icon: "lock", tone: "red" },
  { key: "invalid", label: "Invalid", icon: "alert", tone: "red" },
  { key: "redeemable", label: "Redeemable", icon: "check", tone: "green" },
];

const ICONS = {
  box:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 8 12 3 3 8v8l9 5 9-5V8Z"></path><path d="M3 8l9 5 9-5"></path><path d="M12 13v8"></path><path d="M3 8l9-5 9 5"></path></svg>',
  check:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="m8.5 12.2 2.4 2.4 4.6-4.8"></path></svg>',
  star:
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="m12 3.4 2.6 5.3 5.9.8-4.3 4.2 1 5.9-5.2-2.8-5.2 2.8 1-5.9L3.5 9.5l5.9-.8L12 3.4Z"></path></svg>',
  diamond:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3h12l4 6-10 12L2 9l4-6Z"></path><path d="M2 9h20"></path><path d="M9 3l3 6 3-6"></path><path d="M12 9l-4 12"></path><path d="M12 9l4 12"></path></svg>',
  crown:
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M3 6.5 7.2 11 12 5l4.8 6L21 6.5V19H3V6.5Z"></path></svg>',
  gift:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="8" width="18" height="12" rx="1.6"></rect><path d="M12 8v12"></path><path d="M3 12h18"></path><path d="M12 8c-1.6 0-4-.5-4-2.5S9.4 3 10.4 3 12 5 12 8Z"></path><path d="M12 8c1.6 0 4-.5 4-2.5S14.6 3 13.6 3 12 5 12 8Z"></path></svg>',
  bolt:
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M13 2 4.5 13.5H11l-1 8.5 9.5-12H13l0-8Z"></path></svg>',
  lock:
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a5 5 0 0 0-5 5v3H5.8A1.8 1.8 0 0 0 4 11.8v8.4A1.8 1.8 0 0 0 5.8 22h12.4a1.8 1.8 0 0 0 1.8-1.8v-8.4A1.8 1.8 0 0 0 18.2 10H17V7a5 5 0 0 0-5-5Zm0 2a3 3 0 0 1 3 3v3H9V7a3 3 0 0 1 3-3Z"></path></svg>',
  alert:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4 2.5 20h19L12 4Z"></path><path d="M12 9.5v5"></path><path d="M12 17.4h.01"></path></svg>',
  eye:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6Z"></path><circle cx="12" cy="12" r="2.6"></circle></svg>',
  list:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 6h13M8 12h13M8 18h13"></path><path d="M3 6h.01M3 12h.01M3 18h.01"></path></svg>',
  terminal:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 17l6-5-6-5"></path><path d="M12 19h8"></path></svg>',
};

const state = {
  threads: 15,
  proxyMode: true,
  autoScroll: true,
  running: false,
  stopping: false,
  lines: [],
  results: [],
  stats: {},
  resultFilter: "all",
  controllers: new Set(),
  startTime: 0,
  renderQueued: false,
};

const elements = {
  tokensArea: $("#tokens"),
  tokenCount: $("#token-count"),
  tokenFile: $("#token-file"),
  uploadTokens: $("#upload-tokens"),
  clearTokens: $("#clear-tokens"),
  proxiesArea: $("#proxies"),
  proxyCount: $("#proxy-count"),
  proxyFile: $("#proxy-file"),
  uploadProxies: $("#upload-proxies"),
  proxyToggle: $("#proxy-toggle"),
  threads: $("#threads"),
  start: $("#start"),
  stop: $("#stop"),
  reset: $("#reset"),
  progressFill: $("#progress-fill"),
  progressTrack: $("#progress-track"),
  progressPercent: $("#progress-percent"),
  statsGrid: $("#stats-grid"),
  resultsBody: $("#results-body"),
  resultsEmpty: $("#results-empty"),
  resultFilter: $("#result-filter"),
  exportResults: $("#export-results"),
  consoleBox: $("#console"),
  consoleLines: $("#console-lines"),
  autoscroll: $("#autoscroll"),
  modal: $("#modal"),
  modalTitle: $("#modal-title"),
  modalBody: $("#modal-body"),
  modalClose: $("#modal-close"),
  login: $("#login"),
  toast: $("#toast"),
};

function zeroStats() {
  const stats = { total: 0, processed: 0 };
  for (const def of STAT_DEFS) {
    if (def.key !== "total" && def.key !== "processed") stats[def.key] = 0;
  }
  return stats;
}

function parseLines(raw) {
  if (typeof raw !== "string") return [];
  return raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function plural(count, word) {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}

function nowTime() {
  const date = new Date();
  const pad = (value) => String(value).padStart(2, "0");
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

function appendConsole(message, kind = "info") {
  const line = document.createElement("div");
  line.className = `console-line ${kind}`;

  const time = document.createElement("span");
  time.className = "console-time";
  time.textContent = `[${nowTime()}]`;

  const star = document.createElement("span");
  star.className = "console-star";
  star.textContent = "*";

  const text = document.createElement("span");
  text.className = "console-text";
  text.textContent = message;

  line.append(time, star, text);
  elements.consoleLines.appendChild(line);

  while (elements.consoleLines.childElementCount > 220) {
    elements.consoleLines.firstElementChild.remove();
  }

  if (state.autoScroll) {
    elements.consoleBox.scrollTop = elements.consoleBox.scrollHeight;
  }
}

function resetConsole() {
  elements.consoleLines.replaceChildren();
  appendConsole("Welcome to Hackers Checker!", "accent");
  appendConsole("Load your tokens and press Start to begin...", "accent");
  appendConsole("Stay safe and enjoy!", "accent");
}

let toastTimer = 0;

function showToast(message, kind = "info") {
  elements.toast.textContent = message;
  elements.toast.classList.toggle("error", kind === "error");
  elements.toast.hidden = false;
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => {
    elements.toast.hidden = true;
  }, 2800);
}

function maskLocal(line) {
  const token = line.split(":").pop().trim();
  if (token.length > 20) return token.slice(0, 15) + "..." + token.slice(-5);
  return "INVALID_FORMAT";
}

function errorResult(line, message, { locked = false } = {}) {
  return {
    ok: false,
    status: locked ? "Locked" : "Invalid",
    locked,
    token_masked: maskLocal(line),
    category: locked ? "locked" : "invalid",
    error: message,
  };
}

function classifyResult(profile, billing) {
  const verification = profile?.verification_key;
  const trial = billing?.trial_status;
  const boosts = Number(billing?.boost_count ?? 0);
  if (billing?.has_subscription) {
    if (boosts >= 2) return "nitro_2x";
    if (boosts === 1) return "nitro_1x";
    return "nitro";
  }
  if (trial === "1 Month") {
    return verification === "fully" ? "trial_1m_fv" : "trial_1m_ev";
  }
  if (trial === "2 Week") {
    return verification === "fully" ? "trial_2w_fv" : "trial_2w_ev";
  }
  if (verification === "fully") return "fv";
  if (verification === "email") return "ev";
  return "other";
}

function computeStats() {
  const stats = zeroStats();
  stats.total = state.lines.length;
  let processed = 0;

  for (const result of state.results) {
    if (!result) continue;
    processed += 1;

    if (result.locked) {
      stats.locked += 1;
    } else if (!result.ok) {
      stats.invalid += 1;
    } else {
      const billing = result.billing || {};
      const profile = result.profile || {};
      const category =
        result.category || classifyResult(profile, billing);
      if (category in stats) stats[category] += 1;
      if (billing.redeemable) stats.redeemable += 1;
    }
  }

  stats.processed = processed;
  state.stats = stats;
  renderStats();
}

function renderStats() {
  const grid = elements.statsGrid;
  grid.replaceChildren();

  for (const def of STAT_DEFS) {
    if (def.key !== "total" && !(def.key in state.stats)) state.stats[def.key] = 0;

    const card = document.createElement("button");
    card.type = "button";
    card.className = `stat-card stat stat-clickable tone-${def.tone}`;
    card.dataset.filter = def.filter || def.key;
    if (state.resultFilter === card.dataset.filter) card.classList.add("stat-filtered");

    const icon = document.createElement("span");
    icon.className = "stat-icon";
    icon.innerHTML = ICONS[def.icon] || "";

    const body = document.createElement("span");
    body.className = "stat-body";

    const label = document.createElement("span");
    label.className = "stat-label";
    label.textContent = def.label;

    const value = document.createElement("span");
    value.className = "stat-value";
    value.textContent = String(state.stats[def.key] ?? 0);

    body.append(label, value);
    card.append(icon, body);
    grid.appendChild(card);
  }
}

function highlightActiveStat() {
  for (const card of $$(".stat-card")) {
    card.classList.toggle("stat-filtered", card.dataset.filter === state.resultFilter);
  }
}

function updateProgress() {
  const total = state.lines.length;
  const checked = state.results.filter(Boolean).length;
  const percent = total ? (checked / total) * 100 : 0;
  elements.progressFill.style.width = `${percent.toFixed(2)}%`;
  elements.progressPercent.textContent = `${percent.toFixed(2)}%`;
  elements.progressTrack.setAttribute("aria-valuenow", String(Math.round(percent)));
  return { total, checked };
}

function updateCounters() {
  elements.tokenCount.textContent = plural(parseLines(elements.tokensArea.value).length, "item");
  const proxies = parseLines(elements.proxiesArea.value);
  elements.proxyCount.textContent = plural(proxies.length, "proxy");
}

function clearResults(keepTokens = true) {
  for (const controller of state.controllers) controller.abort();
  state.controllers.clear();
  state.running = false;
  state.stopping = false;
  state.lines = keepTokens ? parseLines(elements.tokensArea.value) : [];
  state.results = new Array(state.lines.length).fill(null);
  state.resultFilter = "all";
  if (elements.resultFilter) elements.resultFilter.value = "all";
  state.stats = zeroStats();
  highlightActiveStat();
  renderStats();
  renderResults();
  updateProgress();
  updateCounters();
}

function formatAge(days) {
  if (typeof days !== "number" || !Number.isFinite(days) || days < 0) return "—";
  const years = Math.floor(days / 365);
  const remainder = days % 365;
  if (years > 0) return `${years}y ${remainder}d`;
  return `${days} ${days === 1 ? "day" : "days"}`;
}

function matchesFilter(result, filter) {
  if (filter === "all") return true;
  if (!result) return false;
  if (filter === "redeemable") {
    return Boolean(result.ok && result.billing && result.billing.redeemable);
  }
  return result.category === filter;
}

function accountName(profile) {
  if (!profile) return "—";
  return profile.global_name || profile.username || "Unknown";
}

function renderResults() {
  const filter = state.resultFilter;
  const body = elements.resultsBody;
  body.replaceChildren();

  const fragment = document.createDocumentFragment();
  let visible = 0;

  state.results.forEach((result, index) => {
    if (!result || !matchesFilter(result, filter)) return;
    visible += 1;
    fragment.appendChild(buildResultRow(result, index));
  });

  body.appendChild(fragment);

  if (visible > 0) {
    elements.resultsEmpty.hidden = true;
    elements.resultsEmpty.textContent = "No results yet. Paste tokens and press Start.";
  } else {
    elements.resultsEmpty.hidden = false;
    elements.resultsEmpty.textContent = filter === "all"
      ? "No results yet. Paste tokens and press Start."
      : `No results match “${CATEGORY_LABELS[filter] || filter}”.`;
  }
}

function buildResultRow(result, index) {
  const row = document.createElement("tr");
  row.className = `result-row ${result.locked ? "result-locked" : result.ok ? "result-valid" : "result-invalid"}`;

  const cellIndex = document.createElement("td");
  cellIndex.className = "cell-mute result-chain";
  cellIndex.textContent = String(index + 1);

  const cellToken = document.createElement("td");
  const tokenSpan = document.createElement("span");
  tokenSpan.className = "result-token";
  tokenSpan.textContent = result.token_masked || "—";
  cellToken.appendChild(tokenSpan);

  const cellAccount = document.createElement("td");
  const validProfile = result.ok ? result.profile || null : null;
  const avatarWrap = document.createElement("span");
  avatarWrap.className = "result-avatar";

  if (validProfile && typeof validProfile.avatar_url === "string" && validProfile.avatar_url.startsWith("https://cdn.discordapp.com/")) {
    const avatar = document.createElement("img");
    avatar.src = validProfile.avatar_url;
    avatar.alt = "";
    avatar.loading = "lazy";
    avatar.referrerPolicy = "no-referrer";
    avatar.addEventListener("error", () => {
      avatarWrap.textContent = accountName(validProfile).trim().charAt(0).toUpperCase() || "?";
    });
    avatarWrap.appendChild(avatar);
  } else {
    avatarWrap.textContent = accountName(validProfile).trim().charAt(0).toUpperCase() || "?";
  }

  const accountBody = document.createElement("span");
  accountBody.className = "result-username";
  const accountNameSpan = document.createElement("span");
  accountNameSpan.className = "result-name";
  accountNameSpan.textContent = accountName(validProfile);
  accountBody.append(avatarWrap, accountNameSpan);

  const cellCategory = document.createElement("td");
  const categoryBadge = document.createElement("span");
  categoryBadge.className = `badge cat-${result.category || "other"}`;
  categoryBadge.textContent = CATEGORY_LABELS[result.category] || result.category || "—";
  cellCategory.appendChild(categoryBadge);

  const cellNitro = document.createElement("td");
  cellNitro.className = "cell-mute";
  if (result.ok) {
    const billing = result.billing || {};
    cellNitro.textContent = billing.nitro_type || "No Nitro";
    cellNitro.title = (billing.subscriptions || [])
      .map((item) => item.label)
      .filter(Boolean)
      .join(" · ") || billing.nitro_type || "";
  } else {
    cellNitro.textContent = "—";
  }

  const cellTrial = document.createElement("td");
  cellTrial.className = "cell-mute";
  cellTrial.textContent = result.ok ? result.billing?.trial_status || "No Trial" : "—";

  const cellBoosts = document.createElement("td");
  cellBoosts.className = result.ok ? "cell-mute" : "cell-dash";
  cellBoosts.textContent = result.ok ? String(result.billing?.boost_count ?? 0) : "—";

  const cellRedeemable = document.createElement("td");
  if (result.ok) {
    const redeemable = Boolean(result.billing?.redeemable);
    const badge = document.createElement("span");
    badge.className = `badge ${redeemable ? "valid" : "invalid"}`;
    badge.textContent = redeemable ? "Yes" : "No";
    cellRedeemable.appendChild(badge);
  } else {
    cellRedeemable.className = "cell-dash";
    cellRedeemable.textContent = "—";
  }

  const cellAge = document.createElement("td");
  cellAge.className = result.ok ? "cell-mute" : "cell-dash";
  cellAge.textContent = result.ok ? formatAge(result.profile?.age_days) : "—";

  const cellDetails = document.createElement("td");
  cellDetails.className = "cell-actions";
  const detailsBtn = document.createElement("button");
  detailsBtn.type = "button";
  detailsBtn.className = "details-btn";
  detailsBtn.title = "Open full details";
  detailsBtn.setAttribute("aria-label", "Open full details");
  detailsBtn.innerHTML = ICONS.eye || "";
  detailsBtn.addEventListener("click", () => openDetails(result, state.lines[index] || ""));
  cellDetails.appendChild(detailsBtn);

  row.append(
    cellIndex,
    cellToken,
    cellAccount,
    cellCategory,
    cellNitro,
    cellTrial,
    cellBoosts,
    cellRedeemable,
    cellAge,
    cellDetails,
  );
  return row;
}

function fieldRow(label, value) {
  const dt = document.createElement("dt");
  dt.textContent = label;
  const dd = document.createElement("dd");
  if (value instanceof Node) dd.appendChild(value);
  else dd.textContent = value ?? "—";
  return [dt, dd];
}

function copyButton(label, text) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "copy-btn";
  button.textContent = label;
  button.dataset.copy = text;
  button.addEventListener("click", async () => {
    const ok = await copyText(String(button.dataset.copy || ""));
    if (ok) {
      button.classList.add("copied");
      button.textContent = "Copied";
      window.setTimeout(() => {
        button.classList.remove("copied");
        button.textContent = label;
      }, 1500);
    } else {
      showToast("Copy failed. Select the text manually.", "error");
    }
  });
  return button;
}

async function copyText(text) {
  if (!text) return false;
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    try {
      const area = document.createElement("textarea");
      area.value = text;
      area.setAttribute("readonly", "true");
      area.style.position = "fixed";
      area.style.left = "-9999px";
      document.body.appendChild(area);
      area.select();
      const ok = document.execCommand("copy");
      area.remove();
      return ok;
    } catch {
      return false;
    }
  }
}

function tokenFromLine(line) {
  if (typeof line !== "string") return "";
  const parts = line.split(":");
  return parts[parts.length - 1].trim();
}

function openDetails(result, line) {
  const body = document.createElement("div");
  body.className = "detail-body";

  if (!result) {
    const note = document.createElement("p");
    note.textContent = "This token has not been checked yet.";
    body.appendChild(note);
    openModal("Token details", body);
    return;
  }

  const badge = document.createElement("span");
  badge.className = `badge cat-${result.category || "other"}`;
  badge.textContent = CATEGORY_LABELS[result.category] || result.category || "—";

  const status = document.createElement("span");
  status.className = `badge ${result.locked ? "locked" : result.ok ? "valid" : "invalid"}`;
  status.textContent = result.locked ? "Locked" : result.ok ? "Valid" : "Invalid";

  const chipRow = document.createElement("div");
  chipRow.className = "chip-row";
  chipRow.append(badge, status);
  body.appendChild(chipRow);

  const details = document.createElement("dl");

  const profile = result.profile || null;
  const billing = result.billing || null;

  if (result.ok && profile) {
    const name = document.createElement("span");
    name.textContent = `${accountName(profile)}${profile.bot ? " (bot)" : ""}`;
    details.append(...fieldRow("Account", name));

    const username = document.createElement("code");
    username.textContent = profile.discriminator && profile.discriminator !== "0"
      ? `@${profile.username}#${profile.discriminator}`
      : `@${profile.username}`;
    details.append(...fieldRow("Username", username));

    const userId = document.createElement("code");
    userId.textContent = profile.id || "—";
    details.append(...fieldRow("User ID", userId));

    details.append(...fieldRow("Verification", profile.verification_label || "—"));
    details.append(
      ...fieldRow("Email", profile.email ? (profile.email_verified ? "Verified" : "Not verified") : "Not available"),
    );
    details.append(
      ...fieldRow("Phone", profile.phone_verified ? "Verified" : "Not linked"),
    );
    details.append(...fieldRow("MFA", profile.mfa_enabled ? "Enabled" : "Disabled"));
    details.append(
      ...fieldRow("Account age", `${formatAge(profile.age_days)}${profile.created_at ? ` (${new Date(profile.created_at).toLocaleDateString()})` : ""}`),
    );
  } else {
    const receipt = document.createElement("code");
    receipt.textContent = result.token_masked || "—";
    details.append(...fieldRow(result.locked ? "Locked token" : "Invalid token", receipt));
  }

  if (result.ok && billing) {
    details.append(...fieldRow("Nitro", billing.nitro_type || "No Nitro"));
    details.append(
      ...fieldRow("Subscription", billing.has_subscription ? `${(billing.subscriptions || []).length} active` : "None"),
    );
    details.append(...fieldRow("Trial", billing.trial_status || "No Trial"));
    details.append(...fieldRow("Boosts", String(billing.boost_count ?? 0)));
    details.append(...fieldRow("Payment sources", String(billing.payment_sources ?? 0)));
    details.append(...fieldRow("Redeemable", billing.redeemable_label || "—"));
  }

  if (result.ok && result.guilds) {
    details.append(...fieldRow("Guilds", `${result.guilds.count} (${result.guilds.owned} owned · ${result.guilds.admin} admin)`));
  }

  if (result.ok && result.connections) {
    details.append(...fieldRow("Connections", String(result.connections.count)));
  }

  if (Array.isArray(result.notes) && result.notes.length) {
    const list = document.createElement("ul");
    for (const note of result.notes) {
      const item = document.createElement("li");
      item.textContent = String(note);
      list.appendChild(item);
    }
    details.append(...fieldRow("Notes", list));
  }

  if (!result.ok && result.error) {
    const error = document.createElement("code");
    error.textContent = result.error;
    details.append(...fieldRow("Error", error));
  }

  body.appendChild(details);

  if (line) {
    const actions = document.createElement("div");
    actions.className = "detail-actions";
    actions.appendChild(copyButton("Copy token", tokenFromLine(line)));
    if (profile && profile.id) {
      actions.appendChild(copyButton("Copy user ID", String(profile.id)));
    }
    body.appendChild(actions);
  }

  openModal("Token details", body);
}

let lastFocused = null;

function openModal(title, node) {
  lastFocused = document.activeElement;
  elements.modalTitle.textContent = title;
  elements.modalBody.replaceChildren(node);
  elements.modal.hidden = false;
  elements.modalClose.focus();
}

function closeModal() {
  elements.modal.hidden = true;
  elements.modalBody.replaceChildren();
  if (lastFocused instanceof HTMLElement) lastFocused.focus();
  lastFocused = null;
}

function readTextFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error || new Error("Could not read the file."));
    reader.readAsText(file);
  });
}

function downloadText(filename, text) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1200);
}

async function checkToken(line, proxy) {
  const controller = new AbortController();
  state.controllers.add(controller);

  try {
    const body = { token: line };
    if (proxy) body.proxy = proxy;

    const response = await fetch("/api/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
      signal: controller.signal,
    });

    let data = null;
    try {
      data = await response.json();
    } catch {
      data = null;
    }

    if (data && typeof data === "object") {
      if (!data.ok) {
        return {
          ok: false,
          status: data.locked ? "Locked" : "Invalid",
          locked: Boolean(data.locked),
          token_masked: data.token_masked || maskLocal(line),
          category: data.category || (data.locked ? "locked" : "invalid"),
          error: data.error || `Local server error (HTTP ${response.status}).`,
        };
      }
      return data;
    }
    return errorResult(line, `Local server returned HTTP ${response.status}.`);
  } catch (error) {
    if (error && error.name === "AbortError") throw error;
    const message = error && error.message ? error.message : "Network error";
    return errorResult(line, message);
  } finally {
    state.controllers.delete(controller);
  }
}

function logResult(result) {
  const label = result.token_masked || "token";
  if (result.ok) {
    const profile = result.profile || {};
    const billing = result.billing || {};
    const name = accountName(profile);
    const category = CATEGORY_LABELS[result.category] || result.category || "—";
    appendConsole(
      `${label} valid · @${name} · ${category}`,
      "ok",
    );
  } else if (result.locked) {
    appendConsole(`${label} locked`, "error");
  } else {
    appendConsole(`${label} invalid${result.error ? ` — ${result.error}` : ""}`, "error");
  }
}

function scheduleResultsRender() {
  if (state.renderQueued) return;
  state.renderQueued = true;
  window.setTimeout(() => {
    state.renderQueued = false;
    renderResults();
  }, 160);
}

function buildBuckets() {
  const buckets = {
    nitro: [],
    email_verified: [],
    redeemable: [],
    trial_1month: [],
    trial_2week: [],
  };

  state.results.forEach((result, index) => {
    const line = state.lines[index];
    if (!result || !line) return;
    if (!result.ok) return;

    const billing = result.billing || {};
    const profile = result.profile || {};
    const category = result.category || classifyResult(profile, billing);
    const verification = profile.verification_key;

    if (category.startsWith("nitro")) buckets.nitro.push(line);
    if (verification === "fully" || verification === "email") {
      buckets.email_verified.push(line);
    }
    if (billing.redeemable) buckets.redeemable.push(line);
    if (billing.trial_status === "1 Month") buckets.trial_1month.push(line);
    if (billing.trial_status === "2 Week") buckets.trial_2week.push(line);
  });

  return buckets;
}

async function saveOutputs() {
  const buckets = buildBuckets();
  const hasAny = Object.values(buckets).some((group) => group.length > 0);
  if (!hasAny) return;

  try {
    const response = await fetch("/api/save-output", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ buckets }),
    });
    const data = await response.json().catch(() => null);

    if (response.ok && data && data.ok) {
      const counts = Object.entries(data.counts || {})
        .filter(([, count]) => Number(count) > 0)
        .map(([key, count]) => `${key} ${count}`);
      appendConsole(
        counts.length
          ? `Saved categorized results to output/ (${counts.join(", ")}).`
          : "Saved empty categories to output/.",
        "ok",
      );
    } else {
      appendConsole(`Could not save output files: ${data?.error || `HTTP ${response.status}`}`, "error");
    }
  } catch (error) {
    appendConsole(`Could not save output files: ${error.message || "network error"}`, "error");
  }
}

async function startRun() {
  if (state.running) return;

  const lines = parseLines(elements.tokensArea.value);
  if (!lines.length) {
    showToast("Paste at least one token first.", "error");
    elements.tokensArea.focus();
    return;
  }
  if (lines.length > MAX_TOKENS_PER_RUN) {
    showToast(`Maximum ${MAX_TOKENS_PER_RUN} tokens per run.`, "error");
    return;
  }

  const sameTokens =
    state.lines.length === lines.length &&
    state.lines.every((line, index) => line === lines[index]);
  if (!sameTokens) {
    state.lines = lines;
    state.results = new Array(lines.length).fill(null);
    state.resultFilter = "all";
    elements.resultFilter.value = "all";
  } else {
    if (state.results.length !== lines.length) {
      state.results = new Array(lines.length).fill(null);
    }
    if (state.results.every(Boolean)) {
      state.results = new Array(lines.length).fill(null);
      appendConsole("Rechecking all tokens from scratch.", "info");
    }
  }

  state.stats = zeroStats();
  renderStats();
  renderResults();
  updateProgress();

  const proxies = parseLines(elements.proxiesArea.value);
  const usable = proxies.filter((proxy) => /^https?:\/\//i.test(proxy));
  const useProxy = state.proxyMode && usable.length > 0;

  if (state.proxyMode && proxies.length > usable.length) {
    appendConsole(
      usable.length ? "Skipping non-http proxies; using the valid ones." : "Skipping non-http proxies; checking direct.",
      "warn",
    );
  } else if (state.proxyMode && !proxies.length) {
    appendConsole("Proxy mode is on but no proxies were added; checking direct.", "warn");
  }

  const threadCount = Math.max(1, Math.min(state.threads, state.lines.length));
  state.running = true;
  state.stopping = false;
  state.startTime = Date.now();
  updateRunButtons();

  appendConsole(
    `Starting ${plural(threadCount, "thread")} for ${plural(state.lines.length, "token")}${useProxy ? " via proxy" : " (direct)"}.`,
    "accent",
  );

  const total = state.lines.length;
  let cursor = 0;
  const stateProxies = usable;

  const worker = async () => {
    while (true) {
      if (state.stopping) return;
      const index = cursor++;
      if (index >= total) return;
      if (state.results[index]) continue;

      let result;
      try {
        result = await checkToken(
          state.lines[index],
          useProxy ? stateProxies[index % stateProxies.length] : null,
        );
      } catch (error) {
        if (error && error.name === "AbortError") return;
        result = errorResult(state.lines[index], error?.message || "Network error");
      }

      if (state.stopping) return;
      state.results[index] = result;
      computeStats();
      scheduleResultsRender();
      logResult(result);
      updateProgress();
    }
  };

  try {
    await Promise.all(Array.from({ length: threadCount }, () => worker()));
  } finally {
    state.running = false;
    state.stopping = false;
    updateRunButtons();

    const { total: totalCount, checked } = { total: state.lines.length, checked: state.results.filter(Boolean).length };
    const elapsed = ((Date.now() - state.startTime) / 1000).toFixed(1);
    if (checked >= totalCount) {
      appendConsole(`Checked ${checked}/${totalCount} tokens in ${elapsed}s.`, "ok");
    } else {
      appendConsole(`Stopped after indexing ${checked}/${totalCount} tokens in ${elapsed}s.`, "warn");
    }
    await saveOutputs();
  }
}

function stopRun() {
  if (!state.running || state.stopping) return;
  state.stopping = true;
  for (const controller of state.controllers) controller.abort();
  state.controllers.clear();
  updateRunButtons();
  appendConsole("Stop requested — finishing in-flight checks.", "warn");
}

async function resetAll() {
  if (state.running) {
    stopRun();
  }
  clearResults(true);
  appendConsole("Checker reset. Ready for a new run.", "warn");
}

async function clearTokens() {
  elements.tokensArea.value = "";
  clearResults(true);
  elements.tokenCount.textContent = "0 items";
  appendConsole("Token list cleared.", "warn");
  elements.tokensArea.focus();
}

function updateRunButtons() {
  elements.start.disabled = state.running;
  elements.stop.disabled = !state.running || state.stopping;
  elements.reset.disabled = false;
}

function updateProxyMode() {
  elements.proxyToggle.classList.toggle("on", state.proxyMode);
  elements.proxyToggle.setAttribute("aria-checked", String(state.proxyMode));
}

function toggleProxyMode() {
  state.proxyMode = !state.proxyMode;
  updateProxyMode();
  appendConsole(
    state.proxyMode ? "Proxy mode enabled." : "Proxy mode disabled.",
    "accent",
  );
}

function openAboutModal() {
  const body = document.createElement("div");

  const intro = document.createElement("p");
  intro.innerHTML = "<strong>Hackers Checker v2.0.0</strong> runs locally and checks tokens against Discord. Nothing is stored.";

  const defs = document.createElement("p");
  defs.innerHTML = "<strong>FV</strong> = Fully verified (email + phone). <strong>EV</strong> = Email verified.";

  const privacy = document.createElement("p");
  privacy.innerHTML = "Tokens stay in memory for one check, are sent only to discord.com, and are never logged. After a run, categorized token lists are written to the local <code>output/</code> folder.";

  const disclaimer = document.createElement("p");
  disclaimer.innerHTML = "Use this tool only with accounts you own. Not affiliated with Discord.";

  const link = document.createElement("p");
  link.className = "link-row";
  const anchor = document.createElement("a");
  anchor.href = "https://discord.gg/hackers";
  anchor.target = "_blank";
  anchor.rel = "noopener noreferrer";
  anchor.textContent = "discord.gg/hackers";
  link.appendChild(anchor);

  body.append(intro, defs, privacy, disclaimer, link);
  openModal("About", body);
}

function openJoinerModal() {
  const body = document.createElement("div");
  const note = document.createElement("p");
  note.innerHTML = "<strong>Joiner</strong> is not part of this local build. This app only checks tokens locally.";
  body.appendChild(note);
  openModal("Joiner", body);
}

function openLoginModal() {
  const body = document.createElement("div");
  const note = document.createElement("p");
  note.innerHTML = "<strong>Local build:</strong> this checker does not need a Discord login. Paste your tokens and press <strong>Start</strong>.";
  const note2 = document.createElement("p");
  note2.innerHTML = "If you want the hosted version, contact <a href=\"https://discord.gg/hackers\" target=\"_blank\" rel=\"noopener noreferrer\">discord.gg/hackers</a>.";
  body.append(note, note2);
  openModal("Login with Discord", body);
}

function openResultExport() {
  const filter = state.resultFilter;
  const lines = [];
  for (let index = 0; index < state.results.length; index += 1) {
    const result = state.results[index];
    const line = state.lines[index];
    if (!line) continue;

    if (filter === "all") {
      if (result) lines.push(line);
      continue;
    }
    if (!result || !result.ok) continue;
    if (filter === "redeemable") {
      if (result.billing?.redeemable) lines.push(line);
      continue;
    }
    if (result.category === filter) lines.push(line);
  }

  if (!lines.length) {
    showToast("Nothing of this category has been checked yet.", "error");
    return;
  }

  const safeFilter = filter === "all" ? "all" : filter;
  const filename = `hackers-checker_${safeFilter}.txt`;
  downloadText(filename, `${lines.join("\n")}\n`);
  appendConsole(`Exported ${plural(lines.length, "token")} to ${filename}.`, "ok");
}

function bindNav() {
  $$(".nav-item").forEach((item) => {
    item.addEventListener("click", () => {
      $$(".nav-item").forEach((other) => other.classList.remove("active"));
      item.classList.add("active");

      if (item.dataset.nav === "dashboard") {
        document.getElementById("top").scrollIntoView({ behavior: "smooth", block: "start" });
      } else if (item.dataset.nav === "checker") {
        elements.tokensArea.focus({ preventScroll: true });
        document.getElementById("checker").scrollIntoView({ behavior: "smooth", block: "center" });
      } else if (item.dataset.nav === "settings") {
        document.getElementById("settings").scrollIntoView({ behavior: "smooth", block: "center" });
      } else if (item.dataset.nav === "joiner") {
        openJoinerModal();
      } else if (item.dataset.nav === "about") {
        openAboutModal();
      }
    });
  });
}

function bindModal() {
  elements.modalClose.addEventListener("click", closeModal);
  $(".modal-backdrop").addEventListener("click", closeModal);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !elements.modal.hidden) closeModal();
  });
}

function bindControls() {
  elements.tokensArea.addEventListener("input", () => {
    updateCounters();
    if (state.results.some(Boolean)) clearResults(true);
  });

  elements.proxiesArea.addEventListener("input", updateCounters);

  elements.clearTokens.addEventListener("click", clearTokens);

  elements.uploadTokens.addEventListener("click", () => elements.tokenFile.click());
  elements.tokenFile.addEventListener("change", async () => {
    const file = elements.tokenFile.files?.[0];
    if (!file) return;
    try {
      const text = await readTextFile(file);
      elements.tokensArea.value = text;
      updateCounters();
      if (state.results.some(Boolean)) clearResults(true);
      appendConsole(`Loaded ${plural(parseLines(text).length, "item")} from ${file.name}.`, "ok");
    } catch (error) {
      showToast(error.message || "Could not read that file.", "error");
    } finally {
      elements.tokenFile.value = "";
    }
  });

  elements.uploadProxies.addEventListener("click", () => elements.proxyFile.click());
  elements.proxyFile.addEventListener("change", async () => {
    const file = elements.proxyFile.files?.[0];
    if (!file) return;
    try {
      const text = await readTextFile(file);
      elements.proxiesArea.value = text;
      updateCounters();
      if (state.proxyMode) appendConsole(`Loaded ${plural(parseLines(text).length, "proxy")} from ${file.name}.`, "ok");
      else appendConsole(`Loaded ${plural(parseLines(text).length, "proxy")} (proxy mode is off).`, "warn");
    } catch (error) {
      showToast(error.message || "Could not read that file.", "error");
    } finally {
      elements.proxyFile.value = "";
    }
  });

  elements.threads.addEventListener("change", () => {
    state.threads = Number(elements.threads.value) || 15;
    appendConsole(`Threads set to MAX ${state.threads}.`, "accent");
  });

  elements.proxyToggle.addEventListener("click", toggleProxyMode);

  elements.start.addEventListener("click", startRun);
  elements.stop.addEventListener("click", stopRun);
  elements.reset.addEventListener("click", resetAll);

  elements.resultFilter.addEventListener("change", () => {
    state.resultFilter = elements.resultFilter.value;
    highlightActiveStat();
    renderResults();
  });

  elements.statsGrid.addEventListener("click", (event) => {
    const card = event.target.closest(".stat-card");
    if (!card) return;
    const filter = card.dataset.filter || "all";
    state.resultFilter = filter;
    elements.resultFilter.value = filter;
    highlightActiveStat();
    renderResults();
  });

  elements.exportResults.addEventListener("click", openResultExport);

  elements.autoscroll.addEventListener("click", () => {
    state.autoScroll = !state.autoScroll;
    elements.autoscroll.classList.toggle("on", state.autoScroll);
    elements.autoscroll.setAttribute("aria-checked", String(state.autoScroll));
    const nested = elements.autoscroll.querySelector(".switch");
    if (nested) nested.classList.toggle("on", state.autoScroll);
    if (state.autoScroll) elements.consoleBox.scrollTop = elements.consoleBox.scrollHeight;
  });

  elements.login.addEventListener("click", openLoginModal);
}

function init() {
  state.lines = [];
  state.results = [];
  state.stats = zeroStats();
  state.proxyMode = true;
  state.resultFilter = "all";
  resetConsole();
  renderStats();
  renderResults();
  updateProgress();
  updateCounters();
  updateProxyMode();
  updateRunButtons();
  bindNav();
  bindModal();
  bindControls();
}

init();
