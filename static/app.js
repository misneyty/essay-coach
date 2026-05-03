(function () {
  "use strict";

  // ── DOM refs ──────────────────────────────────────
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const stateInput = $("#state-input");
  const stateParsing = $("#state-parsing");
  const stateConfirm = $("#state-confirm");
  const stateAnalyzing = $("#state-analyzing");
  const stateAssessment = $("#state-assessment");
  const stateQuestions = $("#state-questions");
  const stateError = $("#state-error");

  const essayInput = $("#essay-input");
  const charCount = $("#char-count");
  const btnSubmit = $("#btn-submit");
  const btnConfirm = $("#btn-confirm");
  const btnReparse = $("#btn-reparse");
  const btnContinue = $("#btn-continue");
  const btnModify = $("#btn-modify");
  const btnModifySubmit = $("#btn-modify-submit");
  const btnModifyCancel = $("#btn-modify-cancel");
  const btnQuestionsYes = $("#btn-questions-yes");
  const btnQuestionsSkip = $("#btn-questions-skip");
  const btnReset = $("#btn-reset");
  const btnErrorReset = $("#btn-error-reset");

  const structureMapContent = $("#structure-map-content");
  const plagiarismWarning = $("#plagiarism-warning");
  const progressFill = $("#progress-fill");
  const progressLabel = $("#progress-label");
  const stageLabel = $("#stage-label");
  const analysisResult = $("#analysis-result");
  const analyzeButtons = $("#analyze-buttons");
  const modifyDialog = $("#modify-dialog");
  const modifyPoint = $("#modify-point");
  const modifyResult = $("#modify-result");
  const assessmentResult = $("#assessment-result");
  const questionsResult = $("#questions-result");
  const errorMessage = $("#error-message");

  // ── State ─────────────────────────────────────────
  let sessionId = null;
  let nextStage = null;
  let stageOrder = [];      // ["abstract","introduction","body_0","body_1","conclusion","references"]
  let stageIndex = -1;      // current position in stageOrder
  let currentStage = null;
  let currentSection = null; // for modify: which section we are on

  const allPanels = [
    stateInput, stateParsing, stateConfirm, stateAnalyzing,
    stateAssessment, stateQuestions, stateError,
  ];

  function showPanel(panel) {
    allPanels.forEach((p) => p.classList.add("hidden"));
    panel.classList.remove("hidden");
  }

  // ── Character counter ────────────────────────────
  essayInput.addEventListener("input", function () {
    const len = this.value.length;
    charCount.textContent = len + " / 8000";
    charCount.classList.toggle("over", len > 8000);
    btnSubmit.disabled = len === 0 || len > 8000;
  });

  // ── Markdown-ish to HTML ─────────────────────────
  function renderMarkdown(text) {
    if (!text) return "";
    let html = text;

    // Escape HTML
    html = html
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Bold **text**
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

    // Bullet lists: lines starting with - or •
    html = html.replace(
      /^([ \t]*)([-•])\s+(.+)$/gm,
      '$1<span class="li-bullet">$2</span> <span class="li-text">$3</span>'
    );

    // Numbered lists
    html = html.replace(
      /^([ \t]*)(\d+)[.)]\s+(.+)$/gm,
      '$1<span class="li-num">$2.</span> <span class="li-text">$3</span>'
    );

    // Error/Correct pairs
    html = html.replace(/❌\s*(.+)/g, '<span class="ref-error">❌ $1</span>');
    html = html.replace(/✅\s*(.+)/g, '<span class="ref-correct">✅ $1</span>');

    // Blank lines to paragraph breaks
    html = html.replace(/\n\n+/g, "</p><p>");
    html = "<p>" + html + "</p>";
    html = html.replace(/<p><\/p>/g, "");

    // Line breaks within paragraphs
    html = html.replace(/\n/g, "<br>");

    return html;
  }

  // ── Reset ─────────────────────────────────────────
  function resetAll() {
    sessionId = null;
    nextStage = null;
    stageOrder = [];
    stageIndex = -1;
    currentStage = null;
    currentSection = null;
    essayInput.value = "";
    charCount.textContent = "0 / 8000";
    btnSubmit.disabled = true;
    analysisResult.innerHTML = "";
    assessmentResult.innerHTML = "";
    questionsResult.innerHTML = "";
    modifyResult.innerHTML = "";
    modifyResult.classList.add("hidden");
    modifyDialog.classList.add("hidden");
    plagiarismWarning.classList.add("hidden");
    modifyPoint.value = "";
    progressFill.style.width = "0%";
    progressLabel.textContent = "";
    stageLabel.textContent = "";
    analyzeButtons.classList.remove("hidden");
    showPanel(stateInput);
  }

  // ── API helpers ───────────────────────────────────
  async function apiPost(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "请求失败");
    return data;
  }

  async function apiGet(url) {
    const res = await fetch(url);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "请求失败");
    return data;
  }

  // ── Submit essay ──────────────────────────────────
  btnSubmit.addEventListener("click", async function () {
    const essay = essayInput.value.trim();
    if (!essay) return;

    showPanel(stateParsing);
    try {
      const data = await apiPost("/api/session", { essay });
      sessionId = data.session_id;

      structureMapContent.innerHTML = renderMarkdown(data.structure_map);

      if (data.plagiarism_flag) {
        plagiarismWarning.textContent =
          "⚠️ " + data.plagiarism_flag;
        plagiarismWarning.classList.remove("hidden");
      }

      // Build stage order
      stageOrder = ["abstract", "introduction"];
      for (let i = 0; i < data.sections.body_count; i++) {
        stageOrder.push("body_" + i);
      }
      stageOrder.push("conclusion", "references");

      showPanel(stateConfirm);
    } catch (err) {
      showError(err.message);
    }
  });

  // ── Confirm structure ────────────────────────────
  btnConfirm.addEventListener("click", async function () {
    try {
      await apiPost("/api/session/" + sessionId + "/confirm", { confirm: true });
      stageIndex = 0;
      currentSection = stageOrder[0];
      nextStage = stageOrder[0];
      updateProgress();
      runNextStage();
    } catch (err) {
      showError(err.message);
    }
  });

  btnReparse.addEventListener("click", function () {
    resetAll();
  });

  // ── Run next analysis stage ──────────────────────
  async function runNextStage() {
    showPanel(stateAnalyzing);
    modifyDialog.classList.add("hidden");
    modifyResult.innerHTML = "";
    modifyResult.classList.add("hidden");
    analyzeButtons.classList.remove("hidden");

    if (!nextStage || nextStage === "assessment" || nextStage === "done") {
      return runAssessment();
    }

    currentStage = nextStage;
    currentSection = nextStage;

    const labels = {
      abstract: "摘要分析 Abstract Analysis",
      introduction: "引言分析 Introduction Analysis",
      conclusion: "结论分析 Conclusion Analysis",
      references: "参考文献审查 Reference Audit",
    };

    if (nextStage.startsWith("body_")) {
      const idx = parseInt(nextStage.split("_")[1]) + 1;
      stageLabel.textContent = "主体段落分析 Body Paragraph " + idx;
    } else {
      stageLabel.textContent = labels[nextStage] || nextStage;
    }

    analysisResult.innerHTML =
      '<div class="spinner"></div><p style="text-align:center">分析中...</p>';

    try {
      const data = await apiPost(
        "/api/session/" + sessionId + "/analyze/" + nextStage,
        {}
      );
      analysisResult.innerHTML = renderMarkdown(data.result);
      nextStage = data.next;
      stageIndex++;
      updateProgress();

      if (nextStage === "assessment") {
        // Switch buttons for assessment phase
        analyzeButtons.classList.add("hidden");
        const btnAssess = document.createElement("button");
        btnAssess.className = "btn btn-primary";
        btnAssess.textContent = "查看综合评估 ▶";
        btnAssess.addEventListener("click", runAssessment);
        analyzeButtons.innerHTML = "";
        analyzeButtons.appendChild(btnAssess);
      }
    } catch (err) {
      showError(err.message);
    }
  }

  btnContinue.addEventListener("click", runNextStage);

  // ── Progress bar ──────────────────────────────────
  function updateProgress() {
    const total = stageOrder.length + 1; // +1 for assessment
    const done = stageIndex;
    const pct = total > 0 ? Math.round((done / total) * 100) : 0;
    progressFill.style.width = pct + "%";
    progressLabel.textContent = done + " / " + total + " stages";
  }

  // ── Modify / drill-down ──────────────────────────
  btnModify.addEventListener("click", function () {
    modifyDialog.classList.remove("hidden");
    modifyResult.innerHTML = "";
    modifyResult.classList.add("hidden");
    modifyPoint.value = "";
    modifyPoint.focus();
  });

  btnModifyCancel.addEventListener("click", function () {
    modifyDialog.classList.add("hidden");
  });

  btnModifySubmit.addEventListener("click", async function () {
    const point = modifyPoint.value.trim();
    if (!point) return;

    modifyResult.innerHTML =
      '<div class="spinner"></div><p style="text-align:center">深入分析中...</p>';
    modifyResult.classList.remove("hidden");
    analyzeButtons.classList.add("hidden");

    try {
      const data = await apiPost(
        "/api/session/" + sessionId + "/modify",
        { section: currentSection, point: point }
      );
      modifyResult.innerHTML = renderMarkdown(data.result);
      analyzeButtons.classList.remove("hidden");
    } catch (err) {
      modifyResult.innerHTML =
        '<p style="color:#c0392b">错误：' + err.message + "</p>";
      analyzeButtons.classList.remove("hidden");
    }
  });

  // Modify: Enter key submits
  modifyPoint.addEventListener("keydown", function (e) {
    if (e.key === "Enter") btnModifySubmit.click();
  });

  // ── Assessment ────────────────────────────────────
  async function runAssessment() {
    showPanel(stateAnalyzing);
    analyzeButtons.classList.add("hidden");
    modifyDialog.classList.add("hidden");
    stageLabel.textContent = "综合评估 Comprehensive Assessment";
    analysisResult.innerHTML =
      '<div class="spinner"></div><p style="text-align:center">生成综合评估...</p>';

    try {
      const data = await apiPost(
        "/api/session/" + sessionId + "/assess",
        {}
      );
      assessmentResult.innerHTML = renderMarkdown(data.result);
      showPanel(stateAssessment);
    } catch (err) {
      showError(err.message);
    }
  }

  // ── Questions ─────────────────────────────────────
  btnQuestionsYes.addEventListener("click", async function () {
    showPanel(stateParsing);
    try {
      const data = await apiPost(
        "/api/session/" + sessionId + "/questions",
        { include_questions: true }
      );
      questionsResult.innerHTML = renderMarkdown(data.result || "暂无思考题。");
      showPanel(stateQuestions);
    } catch (err) {
      showError(err.message);
    }
  });

  btnQuestionsSkip.addEventListener("click", async function () {
    try {
      await apiPost("/api/session/" + sessionId + "/questions", {
        include_questions: false,
      });
      questionsResult.innerHTML = "<p>分析完成！感谢使用写作教练。</p>";
      showPanel(stateQuestions);
    } catch (err) {
      showError(err.message);
    }
  });

  // ── New essay ─────────────────────────────────────
  btnReset.addEventListener("click", resetAll);
  btnErrorReset.addEventListener("click", resetAll);

  // ── Error handling ───────────────────────────────
  function showError(msg) {
    errorMessage.textContent = msg;
    showPanel(stateError);
  }

  // ── Init ──────────────────────────────────────────
  showPanel(stateInput);
})();
