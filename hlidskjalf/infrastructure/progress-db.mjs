import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { queryJson, runSql, sqlValue } from "./sqlite-cli.mjs";


const CURRENT_SCHEMA_VERSION = 1;


export function ensureProgressDb(dbPath) {
  fs.mkdirSync(path.dirname(dbPath), { recursive: true });
  runSql(dbPath, `
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (
  id TEXT PRIMARY KEY,
  group_id TEXT NOT NULL,
  attempted_at TEXT NOT NULL,
  difficulty TEXT NOT NULL CHECK (difficulty IN ('hard', 'good', 'easy')),
  total_items INTEGER NOT NULL,
  correct_items INTEGER NOT NULL,
  wrong_items INTEGER NOT NULL,
  annulled_items INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attempts_group ON attempts(group_id, attempted_at);
CREATE TABLE IF NOT EXISTS attempt_answers (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
  item_id TEXT NOT NULL,
  item_label TEXT NOT NULL,
  user_answer TEXT,
  answer_normalized TEXT NOT NULL,
  is_correct INTEGER NOT NULL,
  is_annulled INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attempt_answers_attempt ON attempt_answers(attempt_id);
CREATE TABLE IF NOT EXISTS review_cards (
  group_id TEXT PRIMARY KEY,
  due_at TEXT NOT NULL,
  interval_days INTEGER NOT NULL,
  ease_factor REAL NOT NULL,
  repetitions INTEGER NOT NULL,
  lapses INTEGER NOT NULL,
  updated_at TEXT NOT NULL,
  last_attempt_id TEXT NOT NULL REFERENCES attempts(id)
);
INSERT OR IGNORE INTO schema_migrations(version, applied_at)
VALUES (${CURRENT_SCHEMA_VERSION}, datetime('now'));
`);
}


export function getReviewCard(dbPath, groupId) {
  return queryJson(dbPath, `
SELECT group_id, due_at, interval_days, ease_factor, repetitions, lapses, updated_at, last_attempt_id
FROM review_cards
WHERE group_id = ${sqlValue(groupId)}
LIMIT 1;
`)[0] ?? null;
}


export function saveAttempt(dbPath, { groupId, attemptedAt, difficulty, grade, schedule }) {
  const attemptId = crypto.randomUUID();
  const answerInserts = grade.items.map((item) => `
INSERT INTO attempt_answers(id, attempt_id, item_id, item_label, user_answer, answer_normalized, is_correct, is_annulled)
VALUES (${sqlValue(crypto.randomUUID())}, ${sqlValue(attemptId)}, ${sqlValue(item.itemId)}, ${sqlValue(item.itemLabel)}, ${sqlValue(item.userAnswer)}, ${sqlValue(item.answerNormalized)}, ${item.isCorrect ? 1 : 0}, ${item.isAnnulled ? 1 : 0});
`).join("\n");

  runSql(dbPath, `
PRAGMA foreign_keys = ON;
BEGIN IMMEDIATE;
INSERT INTO attempts(id, group_id, attempted_at, difficulty, total_items, correct_items, wrong_items, annulled_items)
VALUES (${sqlValue(attemptId)}, ${sqlValue(groupId)}, ${sqlValue(attemptedAt)}, ${sqlValue(difficulty)}, ${grade.totalItems}, ${grade.correctItems}, ${grade.wrongItems}, ${grade.annulledItems});
${answerInserts}
INSERT INTO review_cards(group_id, due_at, interval_days, ease_factor, repetitions, lapses, updated_at, last_attempt_id)
VALUES (${sqlValue(groupId)}, ${sqlValue(schedule.dueAt)}, ${schedule.intervalDays}, ${schedule.easeFactor}, ${schedule.repetitions}, ${schedule.lapses}, ${sqlValue(attemptedAt)}, ${sqlValue(attemptId)})
ON CONFLICT(group_id) DO UPDATE SET
  due_at = excluded.due_at,
  interval_days = excluded.interval_days,
  ease_factor = excluded.ease_factor,
  repetitions = excluded.repetitions,
  lapses = excluded.lapses,
  updated_at = excluded.updated_at,
  last_attempt_id = excluded.last_attempt_id;
COMMIT;
`);
  return { attemptId };
}
