# Start Checklist

Use este checklist antes do primeiro push e antes de importar os bancos de questões.

## 0. Decisão De Existência

- [x] O projeto tem fronteira própria: prática ativa de questões com repetição espaçada.
- [x] O projeto não deve nascer dentro de `Skidbladnir`, que é apenas o scaffolder.
- [x] O limite de escopo está claro no `README.md` e no `PROJECT_GATE.md`.
- [x] Conteúdo público e conteúdo autoral foram separados desde o bootstrap.

## 1. Baseline Mínima

- [x] `README.md` criado e preenchido.
- [x] `AGENTS.md` criado e ajustado para o domínio.
- [x] `PROJECT_GATE.md` preenchido.
- [x] `CHANGELOG.md` criado.
- [x] `docs/ARCHITECTURE.md` criado.
- [x] `docs/CONTRACTS.md` criado.
- [x] `docs/OPERATIONS.md` criado.
- [x] `docs/DECISIONS.md` criado.

## 2. Estrutura

- [x] Raiz enxuta e intencional.
- [x] Camadas `domain / application / infrastructure / interfaces` visíveis em `hlidskjalf/`.
- [x] `tests/` criado com smoke test inicial.
- [x] `config/` criado com exemplos versionados.
- [x] `runtime/` definido e ignorado no git.
- [ ] `data/questions/` ainda precisa receber o banco público versionável.

## 3. Configuração E Runtime

- [x] Segredos não entram no git.
- [x] Existe `config/settings.example.json`.
- [x] Runtime state, bancos privados e sessões estão fora do versionamento.
- [x] Caminho de logs previsto em `docs/OPERATIONS.md`.
- [x] Entrypoint principal documentado como `npm start`.
- [ ] Interface HTTP local ainda não foi implementada.

## 4. Contratos

- [x] Entrada canônica definida como SQLite público de questões.
- [x] Saída canônica definida como SQLite local de progresso.
- [x] Identificadores principais definidos.
- [x] Inferências e assunções marcadas.
- [x] Limites com bancos privados e comentários autorais documentados.
- [ ] Schema local de progresso ainda precisa ser materializado.

## 5. Validação

- [x] `python3 scripts/check_project_gate.py` passa.
- [x] `python3 scripts/project_doctor.py` passa.
- [x] `python3 scripts/project_doctor.py --audit-config` passa.
- [x] `npm test` passa.
- [x] Checagem sintática dos scripts Python passa.
- [x] Comportamento de restart documentado.
- [x] Critério de smoke test definido.

## 6. Disciplina De Crescimento

- [x] Regra de branch definida.
- [x] Regra de commit definida.
- [x] Idioma da documentação definido.
- [x] Política de logs definida.
- [x] Política de update de docs definida.
- [ ] `bash scripts/install_git_hooks.sh` deve ser executado depois de `git init`.

## 7. Próxima Rodada

- [ ] Importar para este repositório apenas o banco público de questões e gabaritos.
- [ ] Manter banco privado de comentários fora do git.
- [ ] Implementar piloto de Língua Portuguesa com uma questão completa por página.
- [ ] Criar schema e migrations do banco local de progresso.
- [ ] Implementar correção por item e classificação `difícil / boa / fácil`.
