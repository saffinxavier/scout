(() => {
  const authScreen = document.getElementById("authScreen");
  const appShell = document.getElementById("appShell");
  const scanBtn = document.getElementById("scanBtn");
  const scanLabel = scanBtn.querySelector(".scan-label");
  const results = document.getElementById("results");
  const emptyState = document.getElementById("emptyState");
  const status = document.getElementById("status");
  const errorsEl = document.getElementById("errors");
  const regionEl = document.getElementById("region");
  const companyEl = document.getElementById("company");
  const dateRangeEl = document.getElementById("dateRange");
  const markFilterEl = document.getElementById("markFilter");
  const customWrap = document.getElementById("customWrap");
  const dateFrom = document.getElementById("dateFrom");
  const dateTo = document.getElementById("dateTo");
  const includeUnknown = document.getElementById("includeUnknownDate");
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

  const REGION_LABELS = {
    all: "All",
    india: "India",
    eu: "Europe",
    infopark: "Infopark",
  };

  const cfg = window.SCOUT || {};
  const minLen = Number(cfg.passwordMinLength) || 8;

  let jobs = [];
  let marks = {};
  let localApi = false;
  let sessionUser = null;
  let jobsLoaded = false;
  let sb = null;

  if (window.supabase && cfg.supabaseUrl && cfg.supabaseAnonKey) {
    sb = window.supabase.createClient(cfg.supabaseUrl, cfg.supabaseAnonKey);
  }

  function urlKey(url) {
    return String(url || "").split("?")[0].toLowerCase();
  }

  function jobMark(job) {
    return marks[urlKey(job.url)] || "";
  }

  function setStatus(msg) {
    status.textContent = msg || "";
  }

  function setScanning(on) {
    scanBtn.disabled = on;
    scanBtn.classList.toggle("loading", on);
    scanLabel.textContent = on ? "Scanning…" : "Scan now";
  }

  function showErrors(errs) {
    if (!errs || !errs.length) {
      errorsEl.classList.add("hidden");
      errorsEl.innerHTML = "";
      return;
    }
    errorsEl.classList.remove("hidden");
    const items = errs
      .map((e) => `<li><strong>${escapeHtml(e.source)}</strong>: ${escapeHtml(e.message)}</li>`)
      .join("");
    errorsEl.innerHTML = `<div>${errs.length} source(s) failed</div><ul>${items}</ul>`;
  }

  function escapeHtml(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
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

  function rebuildRegionOptions() {
    const prev = regionEl.value || "all";
    const dated = jobs.filter(inDateRange);
    const byRegion = countBy(dated, (j) => j.region);
    const total = dated.length;
    const order = ["all", "india", "eu", "infopark"];
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
    const region = regionEl.value;
    const pool = jobs.filter((j) => {
      if (region !== "all" && j.region !== region) return false;
      return inDateRange(j);
    });
    const byCompany = countBy(pool, (j) => j.company);
    const names = [...byCompany.keys()].sort((a, b) => a.localeCompare(b));
    companyEl.innerHTML =
      `<option value="all">All companies (${pool.length})</option>` +
      names
        .map(
          (n) =>
            `<option value="${escapeHtml(n)}">${escapeHtml(n)} (${byCompany.get(n)})</option>`
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
    const region = regionEl.value;
    const company = companyEl.value;
    const mark = markFilterEl.value;
    return jobs
      .filter((j) => {
        if (region !== "all" && j.region !== region) return false;
        if (company !== "all" && j.company !== company) return false;
        if (!inDateRange(j)) return false;
        const st = jobMark(j);
        if (mark === "open") return !st;
        if (mark === "applied") return st === "applied";
        if (mark === "hidden") return st === "hidden";
        return true;
      })
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
        ? `<p>Click <strong>Scan now</strong> to fetch listings that fit your profile.</p>`
        : `<p>No listings yet. On GitHub: <strong>Actions</strong> → <strong>Scan and publish</strong> → Run workflow.</p>`;
      setStatus("");
      return;
    }

    if (!rows.length) {
      emptyState.classList.remove("hidden");
      emptyState.innerHTML = `<p>No jobs match the current filters.</p>`;
      setStatus(`${jobs.length} loaded · 0 shown`);
      return;
    }

    emptyState.classList.add("hidden");
    const frag = document.createDocumentFragment();
    rows.forEach((j) => {
      const article = document.createElement("article");
      const st = jobMark(j);
      article.className = "job-card" + (st ? ` is-${st}` : "");
      const key = urlKey(j.url);
      const sponsor = j.sponsorship
        ? `<span class="pill sponsor">Sponsorship</span>`
        : "";
      const markPill =
        st === "applied"
          ? `<span class="pill applied">Applied</span>`
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
            <span class="pill ${regionClass(j.region)}">${escapeHtml(j.region)}</span>
            <span class="pill source">${escapeHtml(j.source)}</span>
            ${sponsor}
            ${markPill}
          </div>
        </div>
        <div class="job-actions">
          <a class="apply" href="${escapeHtml(j.url)}" target="_blank" rel="noopener noreferrer">Apply</a>
          <div class="action-row">
            <button type="button" class="btn btn-ghost btn-sm" data-mark="applied" data-url="${escapeHtml(key)}">Applied</button>
            <button type="button" class="btn btn-ghost btn-sm" data-mark="hidden" data-url="${escapeHtml(key)}">Hide</button>
            ${st ? `<button type="button" class="btn btn-ghost btn-sm" data-mark="" data-url="${escapeHtml(key)}">Clear</button>` : ""}
          </div>
        </div>`;
      frag.appendChild(article);
    });
    results.appendChild(frag);
    setStatus(`${jobs.length} loaded · ${rows.length} shown`);
  }

  async function loadMarks() {
    marks = {};
    if (!sb || !sessionUser) return;
    const { data, error } = await sb.from("job_status").select("url,state");
    if (error) {
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
        showErrors([{ source: "supabase", message: error.message }]);
        return;
      }
      delete marks[key];
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
        showErrors([{ source: "supabase", message: error.message }]);
        return;
      }
      marks[key] = state;
    }
    render();
  }

  async function scan() {
    if (!localApi) {
      setScanning(true);
      try {
        jobsLoaded = false;
        await loadJobs();
        setStatus(
          `${jobs.length} from last GitHub publish · a full scan runs when you push to main (or Actions → Run workflow)`
        );
      } finally {
        setScanning(false);
      }
      return;
    }
    setScanning(true);
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
        setStatus(`Scanning ${src.id} (${i + 1}/${sources.length})…`);
        scanLabel.textContent = `${i + 1}/${sources.length}`;
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
      await fetch("/api/jobs/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          region: scanRegion,
          jobs: toSave,
          errors: allErrors,
        }),
      });
      setStatus(`${jobs.length} scanned · ${filtered().length} shown`);
    } catch (err) {
      showErrors([{ source: "ui", message: String(err) }]);
      setStatus("Scan failed");
    } finally {
      setScanning(false);
    }
  }

  async function loadJobs() {
    if (jobsLoaded) {
      render();
      return;
    }
    try {
      const res = await fetch("/api/jobs");
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data.jobs)) {
          localApi = true;
          jobs = data.jobs;
          jobsLoaded = true;
          if (jobs.length) showErrors(data.errors || []);
          render();
          return;
        }
      }
    } catch (_) {
      /* hosted */
    }
    localApi = false;
    try {
      const res = await fetch("jobs.json");
      const data = await res.json();
      jobs = data.jobs || [];
      jobsLoaded = true;
      showErrors(data.errors || []);
      render();
    } catch (_) {
      jobs = [];
      jobsLoaded = true;
      render();
    }
  }

  async function onAuth(session) {
    sessionUser = session && session.user ? session.user : null;
    renderAuth();
    if (!sessionUser) {
      jobs = [];
      jobsLoaded = false;
      marks = {};
      return;
    }
    await loadMarks();
    await loadJobs();
  }

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
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeFilters();
  });

  dateRangeEl.addEventListener("change", () => {
    customWrap.classList.toggle("hidden", dateRangeEl.value !== "custom");
    render();
  });
  regionEl.addEventListener("change", () => {
    companyEl.value = "all";
    render();
  });
  companyEl.addEventListener("change", render);
  markFilterEl.addEventListener("change", render);
  includeUnknown.addEventListener("change", render);
  dateFrom.addEventListener("change", render);
  dateTo.addEventListener("change", render);
  scanBtn.addEventListener("click", scan);

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
