#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCTOR_CONFIG_PATH = ROOT / "config" / "doctor.json"
REQUIRED_FILES = [
    ROOT / "README.md",
    ROOT / "AGENTS.md",
    ROOT / "PROJECT_GATE.md",
    DOCTOR_CONFIG_PATH,
    ROOT / "docs" / "ARCHITECTURE.md",
    ROOT / "docs" / "CONTRACTS.md",
    ROOT / "docs" / "OPERATIONS.md",
    ROOT / "docs" / "DECISIONS.md",
    ROOT / "scripts" / "check_project_gate.py",
]
KEY_DOCS = [
    ROOT / "README.md",
    ROOT / "docs" / "ARCHITECTURE.md",
    ROOT / "docs" / "CONTRACTS.md",
    ROOT / "docs" / "OPERATIONS.md",
]
STOPWORDS = {
    "este",
    "esta",
    "esse",
    "essa",
    "para",
    "com",
    "sem",
    "onde",
    "quando",
    "ainda",
    "depois",
    "sobre",
    "entre",
    "muito",
    "pouco",
    "seria",
    "deveria",
    "repositorio",
    "repositório",
    "projeto",
    "sistema",
    "modulo",
    "módulo",
    "core",
    "local",
    "dados",
    "coisa",
    "coisas",
}
KNOWN_WARNING_CODES = {
    "scope_negative_mismatch",
    "objective_mismatch",
    "scope_architecture_mismatch",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_section(text: str, heading: str) -> str | None:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != heading:
            continue

        level = len(line) - len(line.lstrip("#"))
        section: list[str] = []
        for candidate in lines[index + 1 :]:
            stripped = candidate.strip()
            if stripped.startswith("#"):
                candidate_level = len(stripped) - len(stripped.lstrip("#"))
                if candidate_level <= level:
                    break
            section.append(candidate)
        return "\n".join(section).strip()
    return None


def extract_first_code_block(section: str | None) -> str | None:
    if not section:
        return None
    match = re.search(r"```(?:bash)?\n(.*?)```", section, flags=re.S)
    if not match:
        return None
    return match.group(1).strip()


def normalize_block(value: str | None) -> str | None:
    if value is None:
        return None
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    return "\n".join(lines)


def extract_bullets(section: str | None) -> list[str]:
    if not section:
        return []
    bullets: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
    return bullets


def extract_readme_entrypoints(text: str) -> list[str]:
    match = re.search(
        r"entrypoints principais:\n((?:\s+- `[^`]+`\n?)+)",
        text,
        flags=re.S,
    )
    if not match:
        return []
    return re.findall(r"`([^`]+)`", match.group(1))


def extract_agents_validation(text: str) -> str | None:
    match = re.search(r"comando de validacao minima:\s*`([^`]+)`", text)
    if not match:
        return None
    return match.group(1).strip()


def normalize_token(token: str) -> str:
    cleaned = re.sub(r"[^A-Za-zÀ-ÿ0-9_-]+", "", token.lower())
    return cleaned.strip("_-")


def load_doctor_config(errors: list[str]) -> dict[str, object]:
    default = {
        "version": 1,
        "ignored_warnings": [],
        "token_alias_groups": [],
    }
    if not DOCTOR_CONFIG_PATH.exists():
        return default

    try:
        raw = json.loads(read_text(DOCTOR_CONFIG_PATH))
    except json.JSONDecodeError as exc:
        add_error(errors, f"config/doctor.json invalido: {exc}")
        return default

    if not isinstance(raw, dict):
        add_error(errors, "config/doctor.json deve ser um objeto JSON")
        return default

    version = raw.get("version", 1)
    if version != 1:
        add_error(errors, "config/doctor.json usa versao nao suportada")

    ignored_warnings_raw = raw.get("ignored_warnings", [])
    normalized_ignored: list[dict[str, str]] = []
    seen_ignored_codes: set[str] = set()
    if not isinstance(ignored_warnings_raw, list):
        add_error(errors, "config/doctor.json: ignored_warnings deve ser uma lista")
    else:
        for index, item in enumerate(ignored_warnings_raw):
            if not isinstance(item, dict):
                add_error(
                    errors,
                    f"config/doctor.json: ignored_warnings[{index}] deve ser um objeto",
                )
                continue

            code = str(item.get("code", "")).strip()
            reason = str(item.get("reason", "")).strip()
            if code not in KNOWN_WARNING_CODES:
                add_error(
                    errors,
                    f"config/doctor.json: codigo de warning desconhecido em ignored_warnings[{index}]",
                )
                continue
            if code in seen_ignored_codes:
                add_error(
                    errors,
                    f"config/doctor.json: codigo duplicado em ignored_warnings[{index}]",
                )
                continue
            if len(reason) < 12:
                add_error(
                    errors,
                    f"config/doctor.json: reason curto demais em ignored_warnings[{index}]",
                )
                continue
            seen_ignored_codes.add(code)
            normalized_ignored.append({"code": code, "reason": reason})

    alias_groups_raw = raw.get("token_alias_groups", [])
    normalized_alias_groups: list[set[str]] = []
    if not isinstance(alias_groups_raw, list):
        add_error(errors, "config/doctor.json: token_alias_groups deve ser uma lista")
    else:
        for index, item in enumerate(alias_groups_raw):
            if not isinstance(item, list):
                add_error(
                    errors,
                    f"config/doctor.json: token_alias_groups[{index}] deve ser uma lista",
                )
                continue
            tokens = {normalize_token(str(value)) for value in item if normalize_token(str(value))}
            if len(tokens) < 2:
                add_error(
                    errors,
                    f"config/doctor.json: token_alias_groups[{index}] precisa ter ao menos 2 termos validos",
                )
                continue
            normalized_alias_groups.append(tokens)

    return {
        "version": 1,
        "ignored_warnings": normalized_ignored,
        "token_alias_groups": normalized_alias_groups,
    }


def significant_tokens(text: str) -> set[str]:
    tokens = set()
    for token in re.findall(r"[A-Za-zÀ-ÿ0-9_-]+", text.lower()):
        if len(token) < 5:
            continue
        if token in STOPWORDS:
            continue
        normalized = normalize_token(token)
        if normalized:
            tokens.add(normalized)
    return tokens


def compare_token_sets(
    left_text: str,
    right_text: str,
    alias_groups: list[set[str]],
) -> dict[str, object]:
    left_tokens = significant_tokens(left_text)
    right_tokens = significant_tokens(right_text)
    shared_tokens = left_tokens & right_tokens
    matched_alias_indexes: list[int] = []

    if not shared_tokens:
        for index, group in enumerate(alias_groups):
            if left_tokens & group and right_tokens & group:
                matched_alias_indexes.append(index)

    return {
        "shared_tokens": shared_tokens,
        "matched_alias_indexes": matched_alias_indexes,
    }


def add_error(errors: list[str], message: str) -> None:
    errors.append(message)


def add_warning(warnings: list[dict[str, str]], code: str, message: str) -> None:
    warnings.append({"code": code, "message": message})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valida coerencia estrutural minima do projeto")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="trata warnings semanticos como erro",
    )
    parser.add_argument(
        "--audit-config",
        action="store_true",
        help="audita config/doctor.json e overrides semanticos",
    )
    return parser.parse_args()


