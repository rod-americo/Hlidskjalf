#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT / "runtime" / "books" / "tps-comentado-2019-md-reflow"
DEFAULT_PUBLIC_DB = ROOT / "data" / "questions" / "tps-comentado-2019-public.db"
DEFAULT_PRIVATE_DB = ROOT / "runtime" / "books" / "tps-comentado-2019-comments.db"
EXTRACTOR_VERSION = "2026-05-16.1"

CHAPTER_FILES = [
    "01-lingua-portuguesa.md",
    "02-ingles.md",
    "03-politica-internacional.md",
    "04-historia-mundial.md",
    "05-historia-do-brasil.md",
    "06-geografia.md",
    "07-direito-internacional.md",
    "08-direito-interno.md",
    "09-economia.md",
]

ANSWER_MAP = {
    "C": "correct",
    "CERTO": "correct",
    "CORRETO": "correct",
    "E": "wrong",
    "ERRADO": "wrong",
    "INCORRETO": "wrong",
    "INCORRETA": "wrong",
    "A": "A",
    "B": "B",
    "D": "D",
    "ANULADA": "annulled",
    "ANULADO": "annulled",
}

COMMENT_START_RE = re.compile(
    r"(?m)^(?:"
    r"[1-9][0-9]?\s*[:.-]\s*(?:Certo|Errado|Anulad[ao]|Corret[ao]|Incorret[ao])"
    r"|[A-E](?:\s+e\s+[A-E])?\s*[:.-]\s*(?:Certo|Errado|Anulad[ao]|Corret[ao]|Incorret[ao]|Certa|Errada)"
    r")\b",
    flags=re.IGNORECASE,
)
EXAM_HEADER_RE = re.compile(r"^\(Diplomacia\b.*\)", flags=re.IGNORECASE)
EXAM_HEADER_PREFIX_RE = re.compile(r"^(\(Diplomacia\b[^)]*\))\s*(.*)$", flags=re.IGNORECASE)
ITEM_MARKER_RE = re.compile(r"(?=\([1-9][0-9]?\)\s)")
OPTION_MARKER_RE = re.compile(r"(?=\([A-E]\)\s)")
BARE_ITEM_MARKER_RE = re.compile(r"(?m)(?=^[1-9][0-9]?\.\s)")


@dataclass(frozen=True)
class Line:
    number: int
    text: str


@dataclass(frozen=True)
class ParsedBlock:
    question_id: str
    source_file: str
    chapter_number: int
    chapter_title: str
    ordinal: int
    start_line: int
    end_line: int
    header_raw: str
    exam_name: str | None
    exam_year: int | None
    board: str | None
    support_text: str | None
    prompt: str
    question_type: str
    answer_key_raw: str | None
    confidence: float
    needs_review: int
    review_notes: str
    items: list[dict[str, object]]
    comments: list[dict[str, object]]


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def stable_id(*parts: object) -> str:
    payload = "\n".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def read_lines(path: Path) -> list[Line]:
    return [Line(index + 1, text) for index, text in enumerate(path.read_text(encoding="utf-8").splitlines())]


def chapter_metadata(lines: list[Line], fallback_file: str) -> tuple[int, str]:
    for line in lines[:20]:
        match = re.match(r"#\s+([0-9]+)\.\s+(.+)$", line.text.strip())
        if match:
            return int(match.group(1)), normalize_space(match.group(2))

    match = re.match(r"([0-9]+)-(.+)\.md$", fallback_file)
    if match:
        return int(match.group(1)), match.group(2).replace("-", " ").title()
    return 0, fallback_file


def parse_exam_header(header_raw: str) -> tuple[str | None, int | None, str | None]:
    inner = header_raw.strip()[1:-1]
    parts = [normalize_space(part) for part in re.split(r"\s+[–-]\s+", inner)]
    exam_name = parts[0] if parts else None
    year = None
    board = None
    for part in parts[1:]:
        if year is None:
            year_match = re.search(r"\b(20[0-9]{2}|19[0-9]{2})\b", part)
            if year_match:
                year = int(year_match.group(1))
                continue
        if board is None and re.search(r"\b[A-Z]{3,}\b", part):
            board = part

    if year is None:
        year_match = re.search(r"\b(20[0-9]{2}|19[0-9]{2})\b", inner)
        if year_match:
            year = int(year_match.group(1))
    if board is None:
        board_match = re.search(r"\b(CESPE|IADES|CEBRASPE)\b", inner)
        if board_match:
            board = board_match.group(1)

    return exam_name, year, board


