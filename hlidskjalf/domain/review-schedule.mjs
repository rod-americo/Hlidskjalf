const DAY_MS = 24 * 60 * 60 * 1000;


export const DIFFICULTIES = new Set(["hard", "good", "easy"]);


export function normalizeDifficulty(value) {
  const normalized = String(value ?? "").trim().toLowerCase();
  if (!DIFFICULTIES.has(normalized)) {
    throw new Error("invalid difficulty");
  }
  return normalized;
}


export function buildReviewSchedule({ previousCard = null, difficulty, correctItems, totalItems, now = new Date() }) {
  const normalizedDifficulty = normalizeDifficulty(difficulty);
  const previousInterval = Number(previousCard?.interval_days ?? 0);
  const previousEase = Number(previousCard?.ease_factor ?? 2.5);
  const previousRepetitions = Number(previousCard?.repetitions ?? 0);
  const previousLapses = Number(previousCard?.lapses ?? 0);
  const hasErrors = correctItems < totalItems;

  let intervalDays;
  let easeFactor = previousEase;
  let repetitions = previousRepetitions + 1;
  let lapses = previousLapses;

  if (normalizedDifficulty === "hard" || hasErrors) {
    intervalDays = Math.max(1, Math.round(previousInterval * 0.5) || 1);
    easeFactor = Math.max(1.3, previousEase - 0.2);
    lapses = hasErrors ? previousLapses + 1 : previousLapses;
  } else if (normalizedDifficulty === "easy") {
    intervalDays = previousRepetitions === 0 ? 3 : Math.max(previousInterval + 1, Math.round(previousInterval * previousEase * 1.4));
    easeFactor = Math.min(3.0, previousEase + 0.15);
  } else {
    intervalDays = previousRepetitions === 0 ? 1 : Math.max(previousInterval + 1, Math.round(previousInterval * previousEase));
  }

  const dueAt = new Date(now.getTime() + intervalDays * DAY_MS).toISOString();
  return {
    dueAt,
    intervalDays,
    easeFactor: Number(easeFactor.toFixed(2)),
    repetitions,
    lapses
  };
}
