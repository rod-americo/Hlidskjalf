import { queryJson, quoteAttachPath, sqlValue } from "./sqlite-cli.mjs";


function mapQuestion(rows) {
  if (rows.length === 0) {
    return null;
  }
  const first = rows[0];
  return {
    id: first.group_id,
    sourceName: first.source_name,
    chapterNumber: first.chapter_number,
    chapterTitle: first.chapter_title,
    ordinal: first.ordinal,
    examName: first.exam_name,
    examYear: first.exam_year,
    board: first.board,
    supportText: first.support_text ?? "",
    prompt: first.prompt,
    questionType: first.question_type,
    items: rows.map((row) => ({
      id: row.item_id,
      group_id: row.group_id,
      item_label: row.item_label,
      item_order: row.item_order,
      item_text: row.item_text,
      answer_normalized: row.answer_normalized,
      is_annulled: Boolean(row.is_annulled)
    }))
  };
}


export function getQuestionById(publicDbPath, groupId) {
  const rows = queryJson(publicDbPath, `
SELECT
  q.id AS group_id,
  q.source_name,
  q.chapter_number,
  q.chapter_title,
  q.ordinal,
  q.exam_name,
  q.exam_year,
  q.board,
  q.support_text,
  q.prompt,
  q.question_type,
  i.id AS item_id,
  i.item_label,
  i.item_order,
  i.item_text,
  i.answer_normalized,
  i.is_annulled
FROM question_groups q
JOIN question_items i ON i.group_id = q.id
WHERE q.id = ${sqlValue(groupId)}
ORDER BY i.item_order;
`);
  return mapQuestion(rows);
}


export function getNextQuestion(publicDbPath, progressDbPath, { chapterNumber = 1, now = new Date().toISOString() } = {}) {
  const rows = queryJson(publicDbPath, `
ATTACH DATABASE ${quoteAttachPath(progressDbPath)} AS progress;
WITH candidate AS (
  SELECT q.id
  FROM question_groups q
  LEFT JOIN progress.review_cards r ON r.group_id = q.id
  WHERE q.chapter_number = ${Number(chapterNumber)}
    AND (r.group_id IS NULL OR r.due_at <= ${sqlValue(now)})
  ORDER BY
    CASE WHEN r.group_id IS NULL THEN 0 ELSE 1 END,
    COALESCE(r.due_at, ''),
    q.ordinal
  LIMIT 1
)
SELECT
  q.id AS group_id,
  q.source_name,
  q.chapter_number,
  q.chapter_title,
  q.ordinal,
  q.exam_name,
  q.exam_year,
  q.board,
  q.support_text,
  q.prompt,
  q.question_type,
  i.id AS item_id,
  i.item_label,
  i.item_order,
  i.item_text,
  i.answer_normalized,
  i.is_annulled
FROM candidate c
JOIN question_groups q ON q.id = c.id
JOIN question_items i ON i.group_id = q.id
ORDER BY i.item_order;
`);
  return mapQuestion(rows);
}
