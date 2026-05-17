export function normalizeUserAnswer(value) {
  const normalized = String(value ?? "").trim().toLowerCase();
  if (["correct", "wrong"].includes(normalized)) {
    return normalized;
  }
  throw new Error("invalid answer");
}


export function gradeAttempt(question, answersByItemId) {
  const gradedItems = question.items.map((item) => {
    const answerNormalized = item.is_annulled ? "annulled" : item.answer_normalized;
    const userAnswer = answersByItemId[item.id] ?? null;

    if (answerNormalized === "annulled") {
      return {
        itemId: item.id,
        itemLabel: item.item_label,
        userAnswer,
        answerNormalized,
        isCorrect: true,
        isAnnulled: true
      };
    }

    const normalizedUserAnswer = normalizeUserAnswer(userAnswer);
    return {
      itemId: item.id,
      itemLabel: item.item_label,
      userAnswer: normalizedUserAnswer,
      answerNormalized,
      isCorrect: normalizedUserAnswer === answerNormalized,
      isAnnulled: false
    };
  });

  const totalItems = gradedItems.length;
  const annulledItems = gradedItems.filter((item) => item.isAnnulled).length;
  const correctItems = gradedItems.filter((item) => item.isCorrect).length;

  return {
    items: gradedItems,
    totalItems,
    correctItems,
    wrongItems: totalItems - correctItems,
    annulledItems
  };
}
