(() => {
  const scanBtn = document.getElementById("scanBtn");
  const scanLabel = scanBtn.querySelector(".scan-label");
  const results = document.getElementById("results");
  const emptyState = document.getElementById("emptyState");
  const status = document.getElementById("status");
  const errorsEl = document.getElementById("errors");
  const regionEl = document.getElementById("region");
  const companyEl = document.getElementById("company");
  const dateRangeEl = document.getElementById("dateRange");
  const customWrap = document.getElementById("customWrap");
  const dateFrom = document.getElementById("dateFrom");
  const dateTo = document.getElementById("dateTo");
  const includeUnknown = document.getElementById("includeUnknownDate");

  const REGION_LABELS = {
    all: "All",
    india: "India",
    eu: "Europe",
    infopark: "Infopark",
  };

  let jobs = [];

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

  function rebuildFilterCounts() {
    rebuildRegionOptions();
    rebuildCompanyOptions();
  }

  function titlePriority(job) {
    // Higher = show first. Java/Spring first, then backend/fullstack/SWE.
    const t = String(job.title || "").toLowerCase();
    let score = 0;
    if (/\bjava\b/.test(t)) score += 100;
    if (/\bspring\s*boot\b|\bspringboot\b/.test(t)) score += 80;
    else if (/\bspring\b/.test(t)) score += 60;
    if (score >= 160) score += 40; // java + spring
    if (/\bbackend\b|\bback[\s-]?end\b/.test(t)) score += 40;
    if (/\bfull[\s-]?stack\b|\bfullstack\b/.test(t)) score += 35;
    if (/\bsoftware\s+engineer\b/.test(t)) score += 25;
    return score;
  }

  function filtered() {
    const region = regionEl.value;
    const company = companyEl.value;
    return jobs
      .filter((j) => {
        if (region !== "all" && j.region !== region) return false;
        if (company !== "all" && j.company !== company) return false;
        return inDateRange(j);
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

  function render() {
    rebuildFilterCounts();
    const rows = filtered();
    const cards = results.querySelectorAll(".job-card");
    cards.forEach((el) => el.remove());

    if (!jobs.length) {
      emptyState.classList.remove("hidden");
      emptyState.innerHTML =
        `<p>Click <strong>Scan now</strong> to fetch listings that fit your profile.</p>`;
      setStatus("");
      return;
    }

    if (!rows.length) {
      emptyState.classList.remove("hidden");
      const region = regionEl.value;
      if (region === "infopark") {
        emptyState.innerHTML =
          `<p>No Infopark jobs match the other filters (date / company / seniority).</p>`;
      } else {
        emptyState.innerHTML = `<p>No jobs match the current filters.</p>`;
      }
      setStatus(`${jobs.length} scanned · 0 shown`);
      return;
    }

    emptyState.classList.add("hidden");
    const frag = document.createDocumentFragment();
    rows.forEach((j) => {
      const article = document.createElement("article");
      article.className = "job-card";
      const sponsor = j.sponsorship
        ? `<span class="pill sponsor">Sponsorship</span>`
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
          </div>
        </div>
        <div class="job-actions">
          <a class="apply" href="${escapeHtml(j.url)}" target="_blank" rel="noopener noreferrer">Apply</a>
        </div>`;
      frag.appendChild(article);
    });
    results.appendChild(frag);
    setStatus(`${jobs.length} scanned · ${rows.length} shown`);
  }

  async function scan() {
    setScanning(true);
    jobs = [];
    const allErrors = [];
    companyEl.value = "all";
    showErrors([]);
    render();

    try {
      const region = regionEl.value || "all";
      const srcRes = await fetch(`/api/sources?region=${encodeURIComponent(region)}`);
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
          // Merge + dedupe by url
          const seen = new Set(jobs.map((j) => (j.url || "").split("?")[0].toLowerCase()));
          for (const j of batch) {
            const key = (j.url || "").split("?")[0].toLowerCase();
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

      await fetch("/api/jobs/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jobs, errors: allErrors }),
      });
      setStatus(`${jobs.length} scanned · ${filtered().length} shown`);
    } catch (err) {
      showErrors([{ source: "ui", message: String(err) }]);
      setStatus("Scan failed");
    } finally {
      setScanning(false);
    }
  }

  async function loadCached() {
    try {
      const res = await fetch("/api/jobs");
      const data = await res.json();
      jobs = data.jobs || [];
      if (jobs.length) {
        showErrors(data.errors || []);
        render();
        setStatus(`${jobs.length} from last scan · adjust filters or Scan now`);
      }
    } catch (_) {
      /* first run */
    }
  }

  dateRangeEl.addEventListener("change", () => {
    customWrap.classList.toggle("hidden", dateRangeEl.value !== "custom");
    render();
  });
  regionEl.addEventListener("change", () => {
    companyEl.value = "all";
    render();
  });
  companyEl.addEventListener("change", render);
  includeUnknown.addEventListener("change", render);
  dateFrom.addEventListener("change", render);
  dateTo.addEventListener("change", render);
  scanBtn.addEventListener("click", scan);

  loadCached();
})();
