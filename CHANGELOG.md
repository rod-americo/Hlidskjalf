# CHANGELOG

Este arquivo registra mudanças relevantes de comportamento, arquitetura e operação.

## [Unreleased]

### Added

- baseline Skidbladnir para aplicação Node.js local
- `PROJECT_GATE.md` com fronteira para prática ativa de questões e repetição espaçada
- documentação estrutural em `README.md`, `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/CONTRACTS.md`, `docs/OPERATIONS.md` e `docs/DECISIONS.md`
- guardrails locais com `scripts/check_project_gate.py`, `scripts/project_doctor.py`, `config/doctor.json` e `.githooks/pre-commit`
- smoke test inicial em `tests/smoke.test.mjs`

### Changed

- nenhum comportamento de aplicação real ainda; o entrypoint atual apenas valida bootstrap e logging estruturado

### Operational Notes

- não há restart produtivo porque não existe processo de produção
- `runtime/` permanece ignorado e reservado para progresso local, comentários autorais, logs e bancos privados
- bancos públicos de questões devem entrar futuramente em `data/questions/`