def clean_support_text(raw: str) -> str | None:
    lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("<!--"):
            continue
        if stripped.startswith("#"):
            continue
        if re.match(r"^[0-9]+(?:\.[0-9]+)*\.\s+", stripped):
            continue
        lines.append(stripped)

    text = normalize_space("\n".join(lines))
    if len(text) < 30:
        return None
    if not re.search(
        r"\b(Texto|tabela|gr[aá]fico|fragmento|trecho|cita[cç][aã]o|Observe|Considerando essa informa[cç][aã]o)\b",
        text,
        flags=re.IGNORECASE,
    ):
        return None
    return text


def find_gabarito(lines: list[Line]) -> int | None:
    candidates = [
        index
        for index, line in enumerate(lines)
        if re.match(r"^Gabarito\b", line.text.strip(), flags=re.IGNORECASE)
    ]
    if not candidates:
        return None
    return candidates[0]


def parse_answer_key(answer_key_raw: str | None) -> dict[str, str]:
    if not answer_key_raw:
        return {}

    raw = answer_key_raw
    payload = re.sub(r"^Gabarito\s*:?", "", raw, flags=re.IGNORECASE).strip()
    payload = payload.strip(" .\"'“”")
    payload = re.sub(r"([0-9])([A-E])\b", r"\1 \2", payload)

    answers: dict[str, str] = {}
    annulled_group = re.search(
        r"^([0-9,\se]+)\s+Anulad[ao]s?$",
        payload,
        flags=re.IGNORECASE,
    )
    if annulled_group:
        for label in re.findall(r"[0-9]+", annulled_group.group(1)):
            answers[label] = "annulled"
        return answers

    for label, answer in re.findall(
        r"\b([0-9]+)\s*[:.-]?\s*(C|E|A|B|D|ANULADA|ANULADO|Certo|Errado|Correto|Incorreto)\b",
        payload,
        flags=re.IGNORECASE,
    ):
        normalized = normalize_answer(answer)
        if normalized:
            answers[label] = normalized

    if answers:
        return answers

    single = re.search(r"\b(A|B|C|D|E|ANULADA|ANULADO)\b", payload, flags=re.IGNORECASE)
    if single:
        normalized = normalize_answer(single.group(1))
        if normalized:
            answers["answer"] = normalized

    return answers


