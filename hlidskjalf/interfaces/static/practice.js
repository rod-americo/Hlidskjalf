let currentQuestion = null;
let corrected = false;
let saved = false;
let pendingAnswers = null;

const statusEl = document.querySelector("#status");
const formEl = document.querySelector("#practice-form");
const metaEl = document.querySelector("#question-meta");
const supportTextEl = document.querySelector("#support-text");
const promptEl = document.querySelector("#prompt");
const itemsEl = document.querySelector("#items");
const resultEl = document.querySelector("#result");
const submitButton = document.querySelector("#submit-button");
const nextButton = document.querySelector("#next-button");
const difficultyPanel = document.querySelector("#difficulty-panel");


function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("status-error", isError);
  statusEl.hidden = !message;
}


function answerLabel(value) {
  if (value === "correct") {
    return "C";
  }
  if (value === "wrong") {
    return "E";
  }
  return "Anulada";
}


function renderTextBlock(element, text) {
  element.textContent = text;
  element.hidden = !text;
}


function renderQuestion(question) {
  currentQuestion = question;
  corrected = false;
  saved = false;
  pendingAnswers = null;
  formEl.hidden = false;
  resultEl.hidden = true;
  difficultyPanel.hidden = true;
  submitButton.disabled = false;
  submitButton.textContent = "Corrigir";
  setStatus("");

  metaEl.textContent = `${question.chapterTitle} · ${question.examName ?? "TPS"} ${question.examYear ?? ""} · questão ${question.ordinal}`;
  renderTextBlock(supportTextEl, question.supportText);
  promptEl.textContent = question.prompt;
  itemsEl.replaceChildren();

  for (const item of question.items) {
    const itemEl = document.createElement("article");
    itemEl.className = "item";
    itemEl.dataset.itemId = item.id;

    const textEl = document.createElement("p");
    textEl.className = "item-text";
    textEl.textContent = `${item.item_label}. ${item.item_text}`;

    const controlsEl = document.createElement("div");
    controlsEl.className = "answer-controls";
    for (const option of ["correct", "wrong"]) {
      const labelEl = document.createElement("label");
      const inputEl = document.createElement("input");
      inputEl.type = "radio";
      inputEl.name = `answer-${item.id}`;
      inputEl.value = option;
      labelEl.append(inputEl, ` ${answerLabel(option)}`);
      controlsEl.append(labelEl);
    }

    const feedbackEl = document.createElement("div");
    feedbackEl.className = "feedback";
    feedbackEl.hidden = true;

    itemEl.append(textEl, controlsEl, feedbackEl);
    itemsEl.append(itemEl);
  }
}


async function loadQuestion() {
  formEl.hidden = true;
  resultEl.hidden = true;
  setStatus("Carregando questão...");
  const response = await fetch("/api/next-question");
  const payload = await response.json();
  if (!response.ok) {
    setStatus(payload.error ?? "Não há questão vencida.", true);
    return;
  }
  renderQuestion(payload.question);
}


function collectAnswers() {
  const answers = {};
  for (const item of currentQuestion.items) {
    if (item.is_annulled) {
      continue;
    }
    const selected = formEl.querySelector(`input[name="answer-${CSS.escape(item.id)}"]:checked`);
    if (!selected) {
      throw new Error(`Responda o item ${item.item_label}.`);
    }
    answers[item.id] = selected.value;
  }
  return answers;
}


function renderResult(result) {
  corrected = true;
  saved = false;
  difficultyPanel.hidden = false;
  submitButton.disabled = false;
  submitButton.textContent = "Salvar revisão";
  resultEl.hidden = false;
  resultEl.textContent = `${result.grade.correctItems}/${result.grade.totalItems} itens corretos.`;

  for (const gradedItem of result.grade.items) {
    const itemEl = itemsEl.querySelector(`[data-item-id="${CSS.escape(gradedItem.itemId)}"]`);
    const feedbackEl = itemEl.querySelector(".feedback");
    feedbackEl.hidden = false;
    feedbackEl.classList.toggle("feedback-ok", gradedItem.isCorrect);
    feedbackEl.classList.toggle("feedback-bad", !gradedItem.isCorrect);
    feedbackEl.textContent = gradedItem.isAnnulled
      ? "Item anulado."
      : `${gradedItem.isCorrect ? "Acerto" : "Erro"} · gabarito ${answerLabel(gradedItem.answerNormalized)}`;
  }
}


function renderSavedAttempt(result) {
  saved = true;
  submitButton.disabled = true;
  submitButton.textContent = "Revisão salva";
  resultEl.textContent = `${result.grade.correctItems}/${result.grade.totalItems} itens corretos. Próxima revisão: ${new Date(result.schedule.dueAt).toLocaleString("pt-BR")}.`;
}


formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (saved) {
    return;
  }

  try {
    if (!corrected) {
      pendingAnswers = collectAnswers();
      const response = await fetch("/api/corrections", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          groupId: currentQuestion.id,
          answers: pendingAnswers
        })
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error ?? "Falha ao corrigir.");
      }
      renderResult(payload);
      return;
    }

    const difficulty = formEl.querySelector('input[name="difficulty"]:checked')?.value ?? "good";
    const response = await fetch("/api/attempts", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        groupId: currentQuestion.id,
        difficulty,
        answers: pendingAnswers
      })
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error ?? "Falha ao salvar.");
    }
    renderSavedAttempt(payload);
  } catch (error) {
    setStatus(error.message, true);
  }
});


nextButton.addEventListener("click", () => {
  loadQuestion().catch((error) => setStatus(error.message, true));
});


loadQuestion().catch((error) => setStatus(error.message, true));
