# AGENTS.md

Este arquivo define regras de colaboração para agentes e autores neste repositório. Ele vale para a raiz inteira, salvo quando um subdiretório tiver um `AGENTS.md` mais específico.

## 1. Ordem mínima de leitura

Antes de fazer mudanças significativas, leia nesta ordem:

1. `README.md`
2. `PROJECT_GATE.md`
3. `docs/ARCHITECTURE.md`
4. `docs/CONTRACTS.md`
5. `docs/OPERATIONS.md`
6. `docs/DECISIONS.md`
7. `START_CHECKLIST.md`

Se a tarefa tocar bancos de questões, importação de material ou repetição espaçada, leia também o schema real do SQLite envolvido antes de editar código.

## 2. Política de idioma

- documentação para humanos: `pt-BR`
- identificadores técnicos: `en-US`
- mensagens de commit: `en-US`
- parágrafos em Markdown ficam em linha única; não aplicar hard-wrap manual em 80 colunas

Inclui:

- `README.md`, `docs/`, runbooks, notas operacionais e changelog
- nomes de módulos, funções, classes, arquivos e variáveis novas
- assuntos de commit no formato `type(scope): summary`

Exceção:

- preserve contratos externos, nomes de campos, env vars e schemas impostos por terceiros
- quando algo for inferido ou adaptado, documente isso explicitamente

## 3. Limite de escopo

Ao iniciar qualquer tarefa, responda primeiro:

- isto pertence ao `Hlidskjalf`?
- isto é prática ativa de questões ou virou OCR/curadoria editorial?
- isto depende de conteúdo público versionável ou de material autoral local?
- isto altera domínio, aplicação, infraestrutura ou interface?

Este repositório existe para:

- praticar questões completas, preservando texto-base, grupo, itens, alternativas e gabarito
- manter bancos públicos de questões e gabaritos em `data/questions/`
- manter progresso local, agenda de revisão e dados privados em `runtime/`
- evoluir uma experiência tipo Anki de questões, com resolução ativa e repetição espaçada

Este repositório não deve:

- versionar PDFs de livros, comentários autorais ou bancos privados derivados de material protegido
- virar laboratório genérico de OCR, NLP, benchmark LLM ou scraping
- depender de comentários autorais para corrigir questão pública
- crescer como LMS completo antes do piloto de questões estar sólido

## 4. Baseline de arquitetura

Prefira a separação já criada:

- `hlidskjalf/domain/`: regras centrais, entidades de questão, tentativa, agenda e repetição espaçada
- `hlidskjalf/application/`: casos de uso como selecionar próxima questão, registrar respostas, corrigir e reagendar
- `hlidskjalf/infrastructure/`: SQLite, filesystem, config, logger e adapters de banco
- `hlidskjalf/interfaces/`: servidor HTTP, CLI ou interface local

Regras:

- não colocar código de produção solto na raiz
- manter `data/questions/` para bancos públicos versionáveis
- manter `runtime/` para progresso local, comentários autorais, caches e logs
- não acoplar interface diretamente ao SQLite quando houver caso de uso na camada de aplicação
- não criar abstrações antes de o piloto de Língua Portuguesa revelar a forma real do fluxo

## 5. Configuração, runtime e logs

- não versionar segredos, sessões, dumps privados, comentários autorais, progresso local ou runtime state
- sempre versionar exemplos de configuração em `config/*.example.json`
- centralizar defaults e parsing em `hlidskjalf/infrastructure/config.mjs`
- logs operacionais devem ser estruturados e parseáveis
- formato preferencial: JSON em uma linha
- campos mínimos recomendados: `ts`, `lvl`, `svc`, `mod`, `evt`, `msg`

## 6. Política de commit e branch

Workflow padrão para repositório solo:

- trabalhar diretamente em `main`
- não criar branches auxiliares sem necessidade explícita
- manter um commit por mudança lógica
- revisar diff, validação e impacto operacional antes de push

Mensagem de commit:

- idioma: `en-US`
- modo imperativo
- formato preferencial: `type(scope): summary`
- limite recomendado: 72 caracteres no assunto

## 7. Validação obrigatória

Antes de concluir:

- executar `npm test` quando código Node mudar
- executar `python3 scripts/build_tps_question_db.py` quando o extrator, banco público ou material local de origem mudar
- executar `python3 scripts/check_project_gate.py` quando `PROJECT_GATE.md` mudar
- executar `python3 scripts/project_doctor.py` quando README/docs/contratos/operação mudarem
- executar `python3 scripts/project_doctor.py --audit-config` quando `config/doctor.json` mudar
- executar `python3 -m py_compile scripts/check_project_gate.py scripts/project_doctor.py scripts/build_tps_question_db.py` quando scripts Python mudarem
- revisar `git diff` e `git status`
- confirmar que `runtime/` não está sendo versionado

Se a mudança afetar execução local:

- declarar se exige restart do processo Node
- atualizar `docs/OPERATIONS.md` no mesmo diff

## 8. Documentação obrigatória

Atualize junto com o código quando necessário:

- `README.md`: objetivo, escopo, quick start, entrypoints, estado atual
- `PROJECT_GATE.md`: fronteira e custo de manutenção do repositório
- `docs/ARCHITECTURE.md`: módulos, fluxo principal, persistência e riscos
- `docs/CONTRACTS.md`: schema consumido, identificadores, invariantes e saídas
- `docs/OPERATIONS.md`: execução, paths, backup, restart e troubleshooting
- `docs/DECISIONS.md`: decisões sobre banco, UX, repetição espaçada e separação público/privado
- `START_CHECKLIST.md`: estado real do projeto e pendências

## 9. Regras de segurança técnica

- não inferir gabarito quando o banco público não trouxer resposta normalizada
- não misturar comentários autorais com banco público versionado
- não apagar progresso local sem comando explícito do usuário
- não assumir que duas questões são equivalentes apenas por ano/banca; use identificadores estáveis do banco
- não transformar texto-base em item separado quando ele pertence ao grupo de questão

## 10. Fragilidades clássicas a evitar

- quebrar uma questão com texto-base em cartões isolados sem contexto
- corrigir múltipla escolha como se fosse certo/errado
- tratar item anulado como erro do usuário
- agendar repetição antes de persistir a tentativa
- versionar banco de comentários ou material protegido por engano

## 11. Extensões específicas do repositório

- domínio crítico: `pratica ativa de questoes com repeticao espacada`
- dependência externa crítica: `SQLite publico de questoes e gabaritos`
- dados sensíveis: `progresso local do usuario, comentarios autorais e configuracao host-local`
- host principal: `execucao local no computador do usuario`
- comando de validação mínima: `npm test && python3 scripts/build_tps_question_db.py && python3 scripts/check_project_gate.py && python3 scripts/project_doctor.py`
- regra de restart: `mudancas em codigo Node exigem restart do processo local; docs isoladas nao exigem restart`
- gate check local: `python3 scripts/check_project_gate.py`
- doctor estrutural: `python3 scripts/project_doctor.py`
- doctor estrito: `python3 scripts/project_doctor.py --strict`
- doctor audit: `python3 scripts/project_doctor.py --audit-config`
- install hooks: `bash scripts/install_git_hooks.sh`
- policy do doctor: `config/doctor.json`
