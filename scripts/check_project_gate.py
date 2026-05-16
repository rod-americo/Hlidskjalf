#!/usr/bin/env python3

from __future__ import annotations

import re
import sys
from pathlib import Path


PROJECT_GATE = Path(__file__).resolve().parents[1] / "PROJECT_GATE.md"
REQUIRED_SECTION_PREFIXES = ("## 1.", "## 2.", "## 3.", "## 4.", "## 5.")
PENDING_MARKERS = ("TODO", "preencher", "{{")
WEAK_EXACT_VALUES = {
    "",
    "?",
    "-",
    "n/a",
    "na",
    "nao sei",
    "não sei",
    "nao aplicavel",
    "não aplicável",
    "nao se aplica",
    "não se aplica",
    "a definir",
    "depois vejo",
    "talvez",
    "placeholder",
}
WEAK_SUBSTRINGS = (
    "depois vejo",
    "a definir",
    "nao sei",
    "não sei",
    "talvez",
    "placeholder",
    "qualquer coisa",
)
FIELD_RULES = {
    "problema real": {"min_words": 5, "min_chars": 24},
    "usuario ou operador alvo": {"min_words": 3, "min_chars": 12},
    "resultado esperado": {"min_words": 4, "min_chars": 20},
    "repositorio candidato que poderia absorver isso": {"min_words": 1, "min_chars": 4},
    "por que esse acoplamento seria inadequado": {"min_words": 5, "min_chars": 24},
    "fronteira que justifica um repositório separado": {"min_words": 5, "min_chars": 24},
    "configuracao": {"min_words": 2, "min_chars": 8},
    "logging": {"min_words": 2, "min_chars": 8},
    "runtime": {"min_words": 2, "min_chars": 8},
    "contratos": {"min_words": 2, "min_chars": 8},
    "autenticacao ou transporte": {"min_words": 2, "min_chars": 8},
    "responsabilidades fora de escopo": {"min_words": 4, "min_chars": 20},
    "integrações que pertencem a outro sistema": {"min_words": 3, "min_chars": 15},
    "dados que nao devem morar aqui": {"min_words": 2, "min_chars": 12},
    "host ou ambiente principal": {"min_words": 2, "min_chars": 6},
    "dependencia externa mais fragil": {"min_words": 2, "min_chars": 6},
    "necessidade de restart": {"min_words": 3, "min_chars": 12},
    "necessidade de backup": {"min_words": 3, "min_chars": 12},
    "risco operacional": {"min_words": 4, "min_chars": 20},
}


def normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def word_count(value: str) -> int:
    return len(re.findall(r"[\w/-]+", value, flags=re.UNICODE))


def collect_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    current_required = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip()

        if line.startswith("## "):
            current_required = line.startswith(REQUIRED_SECTION_PREFIXES)
            continue

        if not current_required or not line.startswith("- "):
            continue

        content = line[2:].strip()
        if ":" not in content:
            continue

        label, value = content.split(":", 1)
        fields[label.strip()] = value.strip()

    return fields


def classify_fields(fields: dict[str, str]) -> tuple[list[str], list[tuple[str, str]], list[tuple[str, str]]]:
    pending: list[str] = []
    weak: list[tuple[str, str]] = []
    short: list[tuple[str, str]] = []

    for label, rules in FIELD_RULES.items():
        value = fields.get(label, "").strip()
        normalized = normalize_text(value)

        if not value:
            pending.append(label)
            continue

        if any(marker.lower() in normalized for marker in PENDING_MARKERS):
            pending.append(label)
            continue

        if normalized in WEAK_EXACT_VALUES or any(marker in normalized for marker in WEAK_SUBSTRINGS):
            weak.append((label, value))
            continue

        words = word_count(value)
        chars = len(value)
        min_words = int(rules["min_words"])
        min_chars = int(rules["min_chars"])
        if words < min_words or chars < min_chars:
            short.append(
                (
                    label,
                    f"{words} palavra(s), {chars} caractere(s); minimo {min_words} palavra(s) e {min_chars} caractere(s)",
                )
            )

    return pending, weak, short


def main() -> int:
    if not PROJECT_GATE.exists():
        print(f"PROJECT_GATE.md ausente: {PROJECT_GATE}", file=sys.stderr)
        return 1

    text = PROJECT_GATE.read_text(encoding="utf-8")
    fields = collect_fields(text)
    pending, weak, short = classify_fields(fields)

    if pending or weak or short:
        print("PROJECT_GATE.md falhou na validacao semantica.", file=sys.stderr)

    if pending:
        print("", file=sys.stderr)
        print("Pendencias estruturais:", file=sys.stderr)
        for field in pending:
            print(f"- {field}", file=sys.stderr)

    if weak:
        print("", file=sys.stderr)
        print("Respostas vagas demais:", file=sys.stderr)
        for field, value in weak:
            print(f"- {field}: {value}", file=sys.stderr)

    if short:
        print("", file=sys.stderr)
        print("Respostas curtas demais:", file=sys.stderr)
        for field, reason in short:
            print(f"- {field}: {reason}", file=sys.stderr)

    if pending or weak or short:
        print("", file=sys.stderr)
        print(
            "Evite respostas como 'a definir', 'nao sei', 'talvez' ou frases curtas sem justificativa.",
            file=sys.stderr,
        )
        print("Preencha o gate antes do primeiro commit relevante.", file=sys.stderr)
        return 1

    print("PROJECT_GATE.md validado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
