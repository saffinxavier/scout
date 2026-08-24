(() => {
  const authScreen = document.getElementById("authScreen");
  const appShell = document.getElementById("appShell");
  const scanBtn = document.getElementById("scanBtn");
  const scanLabel = scanBtn.querySelector(".scan-label");
  const results = document.getElementById("results");
  const emptyState = document.getElementById("emptyState");
  const status = document.getElementById("status");
  const nextScanEl = document.getElementById("nextScan");
  const errorsEl = document.getElementById("errors");
  const regionEl = document.getElementById("region");
  const companyEl = document.getElementById("company");
  const dateRangeEl = document.getElementById("dateRange");
  const markFilterEl = document.getElementById("markFilter");
  const customWrap = document.getElementById("customWrap");
  const dateFrom = document.getElementById("dateFrom");
  const dateTo = document.getElementById("dateTo");
  const includeUnknown = document.getElementById("includeUnknownDate");
  const qEl = document.getElementById("q");
  const loginForm = document.getElementById("loginForm");
  const loginEmail = document.getElementById("loginEmail");
  const loginPassword = document.getElementById("loginPassword");
  const loginError = document.getElementById("loginError");
  const loginSubmit = document.getElementById("loginSubmit");
  const userEmail = document.getElementById("userEmail");
  const signOutBtn = document.getElementById("signOutBtn");
  const filterToggle = document.getElementById("filterToggle");
  const filterDone = document.getElementById("filterDone");
  const filterClose = document.getElementById("filterClose");
  const filterBackdrop = document.getElementById("filterBackdrop");
  const sourceInfoBtn = document.getElementById("sourceInfoBtn");
  const sourceInfoDot = document.getElementById("sourceInfoDot");
  const sourceDialog = document.getElementById("sourceDialog");
  const sourceDialogClose = document.getElementById("sourceDialogClose");
  const sourceDialogScan = document.getElementById("sourceDialogScan");
  const sourceDialogBody = document.getElementById("sourceDialogBody");

  const REGION_LABELS = {
    all: "All",
    india: "BIG4 & Banks",
    eu: "Europe",
    uae: "UAE",
    infopark: "Infopark",
  };

  const cfg = window.SCOUT || {};
  const minLen = Number(cfg.passwordMinLength) || 8;
  const PREFS_KEY = "scout.filterPrefs";
  const SEEN_KEY = "scout.seenUrls";

  let jobs = [];
  let marks = {};
  let localApi = false;
  let sessionUser = null;
  let jobsLoaded = false;
  let generatedAt = null;
  let sb = null;
  let sourceCatalog = [];
  let lastErrors = [];
  let scanTick = "";

  if (window.supabase && cfg.supabaseUrl && cfg.supabaseAnonKey) {
    sb = window.supabase.createClient(cfg.supabaseUrl, cfg.supabaseAnonKey);
  }

  let seenSnapshot = new Set();
  try {
    const raw = JSON.parse(localStorage.getItem(SEEN_KEY) || "[]");
    if (Array.isArray(raw)) seenSnapshot = new Set(raw.map(String));
  } catch (_) {
    seenSnapshot = new Set();
  }

  function savePrefs() {
    try {
      localStorage.setItem(
        PREFS_KEY,
        JSON.stringify({
          region: regionEl.value,
          dateRange: dateRangeEl.value,
          markFilter: markFilterEl.value,
          includeUnknown: includeUnknown.checked,
          q: qEl.value,
        })
      );
    } catch (_) {}
  }

  function loadPrefs() {
    try {
      const p = JSON.parse(localStorage.getItem(PREFS_KEY) || "null");
      if (!p || typeof p !== "object") return;
      const regions = ["all", "india", "eu", "uae", "infopark"];
      const dates = ["all", "24h", "48h", "7d", "custom"];
      const marks = ["open", "new", "applied", "flagged", "hidden", "all"];
      if (regions.includes(p.region)) regionEl.value = p.region;
      if (dates.includes(p.dateRange)) dateRangeEl.value = p.dateRange;
      if (marks.includes(p.markFilter)) markFilterEl.value = p.markFilter;
      if (typeof p.includeUnknown === "boolean") includeUnknown.checked = p.includeUnknown;
      if (typeof p.q === "string") qEl.value = p.q;
      customWrap.classList.toggle("hidden", dateRangeEl.value !== "custom");
    } catch (_) {}
  }

  function rememberUrls() {
    try {
      const next = new Set(seenSnapshot);
      jobs.forEach((j) => next.add(urlKey(j.url)));
      localStorage.setItem(SEEN_KEY, JSON.stringify([...next]));
    } catch (_) {}
  }

  function isNewJob(j) {
    return !seenSnapshot.has(urlKey(j.url));
  }

  loadPrefs();

  function urlKey(url) {
    return String(url || "").split("?")[0].toLowerCase();
  }

  function jobMark(job) {
    return marks[urlKey(job.url)] || "";
  }

  function setStatus(msg) {
    status.textContent = msg || "";
  }

  function scanButtonLabel() {
    return localApi ? "Scan now" : "Reload list";
  }

  function setScanLabel(text) {
    scanLabel.textContent = text;
    scanBtn.setAttribute("aria-label", text);
  }

  function setScanning(on) {
    scanBtn.disabled = on;
    scanBtn.classList.toggle("loading", on);
    setScanLabel(
      on
        ? localApi
          ? "Scanning…"
          : "Reloading…"
        : scanButtonLabel()
    );
  }

  function formatPublished(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return String(iso);
    const dd = String(d.getDate()).padStart(2, "0");
    const mmm = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][
      d.getMonth()
    ];
    const yyyy = d.getFullYear();
    const min = String(d.getMinutes()).padStart(2, "0");
    let h = d.getHours();
    const ampm = h >= 12 ? "PM" : "AM";
    h = h % 12 || 12;
    return `${dd}/${mmm}/${yyyy}, ${h}:${min} ${ampm}`;
  }

  function nextScheduledScanMs() {
    const now = Date.now();
    const utc = new Date(now);
    const y = utc.getUTCFullYear();
    const mo = utc.getUTCMonth();
    const da = utc.getUTCDate();
    const times = [2, 14].map((hour) => Date.UTC(y, mo, da, hour, 30, 0, 0));
    times.push(Date.UTC(y, mo, da + 1, 2, 30, 0, 0));
    return times.filter((t) => t > now).sort((a, b) => a - b)[0];
  }

  function formatRemain(ms) {
    if (ms <= 0) return "soon";
    const s = Math.floor(ms / 1000);
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    if (h > 0) return `${h}h ${String(m).padStart(2, "0")}m`;
    if (m > 0) return `${m}m ${String(sec).padStart(2, "0")}s`;
    return `${sec}s`;
  }

  function tickNextScan() {
    if (!nextScanEl) return;
    if (localApi) {
      nextScanEl.textContent = "";
      return;
    }
    const next = nextScheduledScanMs();
    nextScanEl.textContent = next
      ? ` · next scan ${formatRemain(next - Date.now())}`
      : "";
  }

  function publishedNote() {
    const t = formatPublished(generatedAt);
    return t ? ` · updated ${t}` : "";
  }

  function isAuthLost(error) {
    if (!error) return false;
    const code = String(error.code || error.status || "");
    const msg = String(error.message || "").toLowerCase();
    return (
      code === "401" ||
      error.status === 401 ||
      code === "PGRST301" ||
      msg.includes("jwt") ||
      msg.includes("not authenticated") ||
      msg.includes("refresh token")
    );
  }

  async function forceReLogin(message) {
    showLoginError(message || "Sign in again.");
    if (sb) await sb.auth.signOut();
  }

  function showErrors(errs) {
    const list = Array.isArray(errs) ? errs : [];
    lastErrors = list.filter((e) => e && e.source && e.source !== "supabase" && e.source !== "ui");
    const other = list.filter((e) => e && (e.source === "supabase" || e.source === "ui"));
    if (!other.length) {
      errorsEl.classList.add("hidden");
      errorsEl.innerHTML = "";
    } else {
      errorsEl.classList.remove("hidden");
      errorsEl.innerHTML = other.map((e) => escapeHtml(e.message || "")).join(" · ");
    }
    sourceInfoDot.classList.toggle("hidden", !lastErrors.length);
    if (sourceDialog.open) fillSourceDialog();
  }

  function applyCatalog(data) {
    if (data && Array.isArray(data.sources) && data.sources.length) {
      sourceCatalog = data.sources;
    }
  }

  function isLocalFlask() {
    const h = location.hostname;
    return h === "localhost" || h === "127.0.0.1";
  }

  async function ensureCatalog() {
    if (sourceCatalog.length) return;
    if (!isLocalFlask()) return;
    try {
      const res = await fetch("/api/sources?catalog=1");
      if (res.ok) {
        applyCatalog(await res.json());
      }
    } catch (_) {}
  }

  function fillSourceDialog() {
    if (!sourceCatalog.length) {
      const ids = [...new Set(jobs.map((j) => j.source).filter(Boolean))];
      sourceCatalog = ids.map((id) => ({
        id,
        label: id,
        region: "",
        enabled: true,
        note: "",
      }));
    }
    const err = {};
    for (const e of lastErrors) err[e.source] = e.message;
    const counts = countBy(jobs, (j) => j.source);
    const on = sourceCatalog.filter((s) => s.enabled);
    const off = sourceCatalog.filter((s) => !s.enabled);
    const rowHtml = (rows, empty) => {
      if (!rows.length) return `<p class="source-empty">${empty}</p>`;
      return `<ul class="source-list">${rows
        .map((s) => {
          const n = counts.get(s.id) || 0;
          const fail = err[s.id];
          const note = fail || s.note || "";
          const active = scanTick && scanTick.startsWith(s.id + " ");
          return `<li class="${active ? "is-scanning" : ""}${fail ? " is-fail" : ""}">
            <span class="source-name">${escapeHtml(s.label || s.id)}</span>
            <span class="source-meta">${escapeHtml(REGION_LABELS[s.region] || s.region || "")} · ${
              s.enabled ? `${n} in list` : "not scanned"
            }</span>
            ${note ? `<span class="source-note">${escapeHtml(note)}</span>` : ""}
          </li>`;
        })
        .join("")}</ul>`;
    };
    sourceDialogBody.innerHTML = `<h3>On</h3>${rowHtml(on, "None enabled.")}<h3>Off</h3>${rowHtml(
      off,
      "None disabled."
    )}${
      localApi
        ? ""
        : `<p class="source-foot">Reload only refreshes this page. A full scan runs on GitHub when you push to main.</p>`
    }`;
    if (scanTick) {
      sourceDialogScan.classList.remove("hidden");
      sourceDialogScan.textContent = `Scanning ${scanTick}`;
    } else {
      sourceDialogScan.classList.add("hidden");
      sourceDialogScan.textContent = "";
    }
  }

  async function openSourceDialog() {
    await ensureCatalog();
    fillSourceDialog();
    if (typeof sourceDialog.showModal === "function") sourceDialog.showModal();
    else sourceDialog.setAttribute("open", "");
    sourceInfoBtn.setAttribute("aria-expanded", "true");
  }

  function closeSourceDialog() {
    if (sourceDialog.open) sourceDialog.close();
    sourceDialog.removeAttribute("open");
    sourceInfoBtn.setAttribute("aria-expanded", "false");
  }

  function escapeHtml(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function safeApplyHref(url) {
    try {
      const u = new URL(String(url || ""));
      if (u.protocol !== "http:" && u.protocol !== "https:") return "";
      return u.href;
    } catch (_) {
      return "";
    }
  }

  function showLoginError(msg) {
    if (!msg) {
      loginError.hidden = true;
      loginError.textContent = "";
      return;
    }
    loginError.hidden = false;
    loginError.textContent = msg;
  }

  function authMessage(err) {
    const t = String((err && err.message) || err || "").toLowerCase();
    if (t.includes("rate") || t.includes("too many")) return "Too many attempts. Wait a moment and try again.";
    if (t.includes("invalid") || t.includes("credential") || t.includes("password")) {
      return "Email or password is wrong.";
    }
    return "Could not sign in. Try again.";
  }

  function openFilters() {
    document.body.classList.add("filters-open");
    filterBackdrop.hidden = false;
    filterBackdrop.classList.remove("hidden");
    filterToggle.setAttribute("aria-expanded", "true");
  }

  function closeFilters() {
    document.body.classList.remove("filters-open");
    filterBackdrop.hidden = true;
    filterBackdrop.classList.add("hidden");
    filterToggle.setAttribute("aria-expanded", "false");
  }

  function startOfDay(d) {
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
  }

  function parseISODate(s) {
    if (!s) return null;
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s);
    if (!m) return null;
    return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  }

  function inDateRange(job) {
    const mode = dateRangeEl.value;
    const posted = parseISODate(job.posted_at);
    if (!posted) return includeUnknown.checked;
    if (mode === "all") return true;
    const today = startOfDay(new Date());
    if (mode === "24h") {
      const from = new Date(today);
      from.setDate(from.getDate() - 1);
      return posted >= from && posted <= today;
    }
    if (mode === "48h") {
      const from = new Date(today);
      from.setDate(from.getDate() - 2);
      return posted >= from && posted <= today;
    }
    if (mode === "7d") {
      const from = new Date(today);
      from.setDate(from.getDate() - 7);
      return posted >= from && posted <= today;
    }
    if (mode === "custom") {
      const from = dateFrom.value ? parseISODate(dateFrom.value) : null;
      const to = dateTo.value ? parseISODate(dateTo.value) : null;
      if (from && posted < from) return false;
      if (to && posted > to) return false;
      return true;
    }
    return true;
  }

  function countBy(list, keyFn) {
    const map = new Map();
    for (const item of list) {
      const k = keyFn(item);
      if (!k) continue;
      map.set(k, (map.get(k) || 0) + 1);
    }
    return map;
  }

  function matchesSearch(job) {
    const q = (qEl.value || "").trim().toLowerCase();
    if (!q) return true;
    const hay = `${job.title || ""} ${job.company || ""}`.toLowerCase();
    return hay.includes(q);
  }

  function matchesMark(job) {
    const mark = markFilterEl.value;
    const st = jobMark(job);
    if (mark === "open") return !st;
    if (mark === "new") return isNewJob(job);
    if (mark === "applied") return st === "applied";
    if (mark === "flagged") return st === "flagged";
    if (mark === "hidden") return st === "hidden";
    return true;
  }

  // opts.region / opts.company override the dropdown so facet counts ignore that facet.
  function matchesFilters(job, opts = {}) {
    const region = opts.region !== undefined ? opts.region : regionEl.value;
    const company = opts.company !== undefined ? opts.company : companyEl.value;
    if (region !== "all" && job.region !== region) return false;
    if (company !== "all" && job.company !== company) return false;
    if (!inDateRange(job)) return false;
    if (!matchesSearch(job)) return false;
    return matchesMark(job);
  }

  function rebuildRegionOptions() {
    const prev = regionEl.value || "all";
    const pool = jobs.filter((j) => matchesFilters(j, { region: "all" }));
    const byRegion = countBy(pool, (j) => j.region);
    const total = pool.length;
    const order = ["all", "india", "eu", "uae", "infopark"];
    regionEl.innerHTML = order
      .map((id) => {
        const n = id === "all" ? total : byRegion.get(id) || 0;
        const label = REGION_LABELS[id] || id;
        return `<option value="${id}">${label} (${n})</option>`;
      })
      .join("");
    regionEl.value = order.includes(prev) ? prev : "all";
  }

  function rebuildCompanyOptions() {
    const prev = companyEl.value || "all";
    const pool = jobs.filter((j) => matchesFilters(j, { company: "all" }));
    const byCompany = countBy(pool, (j) => j.company);
    const names = [...byCompany.keys()].sort((a, b) => a.localeCompare(b));
    if (prev !== "all" && !names.includes(prev)) names.push(prev);
    names.sort((a, b) => a.localeCompare(b));
    companyEl.innerHTML =
      `<option value="all">All companies (${pool.length})</option>` +
      names
        .map(
          (n) =>
            `<option value="${escapeHtml(n)}">${escapeHtml(n)} (${byCompany.get(n) || 0})</option>`
        )
        .join("");
    if (prev === "all" || names.includes(prev)) {
      companyEl.value = prev;
    } else {
      companyEl.value = "all";
    }
  }

  function titlePriority(job) {
    const t = String(job.title || "").toLowerCase();
    let score = 0;
    if (/\bjava\b/.test(t)) score += 100;
    if (/\bspring\s*boot\b|\bspringboot\b/.test(t)) score += 80;
    else if (/\bspring\b/.test(t)) score += 60;
    if (score >= 160) score += 40;
    if (/\bbackend\b|\bback[\s-]?end\b/.test(t)) score += 40;
    if (/\bfull[\s-]?stack\b|\bfullstack\b/.test(t)) score += 35;
    if (/\bsoftware\s+engineer\b/.test(t)) score += 25;
    return score;
  }

  function filtered() {
    return jobs
      .filter((j) => matchesFilters(j))
      .sort((a, b) => {
        const d = titlePriority(b) - titlePriority(a);
        if (d !== 0) return d;
        const dateA = a.posted_at || "";
        const dateB = b.posted_at || "";
        if (dateA !== dateB) return dateB.localeCompare(dateA);
        return String(a.title || "").localeCompare(String(b.title || ""));
      });
  }

  function regionClass(region) {
    if (region === "eu") return "region-eu";
    if (region === "uae") return "region-uae";
    if (region === "infopark") return "region-infopark";
    return "region-india";
  }

  function showGate(on) {
    if (on) {
      authScreen.classList.remove("hidden");
      appShell.classList.add("hidden");
    } else {
      authScreen.classList.add("hidden");
      appShell.classList.remove("hidden");
    }
  }

  function renderAuth() {
    if (sessionUser) {
      showGate(false);
      userEmail.textContent = sessionUser.email || "Signed in";
    } else {
      showGate(true);
      userEmail.textContent = "";
      closeFilters();
    }
  }

  function render() {
    if (!sessionUser) return;
    rebuildRegionOptions();
    rebuildCompanyOptions();
    const rows = filtered();
    const cards = results.querySelectorAll(".job-card");
    cards.forEach((el) => el.remove());

    if (!jobs.length) {
      emptyState.classList.remove("hidden");
      emptyState.innerHTML = localApi
        ? `<p>No listings yet. Click <strong>Scan now</strong> to fetch jobs.</p>`
        : `<p>No listings in the last publish${publishedNote() ? ` (${formatPublished(generatedAt)})` : ""}. Push to <strong>main</strong> or run <strong>Scan and publish</strong> in GitHub Actions.</p>`;
      setStatus(generatedAt ? `0 jobs${publishedNote()}` : "");
      return;
    }

    if (!rows.length) {
      emptyState.classList.remove("hidden");
      const dateHint = dateRangeEl.value !== "all";
      emptyState.innerHTML = `
        <p>No jobs match the current filters (0 shown of ${jobs.length} loaded).</p>
        ${
          dateHint
            ? `<p>The default date range is last 24 hours; many postings have no date.</p>
               <p class="empty-actions">
                 <button type="button" class="btn btn-outline" data-empty="any-time">Any time</button>
                 <button type="button" class="btn btn-outline" data-empty="unknown">Include unknown dates</button>
               </p>`
            : `<p>Try Status = All, clear search, or another region / company.</p>`
        }`;
      setStatus(`${jobs.length} loaded · 0 shown${publishedNote()}`);
      return;
    }

    emptyState.classList.add("hidden");
    const frag = document.createDocumentFragment();
    rows.forEach((j) => {
      const article = document.createElement("article");
      const st = jobMark(j);
      article.className = "job-card" + (st ? ` is-${st}` : "");
      const key = urlKey(j.url);
      const applyHref = safeApplyHref(j.url);
      const sponsor = j.sponsorship
        ? `<span class="pill sponsor">Sponsorship</span>`
        : "";
      const newPill = isNewJob(j) ? `<span class="pill is-new">New</span>` : "";
      const markPill =
        st === "applied"
          ? `<span class="pill applied">Applied</span>`
          : st === "flagged"
            ? `<span class="pill flagged">Flagged</span>`
            : st === "hidden"
              ? `<span class="pill hidden-mark">Hidden</span>`
              : "";
      article.innerHTML = `
        <div>
          <h2 class="job-title">${escapeHtml(j.title)}</h2>
          <div class="job-meta">
            <span>${escapeHtml(j.company || "")}</span>
            <span class="dot">${escapeHtml(j.location || "")}</span>
            <span class="dot">${escapeHtml(j.posted_at || "Date unknown")}</span>
          </div>
          <div class="job-meta pills-row">
            <span class="pill ${regionClass(j.region)}">${escapeHtml(REGION_LABELS[j.region] || j.region)}</span>
            <span class="pill source">${escapeHtml(j.source)}</span>
            ${sponsor}
            ${newPill}
            ${markPill}
          </div>
        </div>
        <div class="job-actions">
          ${
            applyHref
              ? `<a class="apply" href="${escapeHtml(applyHref)}" target="_blank" rel="noopener noreferrer">Apply</a>`
              : `<span class="apply">Apply</span>`
          }
          <div class="action-row">
            <button type="button" class="btn btn-ghost btn-sm" data-mark="applied" data-url="${escapeHtml(key)}">Applied</button>
            <button type="button" class="btn btn-ghost btn-sm" data-mark="flagged" data-url="${escapeHtml(key)}">Flag</button>
            <button type="button" class="btn btn-ghost btn-sm" data-mark="hidden" data-url="${escapeHtml(key)}">Hide</button>
            ${st ? `<button type="button" class="btn btn-ghost btn-sm" data-mark="" data-url="${escapeHtml(key)}">Clear</button>` : ""}
          </div>
        </div>`;
      frag.appendChild(article);
    });
    results.appendChild(frag);
    setStatus(`${jobs.length} loaded · ${rows.length} shown${publishedNote()}`);
  }

  async function loadMarks() {
    marks = {};
    if (!sb || !sessionUser) return;
    const { data, error } = await sb.from("job_status").select("url,state");
    if (error) {
      if (isAuthLost(error)) {
        await forceReLogin("Sign in again.");
        return;
      }
      showErrors([{ source: "supabase", message: error.message }]);
      return;
    }
    for (const row of data || []) {
      marks[urlKey(row.url)] = row.state;
    }
  }

  async function setMark(key, state) {
    if (!sb || !sessionUser) return;
    if (!state) {
      const { error } = await sb.from("job_status").delete().eq("url", key);
      if (error) {
        if (isAuthLost(error)) {
          await forceReLogin("Sign in again.");
          return;
        }
        showErrors([{ source: "supabase", message: error.message }]);
        return;
      }
      delete marks[key];
      render();
      setStatus(`Cleared mark${publishedNote()}`);
    } else {
      const { error } = await sb.from("job_status").upsert(
        {
          url: key,
          state,
          user_id: sessionUser.id,
          updated_at: new Date().toISOString(),
        },
        { onConflict: "user_id,url" }
      );
      if (error) {
        if (isAuthLost(error)) {
          await forceReLogin("Sign in again.");
          return;
        }
        showErrors([{ source: "supabase", message: error.message }]);
        return;
      }
      marks[key] = state;
      render();
      const done =
        state === "applied"
          ? "Marked applied"
          : state === "flagged"
            ? "Flagged for later"
            : "Hidden";
      setStatus(done + publishedNote());
    }
  }

  async function scan() {
    if (!localApi) {
      setScanning(true);
      try {
        await loadJobs(true);
        setStatus(
          `${jobs.length} loaded · ${filtered().length} shown${publishedNote()} · reloaded this page`
        );
      } finally {
        setScanning(false);
      }
      return;
    }
    setScanning(true);
    scanTick = "";
    const scanRegion = regionEl.value || "all";
    if (scanRegion === "all") {
      jobs = [];
    } else {
      jobs = jobs.filter((j) => j.region !== scanRegion);
    }
    const allErrors = [];
    companyEl.value = "all";
    showErrors([]);
    render();

    try {
      const srcRes = await fetch(`/api/sources?region=${encodeURIComponent(scanRegion)}`);
      const srcData = await srcRes.json();
      const sources = srcData.sources || [];
      if (!sources.length) {
        setStatus("No sources for this region");
        return;
      }

      for (let i = 0; i < sources.length; i++) {
        const src = sources[i];
        scanTick = `${src.id} (${i + 1}/${sources.length})`;
        setScanLabel(`${i + 1}/${sources.length}`);
        if (sourceDialog.open) fillSourceDialog();
        try {
          const res = await fetch("/api/scan/one", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ source_id: src.id }),
          });
          const data = await res.json();
          const batch = data.jobs || [];
          const seen = new Set(jobs.map((j) => urlKey(j.url)));
          for (const j of batch) {
            const key = urlKey(j.url);
            if (!key || seen.has(key)) continue;
            seen.add(key);
            jobs.push(j);
          }
          for (const e of data.errors || []) allErrors.push(e);
          showErrors(allErrors);
          render();
        } catch (err) {
          allErrors.push({ source: src.id, message: String(err) });
          showErrors(allErrors);
        }
      }

      const toSave =
        scanRegion === "all" ? jobs : jobs.filter((j) => j.region === scanRegion);
      const saveRes = await fetch("/api/jobs/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          region: scanRegion,
          jobs: toSave,
          errors: allErrors,
        }),
      });
      if (!saveRes.ok) {
        let msg = `Save failed (${saveRes.status})`;
        try {
          const errBody = await saveRes.json();
          if (errBody && errBody.error) msg = String(errBody.error);
        } catch (_) {}
        throw new Error(msg);
      }
      const saved = await saveRes.json();
      if (Array.isArray(saved.jobs)) {
        if (scanRegion === "all") jobs = saved.jobs;
        else jobs = jobs.filter((j) => j.region !== scanRegion).concat(saved.jobs);
      }
      if (Array.isArray(saved.errors) && saved.errors.length) showErrors(saved.errors);
      generatedAt = new Date().toISOString();
      rememberUrls();
      scanTick = "";
      if (sourceDialog.open) fillSourceDialog();
      setStatus(`${jobs.length} scanned · ${filtered().length} shown${publishedNote()}`);
    } catch (err) {
      showErrors([{ source: "ui", message: String(err) }]);
      setStatus("Scan failed");
    } finally {
      scanTick = "";
      if (sourceDialog.open) fillSourceDialog();
      setScanning(false);
    }
  }

  async function loadJobs(force) {
    if (jobsLoaded && !force) {
      render();
      return;
    }
    if (isLocalFlask() && !force) {
      try {
        const res = await fetch("/api/jobs");
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data.jobs)) {
            localApi = true;
            jobs = data.jobs;
            generatedAt = data.generated_at || generatedAt;
            applyCatalog(data);
            jobsLoaded = true;
            setScanLabel(scanButtonLabel());
            if (jobs.length) showErrors(data.errors || []);
            rememberUrls();
            render();
            return;
          }
        }
      } catch (_) {
        /* fall through to jobs.json */
      }
    }
    localApi = false;
    try {
      const res = await fetch(`jobs.json?t=${Date.now()}`, { cache: "no-store" });
      const data = await res.json();
      jobs = data.jobs || [];
      generatedAt = data.generated_at || null;
      applyCatalog(data);
      jobsLoaded = true;
      setScanLabel(scanButtonLabel());
      showErrors(data.errors || []);
      rememberUrls();
      render();
    } catch (_) {
      jobs = [];
      generatedAt = null;
      jobsLoaded = true;
      setScanLabel(scanButtonLabel());
      render();
    }
  }

  async function onAuth(session) {
    sessionUser = session && session.user ? session.user : null;
    renderAuth();
    if (!sessionUser) {
      jobs = [];
      jobsLoaded = false;
      generatedAt = null;
      marks = {};
      return;
    }
    await loadMarks();
    await loadJobs();
  }

  emptyState.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-empty]");
    if (!btn) return;
    const act = btn.getAttribute("data-empty");
    if (act === "any-time") dateRangeEl.value = "all";
    if (act === "unknown") includeUnknown.checked = true;
    customWrap.classList.toggle("hidden", dateRangeEl.value !== "custom");
    savePrefs();
    render();
  });

  results.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-mark]");
    if (!btn) return;
    setMark(btn.getAttribute("data-url"), btn.getAttribute("data-mark") || "");
  });

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    showLoginError("");
    if (!sb) {
      showLoginError("Sign-in is not configured.");
      return;
    }
    const email = loginEmail.value.trim();
    const password = loginPassword.value;
    if (!email || password.length < minLen) {
      showLoginError(`Enter your email and a password of at least ${minLen} characters.`);
      return;
    }
    loginSubmit.disabled = true;
    const { error } = await sb.auth.signInWithPassword({ email, password });
    loginSubmit.disabled = false;
    if (error) showLoginError(authMessage(error));
  });

  signOutBtn.addEventListener("click", async () => {
    if (sb) await sb.auth.signOut();
  });

  filterToggle.addEventListener("click", openFilters);
  filterDone.addEventListener("click", closeFilters);
  if (filterClose) filterClose.addEventListener("click", closeFilters);
  filterBackdrop.addEventListener("click", closeFilters);
  sourceInfoBtn.addEventListener("click", openSourceDialog);
  sourceDialogClose.addEventListener("click", closeSourceDialog);
  sourceDialog.addEventListener("close", () => {
    sourceInfoBtn.setAttribute("aria-expanded", "false");
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (sourceDialog.open) {
      closeSourceDialog();
      return;
    }
    closeFilters();
  });

  dateRangeEl.addEventListener("change", () => {
    customWrap.classList.toggle("hidden", dateRangeEl.value !== "custom");
    savePrefs();
    render();
  });
  regionEl.addEventListener("change", () => {
    companyEl.value = "all";
    savePrefs();
    render();
  });
  companyEl.addEventListener("change", render);
  markFilterEl.addEventListener("change", () => {
    savePrefs();
    render();
  });
  includeUnknown.addEventListener("change", () => {
    savePrefs();
    render();
  });
  qEl.addEventListener("input", () => {
    savePrefs();
    render();
  });
  dateFrom.addEventListener("change", render);
  dateTo.addEventListener("change", render);
  scanBtn.addEventListener("click", scan);
  setInterval(tickNextScan, 1000);
  tickNextScan();

  (async () => {
    if (!sb) {
      showLoginError("Sign-in is not configured.");
      showGate(true);
      return;
    }
    const { data } = await sb.auth.getSession();
    await onAuth(data.session);
    sb.auth.onAuthStateChange((_event, session) => {
      onAuth(session);
    });
  })();
})();