def parse_multiple_choice_answer_label(answer_key_raw: str | None) -> str | None:
    if not answer_key_raw:
        return None
    payload = re.sub(r"^Gabarito\s*:?", "", answer_key_raw, flags=re.IGNORECASE).strip()
    payload = payload.strip(" .\"'“”")
    if re.search(r"\bANULAD[AO]\b", payload, flags=re.IGNORECASE):
        return "annulled"
    match = re.search(r"\b([A-E])\b", payload, flags=re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None


def normalize_answer(answer: str) -> str | None:
    key = answer.strip().strip(" .\"'“”").upper()
    return ANSWER_MAP.get(key)


def split_question_public_text(public_text: str) -> tuple[str, str, list[tuple[str, str]], str]:
    raw_text = public_text.strip()
    text = normalize_space(raw_text)
    text = re.sub(r"^\.\s+", "", text)
    raw_text = re.sub(r"^\.\s+", "", raw_text)
    if not text:
        return "", "unknown", [], "empty_public_text"

    if OPTION_MARKER_RE.search(text):
        parts = OPTION_MARKER_RE.split(text)
        prompt = normalize_space(parts[0])
        items = []
        for part in parts[1:]:
            match = re.match(r"\(([A-E])\)\s*(.+)$", part, flags=re.S)
            if match:
                items.append((match.group(1), normalize_space(match.group(2))))
        return prompt, "multiple_choice", items, ""

    if ITEM_MARKER_RE.search(text):
        parts = ITEM_MARKER_RE.split(text)
        prompt = normalize_space(parts[0])
        items = []
        for part in parts[1:]:
            match = re.match(r"\(([1-9][0-9]?)\)\s*(.+)$", part, flags=re.S)
            if match:
                items.append((match.group(1), normalize_space(match.group(2))))
        return prompt, "true_false", items, ""

    if BARE_ITEM_MARKER_RE.search(raw_text):
        parts = BARE_ITEM_MARKER_RE.split(raw_text)
        prompt = normalize_space(parts[0])
        items = []
        for part in parts[1:]:
            match = re.match(r"([1-9][0-9]?)\.\s*(.+)$", part, flags=re.S)
            if match:
                items.append((match.group(1), normalize_space(match.group(2))))
        return prompt, "true_false", items, ""

    return text, "single", [("answer", text)], "no_item_markers"


def split_comments(comment_text: str) -> list[tuple[str | None, str]]:
    text = comment_text.strip()
    if not text:
        return []

    pattern = re.compile(
        r"(?m)^(?P<label>[1-9][0-9]?|[A-E](?:\s+e\s+[A-E])?)\s*[:.-]\s+",
    )
    matches = list(pattern.finditer(text))
    if not matches:
        return [(None, text)]

    comments: list[tuple[str | None, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        label = normalize_space(match.group("label"))
        comments.append((label, text[start:end].strip()))
    return comments


def parse_block(
    lines: list[Line],
    source_file: str,
    chapter_number: int,
    chapter_title: str,
    ordinal: int,
    support_raw: str,
) -> ParsedBlock:
    header_match = EXAM_HEADER_PREFIX_RE.match(lines[0].text.strip())
    if header_match:
        header_raw = normalize_space(header_match.group(1))
        inline_public_text = normalize_space(header_match.group(2))
    else:
        header_raw = normalize_space(lines[0].text)
        inline_public_text = ""
    exam_name, exam_year, board = parse_exam_header(header_raw)
    gabarito_index = find_gabarito(lines)
    answer_key_raw = normalize_space(lines[gabarito_index].text) if gabarito_index is not None else None

    body_lines = lines[1:gabarito_index] if gabarito_index is not None else lines[1:]
    body_parts = [inline_public_text] if inline_public_text else []
    body_parts.extend(line.text for line in body_lines)
    body_text = "\n".join(body_parts).strip()
    comment_match = COMMENT_START_RE.search(body_text)
    if comment_match:
        public_text = body_text[: comment_match.start()].strip()
        comment_text = body_text[comment_match.start() :].strip()
    else:
        public_text = body_text
        comment_text = ""

    prompt, question_type, public_items, item_note = split_question_public_text(public_text)
    answer_map = parse_answer_key(answer_key_raw)
    all_items_annulled = bool(
        question_type == "true_false"
        and answer_key_raw
        and re.match(r"^Gabarito\s+Anulad[ao]\b", answer_key_raw, flags=re.IGNORECASE)
    )
    inferred_missing_answer: str | None = None
    if question_type == "true_false" and answer_map and len(set(answer_map.values())) == 1:
        if len(answer_map) >= max(1, len(public_items) - 1):
            inferred_missing_answer = next(iter(answer_map.values()))

    support_text = clean_support_text(support_raw)
    seed = f"{source_file}:{lines[0].number}:{header_raw}:{prompt[:240]}"
    question_id = stable_id("tps-comentado-2019", seed)

    notes: list[str] = []
    confidence = 1.0
    if gabarito_index is None:
        notes.append("gabarito_not_found")
        confidence -= 0.35
    if item_note:
        notes.append(item_note)
        confidence -= 0.20
    if not public_items:
        notes.append("items_not_found")
        confidence -= 0.30

    items: list[dict[str, object]] = []
    selected_option = parse_multiple_choice_answer_label(answer_key_raw) if question_type == "multiple_choice" else None
    for order, (label, text) in enumerate(public_items, start=1):
        answer = answer_map.get(label)
        if answer is None and label == "answer":
            answer = answer_map.get("answer")
        if answer is None and all_items_annulled:
            answer = "annulled"
        if answer is None and inferred_missing_answer is not None:
            answer = inferred_missing_answer
        if answer is None and question_type == "multiple_choice" and selected_option:
            if selected_option == "annulled":
                answer = "annulled"
            elif selected_option in {"A", "B", "C", "D", "E"}:
                answer = "correct" if label == selected_option else "wrong"
        item_confidence = confidence
        if answer is None:
            item_confidence -= 0.25
        items.append(
            {
                "id": stable_id(question_id, label),
                "label": label,
                "order": order,
                "text": text,
                "answer": answer,
                "is_annulled": int(answer == "annulled"),
                "confidence": max(0.0, item_confidence),
            }
        )

    if public_items and not answer_map:
        notes.append("answer_key_not_parsed")
        confidence -= 0.20
    if question_type == "single" and len(public_text) > 800:
        notes.append("single_question_long_text_review")
        confidence -= 0.10

    comments: list[dict[str, object]] = []
    for comment_order, (label, text) in enumerate(split_comments(comment_text), start=1):
        comments.append(
            {
                "id": stable_id(question_id, "comment", comment_order, label or ""),
                "label": label,
                "order": comment_order,
                "text": text,
            }
        )

    confidence = max(0.0, min(1.0, confidence))
    needs_review = int(confidence < 0.75 or bool(notes))

    return ParsedBlock(
        question_id=question_id,
        source_file=source_file,
        chapter_number=chapter_number,
        chapter_title=chapter_title,
        ordinal=ordinal,
        start_line=lines[0].number,
        end_line=lines[-1].number,
        header_raw=header_raw,
        exam_name=exam_name,
        exam_year=exam_year,
        board=board,
        support_text=support_text,
        prompt=prompt,
        question_type=question_type,
        answer_key_raw=answer_key_raw,
        confidence=confidence,
        needs_review=needs_review,
        review_notes=", ".join(notes),
        items=items,
        comments=comments,
    )


def parse_chapter(path: Path) -> list[ParsedBlock]:
    lines = read_lines(path)
    chapter_number, chapter_title = chapter_metadata(lines, path.name)
    header_indexes = [index for index, line in enumerate(lines) if EXAM_HEADER_RE.match(line.text.strip())]
    blocks: list[ParsedBlock] = []
    last_gabarito_end = 0

    for ordinal, header_index in enumerate(header_indexes, start=1):
        next_header = header_indexes[ordinal] if ordinal < len(header_indexes) else len(lines)
        support_raw = "\n".join(line.text for line in lines[last_gabarito_end:header_index])
        block_lines = lines[header_index:next_header]
        parsed = parse_block(block_lines, path.name, chapter_number, chapter_title, ordinal, support_raw)
        blocks.append(parsed)

        gabarito_relative = find_gabarito(block_lines)
        if gabarito_relative is not None:
            last_gabarito_end = header_index + gabarito_relative + 1
        else:
            last_gabarito_end = header_index + 1

    return blocks


def create_public_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE extraction_runs (
            id INTEGER PRIMARY KEY,
            source_name TEXT NOT NULL,
            source_dir TEXT NOT NULL,
            created_at TEXT NOT NULL,
            extractor_version TEXT NOT NULL,
            question_count INTEGER NOT NULL,
            item_count INTEGER NOT NULL,
            review_count INTEGER NOT NULL
        );

        CREATE TABLE question_groups (
            id TEXT PRIMARY KEY,
            source_name TEXT NOT NULL,
            source_file TEXT NOT NULL,
            chapter_number INTEGER NOT NULL,
            chapter_title TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            start_line INTEGER NOT NULL,
            end_line INTEGER NOT NULL,
            exam_name TEXT,
            exam_year INTEGER,
            board TEXT,
            header_raw TEXT NOT NULL,
            support_text TEXT,
            prompt TEXT NOT NULL,
            question_type TEXT NOT NULL,
            answer_key_raw TEXT,
            confidence REAL NOT NULL,
            needs_review INTEGER NOT NULL,
            review_notes TEXT NOT NULL
        );

        CREATE TABLE question_items (
            id TEXT PRIMARY KEY,
            group_id TEXT NOT NULL REFERENCES question_groups(id) ON DELETE CASCADE,
            item_label TEXT NOT NULL,
            item_order INTEGER NOT NULL,
            item_text TEXT NOT NULL,
            answer_normalized TEXT,
            is_annulled INTEGER NOT NULL,
            confidence REAL NOT NULL,
            UNIQUE(group_id, item_label)
        );

        CREATE TABLE question_tags (
            group_id TEXT NOT NULL REFERENCES question_groups(id) ON DELETE CASCADE,
            tag TEXT NOT NULL,
            source TEXT NOT NULL,
            PRIMARY KEY (group_id, tag)
        );

        CREATE INDEX idx_question_groups_chapter ON question_groups(chapter_number, ordinal);
        CREATE INDEX idx_question_groups_exam ON question_groups(exam_year, board);
        CREATE INDEX idx_question_items_group ON question_items(group_id, item_order);
        """
    )


def create_private_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE extraction_runs (
            id INTEGER PRIMARY KEY,
            source_name TEXT NOT NULL,
            source_dir TEXT NOT NULL,
            created_at TEXT NOT NULL,
            extractor_version TEXT NOT NULL,
            comment_count INTEGER NOT NULL
        );

        CREATE TABLE question_comments (
            id TEXT PRIMARY KEY,
            group_id TEXT NOT NULL,
            item_label TEXT,
            comment_order INTEGER NOT NULL,
            comment_text TEXT NOT NULL,
            source_file TEXT NOT NULL,
            question_start_line INTEGER NOT NULL,
            question_end_line INTEGER NOT NULL
        );

        CREATE INDEX idx_question_comments_group ON question_comments(group_id, comment_order);
        """
    )


def write_databases(blocks: list[ParsedBlock], source_dir: Path, public_db: Path, private_db: Path) -> None:
    public_db.parent.mkdir(parents=True, exist_ok=True)
    private_db.parent.mkdir(parents=True, exist_ok=True)
    public_db.unlink(missing_ok=True)
    private_db.unlink(missing_ok=True)

    created_at = datetime.now(timezone.utc).isoformat()
    public_conn = sqlite3.connect(public_db)
    private_conn = sqlite3.connect(private_db)
    try:
        create_public_schema(public_conn)
        create_private_schema(private_conn)

        item_count = sum(len(block.items) for block in blocks)
        review_count = sum(block.needs_review for block in blocks)
        comment_count = sum(len(block.comments) for block in blocks)

        public_conn.execute(
            """
            INSERT INTO extraction_runs
            (source_name, source_dir, created_at, extractor_version, question_count, item_count, review_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "tps-comentado-2019",
                str(source_dir),
                created_at,
                EXTRACTOR_VERSION,
                len(blocks),
                item_count,
                review_count,
            ),
        )
        private_conn.execute(
            """
            INSERT INTO extraction_runs
            (source_name, source_dir, created_at, extractor_version, comment_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("tps-comentado-2019", str(source_dir), created_at, EXTRACTOR_VERSION, comment_count),
        )

        for block in blocks:
            public_conn.execute(
                """
                INSERT INTO question_groups
                (id, source_name, source_file, chapter_number, chapter_title, ordinal, start_line, end_line,
                 exam_name, exam_year, board, header_raw, support_text, prompt, question_type,
                 answer_key_raw, confidence, needs_review, review_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    block.question_id,
                    "tps-comentado-2019",
                    block.source_file,
                    block.chapter_number,
                    block.chapter_title,
                    block.ordinal,
                    block.start_line,
                    block.end_line,
                    block.exam_name,
                    block.exam_year,
                    block.board,
                    block.header_raw,
                    block.support_text,
                    block.prompt,
                    block.question_type,
                    block.answer_key_raw,
                    block.confidence,
                    block.needs_review,
                    block.review_notes,
                ),
            )
            public_conn.execute(
                """
                INSERT OR IGNORE INTO question_tags (group_id, tag, source)
                VALUES (?, ?, ?)
                """,
                (block.question_id, block.chapter_title, "chapter"),
            )

            for item in block.items:
                public_conn.execute(
                    """
                    INSERT INTO question_items
                    (id, group_id, item_label, item_order, item_text, answer_normalized, is_annulled, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["id"],
                        block.question_id,
                        item["label"],
                        item["order"],
                        item["text"],
                        item["answer"],
                        item["is_annulled"],
                        item["confidence"],
                    ),
                )

            for comment in block.comments:
                private_conn.execute(
                    """
                    INSERT INTO question_comments
                    (id, group_id, item_label, comment_order, comment_text,
                     source_file, question_start_line, question_end_line)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        comment["id"],
                        block.question_id,
                        comment["label"],
                        comment["order"],
                        comment["text"],
                        block.source_file,
                        block.start_line,
                        block.end_line,
                    ),
                )

        public_conn.commit()
        private_conn.commit()
    finally:
        public_conn.close()
        private_conn.close()


def collect_blocks(source_dir: Path) -> list[ParsedBlock]:
    blocks: list[ParsedBlock] = []
    for filename in CHAPTER_FILES:
        path = source_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de capitulo ausente: {path}")
        blocks.extend(parse_chapter(path))
    return blocks


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extrai questoes publicas e comentarios privados do TPS Comentado 2019.",
    )
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--public-db", type=Path, default=DEFAULT_PUBLIC_DB)
    parser.add_argument("--private-db", type=Path, default=DEFAULT_PRIVATE_DB)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    source_dir = args.source_dir.resolve()
    public_db = args.public_db.resolve()
    private_db = args.private_db.resolve()

    blocks = collect_blocks(source_dir)
    write_databases(blocks, source_dir, public_db, private_db)

    item_count = sum(len(block.items) for block in blocks)
    review_count = sum(block.needs_review for block in blocks)
    comment_count = sum(len(block.comments) for block in blocks)
    print(f"Banco publico: {public_db}")
    print(f"Banco privado: {private_db}")
    print(f"Questoes: {len(blocks)}")
    print(f"Itens/alternativas: {item_count}")
    print(f"Comentarios privados: {comment_count}")
    print(f"Marcadas para revisao: {review_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
