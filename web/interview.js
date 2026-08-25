(() => {
  const navBtns = Array.from(document.querySelectorAll("[data-view]"));
  const interviewScreen = document.getElementById("interviewScreen");
  const interviewBody = document.getElementById("interviewBody");
  const chips = Array.from(document.querySelectorAll(".stack-chip"));

  if (!navBtns.length || !interviewScreen || !interviewBody || !chips.length) return;

  const PREFS_KEY = "scout.interviewPrefs";
  const DEFAULT_TOGGLES = { java: true, springboot: true, angular: false };

  const INTERVIEW = {
    common: [
      {
        id: "q1",
        question: "How are you doing today?",
        answer:
          "Good morning, Ria. I am doing well, thank you. I am glad to be here and looking forward to the conversation.",
      },
      {
        id: "q2",
        question: "Are you interested in this opportunity?",
        answer:
          "Yes, absolutely. I am very interested in this opportunity. The role aligns well with my experience and career goals, and I am looking forward to learning more about the position, team, and projects.",
      },
      {
        id: "q3",
        question: "Does the resume information look accurate?",
        answer:
          "- Option 1: Yes, that is accurate overall. My relevant experience is approximately 3.5 years, and my total professional experience is also approximately 3.5 years. The rest of the information looks correct.\n- Option 2: Yes, all my data is correct.",
      },
      {
        id: "q4",
        question: "Are you open to relocating?",
        answer: "Yes, I am open to relocating based on role requirements.",
      },
      {
        id: "q5",
        question: "What is your earliest joining date? Is your notice period negotiable?",
        answer:
          "I currently have a 90-day notice period, and I have not resigned yet. However, the notice period is negotiable, and I am open to discussing an earlier joining date depending on the role requirements and offer timeline.",
      },
      {
        id: "q6",
        question: "Are you holding any offers?",
        answer: "No, I am not currently holding any offers from other organizations.",
      },
      {
        id: "q7",
        question: "What is your current CTC and fixed/variable split?",
        answer:
          "My current CTC is approximately 10 LPA, and it is fully fixed with no variable pay component.",
      },
      {
        id: "q8",
        question: "What is your salary increment cycle?",
        answer:
          "My current company follows an annual salary increment cycle, generally once every year.",
      },
      {
        id: "q9",
        question: "What month does the increment usually occur?",
        answer: "The usual increment month is April. My last increment was effective from 1 April 2026.",
      },
      {
        id: "q10",
        question: "What are your CTC expectations?",
        answer:
          "I am looking for a standard increment over my current CTC, but I am flexible based on role responsibilities, growth opportunity, and overall compensation structure.",
      },
      {
        id: "q11",
        question: "Are you willing to travel domestically/internationally?",
        answer:
          "Yes, I am comfortable with travel as required for the role, including both domestic and international travel based on project and client needs.",
      },
      {
        id: "q12",
        question: "Are you comfortable with the hybrid work model?",
        answer:
          "Yes, I am comfortable with the hybrid model and willing to work from Deloitte office or client location whenever required.",
      },
      {
        id: "q16",
        question: "Closing response",
        answer:
          "Thank you, Ria, for the opportunity and for taking the time to speak with me. I appreciate the information and look forward to hearing from the team regarding next steps. Have a great day.",
      },
    ],
    roleFit: {
      q13: {
        question: "What attracted you to this role?",
        core:
          "This role attracted me because it aligns with my Java backend foundation and gives me an opportunity to contribute to large-scale enterprise systems while growing into broader responsibilities.",
        backend:
          "This role attracted me because it strongly aligns with my hands-on work in Java and Spring Boot backend development, especially building REST APIs and microservices for real-world business workflows.",
        fullstack:
          "This role attracted me because it combines backend ownership in Java with full-stack collaboration. I am interested in contributing across API and UI layers, especially where Angular and backend integration are critical.",
      },
      q14: {
        question: "What skills and experience make you a strong fit?",
        core:
          "I have around 3.5 years of Java-centric backend experience, including API design, service development, SQL data handling, and secure application practices. I focus on clean code, debugging, and dependable delivery in team environments.",
        backend:
          "I have around 3.5 years of experience in Java Spring Boot backend development, working with microservices, REST APIs, Spring Data JPA, Hibernate, and PostgreSQL. I also bring experience with Spring Security, OAuth2, JWT, and Keycloak for secure backend services.",
        fullstack:
          "I have around 3.5 years of backend experience in Java and Spring Boot, plus practical Angular experience for building and integrating UI flows with APIs. This helps me understand both service design and frontend consumption while keeping security and performance in mind.",
      },
      q15: {
        question: "Is there anything you would like to know about Deloitte?",
        core:
          "Yes. I would like to understand the kind of Java projects the team is currently handling, the expected ownership for this level, and how technical growth is supported in the first year.",
        backend:
          "Yes. I would like to know more about the backend architecture and service landscape, such as microservice patterns, deployment model, and the expectations around API quality and ownership for this role.",
        fullstack:
          "Yes. I would like to understand how responsibilities are split across Angular and backend work, the team structure for full-stack delivery, and the opportunities to grow in both frontend and backend areas.",
      },
    },
  };

  let toggles = { ...DEFAULT_TOGGLES };

  function escapeHtml(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function flavorFromToggles(javaOn, springOn, angularOn) {
    if (angularOn) return "fullstack";
    if (springOn) return "backend";
    return javaOn ? "core" : "core";
  }

  function savePrefs() {
    try {
      localStorage.setItem(PREFS_KEY, JSON.stringify(toggles));
    } catch (_) {}
  }

  function loadPrefs() {
    try {
      const raw = JSON.parse(localStorage.getItem(PREFS_KEY) || "null");
      if (!raw || typeof raw !== "object") return;
      const java = typeof raw.java === "boolean" ? raw.java : DEFAULT_TOGGLES.java;
      const springboot = typeof raw.springboot === "boolean" ? raw.springboot : DEFAULT_TOGGLES.springboot;
      const angular = typeof raw.angular === "boolean" ? raw.angular : DEFAULT_TOGGLES.angular;
      toggles = { java, springboot, angular };
    } catch (_) {
      toggles = { ...DEFAULT_TOGGLES };
    }
  }

  function setChipState() {
    chips.forEach((chip) => {
      const key = chip.getAttribute("data-stack");
      const on = key && toggles[key];
      chip.classList.toggle("is-on", Boolean(on));
      chip.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  function allQuestions() {
    const flavor = flavorFromToggles(toggles.java, toggles.springboot, toggles.angular);
    return [
      ...INTERVIEW.common.slice(0, 12),
      {
        id: "q13",
        question: INTERVIEW.roleFit.q13.question,
        answer: INTERVIEW.roleFit.q13[flavor],
      },
      {
        id: "q14",
        question: INTERVIEW.roleFit.q14.question,
        answer: INTERVIEW.roleFit.q14[flavor],
      },
      {
        id: "q15",
        question: INTERVIEW.roleFit.q15.question,
        answer: INTERVIEW.roleFit.q15[flavor],
      },
      INTERVIEW.common[12],
    ];
  }

  function renderInterview() {
    const rows = allQuestions();
    interviewBody.innerHTML = rows
      .map((row, idx) => {
        const q3OptionRows =
          row.id === "q3"
            ? row.answer
                .split("\n")
                .map((line) => line.trim())
                .filter(Boolean)
                .map((line, optionIdx) => {
                  const clean = line
                    .replace(/^-+\s*/, "")
                    .replace(/^Option\s+\d+\s*:\s*/i, "");
                  return `
              <div class="interview-option-row">
                <p>${escapeHtml(line)}</p>
                <button
                  type="button"
                  class="btn btn-ghost btn-sm copy-answer-btn"
                  data-copy-option="${optionIdx}"
                  title="Copy this option"
                  aria-label="Copy this option"
                >⧉</button>
                <span class="hidden" data-option-text="${optionIdx}">${escapeHtml(clean)}</span>
              </div>
            `;
                })
                .join("")
            : "";

        return `
          <article class="interview-card" data-question="${escapeHtml(row.id)}">
            <header class="interview-card-head">
              <h3>${idx + 1}. ${escapeHtml(row.question)}</h3>
              ${
                row.id === "q3"
                  ? ""
                  : `<button
                type="button"
                class="btn btn-ghost btn-sm copy-answer-btn"
                data-copy="${escapeHtml(row.id)}"
                title="Copy answer"
                aria-label="Copy answer"
              >⧉</button>`
              }
            </header>
            ${
              row.id === "q3"
                ? `<div class="interview-options">${q3OptionRows}</div>`
                : `<p>${escapeHtml(row.answer)}</p>`
            }
          </article>
        `;
      })
      .join("");
  }

  function setView(mode) {
    const interviewOn = mode === "interview";
    document.body.classList.toggle("view-interview", interviewOn);
    navBtns.forEach((btn) => {
      const active = btn.dataset.view === mode;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-pressed", active ? "true" : "false");
    });
    if (interviewOn) renderInterview();
  }

  function runSelfTest() {
    const params = new URLSearchParams(location.search);
    if (params.get("selftest") !== "1") return;
    try {
      console.assert(flavorFromToggles(true, true, false) === "backend", "Expected backend for Java+Spring");
      console.assert(flavorFromToggles(true, false, false) === "core", "Expected core for Java-only");
      console.assert(flavorFromToggles(true, false, true) === "fullstack", "Expected fullstack when Angular enabled");
      console.info("interview selftest passed");
    } catch (err) {
      console.error("interview selftest failed", err);
    }
  }

  navBtns.forEach((btn) => {
    btn.addEventListener("click", () => setView(btn.dataset.view));
  });

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const key = chip.getAttribute("data-stack");
      if (!key) return;
      toggles[key] = !toggles[key];
      setChipState();
      savePrefs();
      renderInterview();
    });
  });

  interviewScreen.addEventListener("click", async (event) => {
    const btn = event.target.closest("button[data-copy]");
    const optionBtn = event.target.closest("button[data-copy-option]");
    if (!btn && !optionBtn) return;

    let text = "";
    if (btn) {
      const id = btn.getAttribute("data-copy");
      const row = allQuestions().find((q) => q.id === id);
      if (!row) return;
      text = row.answer;
    } else {
      const optionIdx = optionBtn.getAttribute("data-copy-option");
      const wrap = optionBtn.closest(".interview-option-row");
      if (!wrap) return;
      const hidden = wrap.querySelector(`[data-option-text="${optionIdx}"]`);
      if (!hidden) return;
      text = hidden.textContent || "";
      if (!text) return;
    }

    const activeBtn = btn || optionBtn;
    try {
      await navigator.clipboard.writeText(text);
      activeBtn.textContent = "✓";
      window.setTimeout(() => {
        activeBtn.textContent = "⧉";
      }, 900);
    } catch (_) {
      activeBtn.textContent = "!";
      window.setTimeout(() => {
        activeBtn.textContent = "⧉";
      }, 1200);
    }
  });

  loadPrefs();
  setChipState();
  setView("jobs");
  runSelfTest();
})();