def print_warning_list(title: str, warnings: list[dict[str, str]], stream: object) -> None:
    if not warnings:
        return
    print(title, file=stream)
    for warning in warnings:
        print(f"- [{warning['code']}] {warning['message']}", file=stream)


def run_config_audit(
    doctor_config: dict[str, object],
    raw_warnings: list[dict[str, str]],
    comparison_reports: list[dict[str, object]],
) -> int:
    ignored_entries = list(doctor_config["ignored_warnings"])
    alias_groups = list(doctor_config["token_alias_groups"])
    ignored_reason_by_code = {
        item["code"]: item["reason"]
        for item in ignored_entries
        if isinstance(item, dict) and "code" in item and "reason" in item
    }
    raw_codes = {item["code"] for item in raw_warnings}
    stale_ignored_codes = sorted(set(ignored_reason_by_code) - raw_codes)
    suppressed_warnings = [
        item for item in raw_warnings if item.get("code") in ignored_reason_by_code
    ]

    alias_usage: dict[int, list[str]] = {}
    for report in comparison_reports:
        for alias_index in report["matched_alias_indexes"]:
            alias_usage.setdefault(alias_index, []).append(str(report["code"]))

    print("Doctor config audit:")
    print(f"- ignored_warnings: {len(ignored_entries)}")
    print(f"- token_alias_groups: {len(alias_groups)}")

    if not ignored_entries and not alias_groups:
        print("- sem overrides configurados")

    if suppressed_warnings:
        print("")
        print("Warnings suprimidos atualmente:")
        for warning in suppressed_warnings:
            code = str(warning["code"])
            reason = ignored_reason_by_code.get(code, "sem reason registrado")
            print(f"- [{code}] {warning['message']}")
            print(f"  reason: {reason}")

    if stale_ignored_codes:
        print("")
        print("Ignored warnings sem efeito atual:", file=sys.stderr)
        for code in stale_ignored_codes:
            print(f"- [{code}] {ignored_reason_by_code[code]}", file=sys.stderr)

    if alias_usage:
        print("")
        print("Alias groups em uso:")
        for index in sorted(alias_usage):
            tokens = ", ".join(sorted(alias_groups[index]))
            codes = ", ".join(sorted(set(alias_usage[index])))
            print(f"- group {index}: {tokens} -> {codes}")

    unused_alias_indexes = [
        index for index in range(len(alias_groups)) if index not in alias_usage
    ]
    if unused_alias_indexes:
        print("")
        print("Alias groups sem uso observavel agora:")
        for index in unused_alias_indexes:
            tokens = ", ".join(sorted(alias_groups[index]))
            print(f"- group {index}: {tokens}")

    if stale_ignored_codes:
        return 1

    print("")
    print("Doctor config audit passou.")
    return 0


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    warnings: list[dict[str, str]] = []

    for path in REQUIRED_FILES:
        if not path.exists():
            add_error(errors, f"arquivo obrigatorio ausente: {path.relative_to(ROOT)}")

    if errors:
        for message in errors:
            print(f"ERRO: {message}", file=sys.stderr)
        return 1

    doctor_config = load_doctor_config(errors)
    if errors:
        print("Project doctor encontrou erros:", file=sys.stderr)
        for message in errors:
            print(f"- {message}", file=sys.stderr)
        return 1

    alias_groups = list(doctor_config["token_alias_groups"])
    ignored_warning_codes = {
        item["code"]
        for item in doctor_config["ignored_warnings"]
        if isinstance(item, dict) and "code" in item
    }

    docs = {path: read_text(path) for path in KEY_DOCS}
    readme_text = read_text(ROOT / "README.md")
    agents_text = read_text(ROOT / "AGENTS.md")
    gate_text = read_text(ROOT / "PROJECT_GATE.md")
    architecture_text = read_text(ROOT / "docs" / "ARCHITECTURE.md")
    contracts_text = read_text(ROOT / "docs" / "CONTRACTS.md")
    operations_text = read_text(ROOT / "docs" / "OPERATIONS.md")

    gate_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_project_gate.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    if gate_check.returncode != 0:
        add_error(errors, "PROJECT_GATE.md falhou em scripts/check_project_gate.py")

    for path, text in docs.items():
        if "{{" in text:
            add_error(errors, f"placeholders nao resolvidos em {path.relative_to(ROOT)}")
        if re.search(r"\bTODO:", text):
            add_error(errors, f"TODO remanescente em {path.relative_to(ROOT)}")
        if re.search(r"\bpreencher\b", text.lower()):
            add_error(errors, f"marcador de scaffolding remanescente em {path.relative_to(ROOT)}")

    required_sections = {
        ROOT / "README.md": [
            "## O que este repositorio e",
            "## O que este repositorio NAO e",
            "### 4. Rodar",
        ],
        ROOT / "docs" / "ARCHITECTURE.md": [
            "## 2. Escopo",
            "## 5. Fluxo principal",
        ],
        ROOT / "docs" / "CONTRACTS.md": [
            "## 2. Entradas canonicas",
            "## 3. Saidas canonicas",
        ],
        ROOT / "docs" / "OPERATIONS.md": [
            "### Boot principal",
            "## 5. Validacao minima",
        ],
    }
    for path, headings in required_sections.items():
        text = read_text(path)
        for heading in headings:
            if extract_section(text, heading) is None:
                add_error(errors, f"secao ausente em {path.relative_to(ROOT)}: {heading}")

    readme_run = normalize_block(
        extract_first_code_block(extract_section(readme_text, "### 4. Rodar"))
    )
    ops_run = normalize_block(
        extract_first_code_block(extract_section(operations_text, "### Boot principal"))
    )
    if readme_run and ops_run and readme_run != ops_run:
        add_error(errors, "README.md e docs/OPERATIONS.md divergem no comando principal de execucao")

    readme_entrypoints = [normalize_block(item) for item in extract_readme_entrypoints(readme_text)]
    readme_entrypoints = [item for item in readme_entrypoints if item]
    if readme_entrypoints and ops_run and ops_run not in readme_entrypoints:
        add_error(errors, "README.md nao lista o boot principal operacional entre os entrypoints")

    agents_validation = extract_agents_validation(agents_text)
    ops_validation = normalize_block(
        extract_first_code_block(extract_section(operations_text, "## 5. Validacao minima"))
    )
    if agents_validation and ops_validation and normalize_block(agents_validation) != ops_validation:
        add_error(errors, "AGENTS.md e docs/OPERATIONS.md divergem na validacao minima")

    negative_scope_readme = " ".join(
        extract_bullets(extract_section(readme_text, "## O que este repositorio NAO e"))
    )
    negative_scope_gate = " ".join(
        extract_bullets(
            extract_section(gate_text, "## 4. O que este projeto NAO pode carregar?")
        )
    )
    comparison_reports: list[dict[str, object]] = []
    if negative_scope_readme and negative_scope_gate:
        negative_comparison = compare_token_sets(
            negative_scope_readme,
            negative_scope_gate,
            alias_groups,
        )
        comparison_reports.append(
            {
                "code": "scope_negative_mismatch",
                "matched_alias_indexes": list(negative_comparison["matched_alias_indexes"]),
            }
        )
        if not negative_comparison["shared_tokens"] and not negative_comparison["matched_alias_indexes"]:
            add_warning(
                warnings,
                "scope_negative_mismatch",
                "README.md e PROJECT_GATE.md parecem desconectados na definicao de fora de escopo",
            )

    positive_scope_readme = " ".join(
        extract_bullets(extract_section(readme_text, "## O que este repositorio e"))
    )
    positive_scope_gate = " ".join(
        extract_bullets(extract_section(gate_text, "## 1. Por que este projeto existe?"))
    )
    if positive_scope_readme and positive_scope_gate:
        positive_comparison = compare_token_sets(
            positive_scope_readme,
            positive_scope_gate,
            alias_groups,
        )
        comparison_reports.append(
            {
                "code": "objective_mismatch",
                "matched_alias_indexes": list(positive_comparison["matched_alias_indexes"]),
            }
        )
        if not positive_comparison["shared_tokens"] and not positive_comparison["matched_alias_indexes"]:
            add_warning(
                warnings,
                "objective_mismatch",
                "README.md e PROJECT_GATE.md parecem desconectados na definicao do objetivo do repositorio",
            )

    architecture_scope = " ".join(
        extract_bullets(extract_section(architecture_text, "## 2. Escopo"))
    )
    if architecture_scope and negative_scope_readme:
        architecture_comparison = compare_token_sets(
            architecture_scope,
            negative_scope_readme,
            alias_groups,
        )
        comparison_reports.append(
            {
                "code": "scope_architecture_mismatch",
                "matched_alias_indexes": list(architecture_comparison["matched_alias_indexes"]),
            }
        )
        if not architecture_comparison["shared_tokens"] and not architecture_comparison["matched_alias_indexes"]:
            add_warning(
                warnings,
                "scope_architecture_mismatch",
                "README.md e docs/ARCHITECTURE.md usam vocabularios muito diferentes para o escopo",
            )

    contracts_inputs = extract_section(contracts_text, "## 2. Entradas canonicas") or ""
    contracts_outputs = extract_section(contracts_text, "## 3. Saidas canonicas") or ""
    if contracts_inputs.count("|") < 10:
        add_error(errors, "docs/CONTRACTS.md parece nao ter entradas canonicas suficientes")
    if contracts_outputs.count("|") < 8:
        add_error(errors, "docs/CONTRACTS.md parece nao ter saidas canonicas suficientes")

    active_warnings = [
        item for item in warnings if item.get("code") not in ignored_warning_codes
    ]

    if errors:
        print("Project doctor encontrou erros:", file=sys.stderr)
        for message in errors:
            print(f"- {message}", file=sys.stderr)
        if active_warnings:
            print("", file=sys.stderr)
            print_warning_list("Warnings:", active_warnings, sys.stderr)
        return 1

    if args.audit_config:
        return run_config_audit(doctor_config, warnings, comparison_reports)

    if args.strict and active_warnings:
        print("Project doctor encontrou warnings em modo strict:", file=sys.stderr)
        for warning in active_warnings:
            print(f"- [{warning['code']}] {warning['message']}", file=sys.stderr)
        return 1

    if active_warnings:
        print("Project doctor passou com warnings:")
        for warning in active_warnings:
            print(f"- [{warning['code']}] {warning['message']}")
        return 0

    print("Project doctor passou.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
