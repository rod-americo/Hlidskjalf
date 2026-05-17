import { gradeAttempt } from "../domain/attempt.mjs";
import { buildReviewSchedule, normalizeDifficulty } from "../domain/review-schedule.mjs";
import { getQuestionById, getNextQuestion } from "../infrastructure/question-db.mjs";
import { ensureProgressDb, getReviewCard, saveAttempt } from "../infrastructure/progress-db.mjs";


export function createPracticeService(settings) {
  ensureProgressDb(settings.progress.dbPath);

  return {
    nextQuestion() {
      return getNextQuestion(settings.questions.publicDbPath, settings.progress.dbPath, {
        chapterNumber: settings.questions.pilotChapterNumber
      });
    },

    gradeAttempt(payload) {
      const groupId = String(payload?.groupId ?? "");
      const answers = payload?.answers;
      if (!groupId || !answers || typeof answers !== "object" || Array.isArray(answers)) {
        throw new Error("invalid attempt payload");
      }

      const question = getQuestionById(settings.questions.publicDbPath, groupId);
      if (!question) {
        throw new Error("question not found");
      }

      return {
        groupId,
        grade: gradeAttempt(question, answers)
      };
    },

    submitAttempt(payload) {
      const groupId = String(payload?.groupId ?? "");
      const difficulty = normalizeDifficulty(payload?.difficulty);
      const answers = payload?.answers;
      if (!groupId || !answers || typeof answers !== "object" || Array.isArray(answers)) {
        throw new Error("invalid attempt payload");
      }

      const question = getQuestionById(settings.questions.publicDbPath, groupId);
      if (!question) {
        throw new Error("question not found");
      }

      const grade = gradeAttempt(question, answers);
      const attemptedAt = new Date().toISOString();
      const previousCard = getReviewCard(settings.progress.dbPath, groupId);
      const schedule = buildReviewSchedule({
        previousCard,
        difficulty,
        correctItems: grade.correctItems,
        totalItems: grade.totalItems,
        now: new Date(attemptedAt)
      });
      const { attemptId } = saveAttempt(settings.progress.dbPath, {
        groupId,
        attemptedAt,
        difficulty,
        grade,
        schedule
      });

      return {
        attemptId,
        attemptedAt,
        groupId,
        difficulty,
        grade,
        schedule
      };
    }
  };
}
