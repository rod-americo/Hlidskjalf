# Hlidskjalf

![Node](https://img.shields.io/badge/node-20%2B-5fa04e) ![License](https://img.shields.io/badge/license-MIT-blue)

`Hlidskjalf` é uma plataforma local de estudo de alta performance para candidatos ao CACD. O foco inicial é prática ativa de questões: uma questão completa por página, com texto-base quando existir, itens ou alternativas, correção imediata e repetição espaçada baseada no desempenho.

Inspirado na mitologia nórdica, Hlidskjalf (nórdico antigo: `Hliðskjálf`, pronunciado `/ˈhliːðˌskjɑːlv/`) é o alto assento de Odin, um ponto de observação a partir do qual todos os mundos podem ser vistos. No projeto, o nome representa clareza, perspectiva estratégica e capacidade de sintetizar informação complexa.

## Por Que Este Projeto Existe

- questões de provas como CACD/TPS frequentemente dependem de textos longos e grupos de itens, o que não se encaixa bem em flashcards simples
- o estudante precisa resolver ativamente cada item ou alternativa antes de ver a correção
- a agenda de revisão deve ser baseada no desempenho e na dificuldade percebida, sem depender de serviço externo

## O que este repositorio e

- uma aplicação local Node.js para treino de questões
- um lugar para versionar schema, aplicação e bancos públicos de questões e gabaritos
- o dono do fluxo de estudo: selecionar questão vencida, registrar resposta, corrigir, classificar dificuldade e reagendar

## O que este repositorio NAO e

- um repositório de OCR ou extração editorial de livros
- um lugar para versionar comentários autorais, PDFs ou bancos privados derivados de material protegido
- um LMS completo, rede social, marketplace de questões ou substituto integral do Anki
- um sistema dependente de internet ou autenticação na primeira versão

## Estado Atual

- fase: `bootstrap estrutural`
- runtime principal: `node20+`
- entrypoints principais:
  - `npm start`
  - `npm test`
  - `python3 scripts/check_project_gate.py`
  - `python3 scripts/project_doctor.py`
- dependência externa crítica:
  - bancos SQLite públicos de questões em `data/questions/*.db`, ainda a serem importados para este repositório

## Baseline Arquitetural

```text
Hlidskjalf/
├── README.md
├── AGENTS.md
├── PROJECT_GATE.md
├── CHANGELOG.md
├── START_CHECKLIST.md
├── package.json
├── config/
│   ├── doctor.json
│   ├── settings.example.json
│   └── logging.example.json
├── data/
│   └── questions/              # bancos públicos versionáveis, quando importados
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CONTRACTS.md
│   ├── OPERATIONS.md
│   └── DECISIONS.md
├── hlidskjalf/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── interfaces/
│   └── main.mjs
├── tests/
├── scripts/
└── runtime/                    # ignorado no git
```

Regras:

- preservar a separação `domain / application / infrastructure / interfaces`
- manter a raiz enxuta e intencional
- usar `data/questions/` apenas para conteúdo público versionável
- usar `runtime/` para progresso local, bancos privados, comentários autorais, logs e estado mutável
- não acoplar a aplicação a comentários autorais; eles podem enriquecer uso local, mas não são requisito para o treino funcionar

## Quick Start

### 1. Preparar ambiente

```bash
npm install
```

### 2. Rodar validacao

```bash
npm test
python3 scripts/check_project_gate.py
python3 scripts/project_doctor.py
```

### 3. Configurar

```bash
cp config/settings.example.json config/settings.local.json
```

### 4. Rodar

```bash
npm start
```

No bootstrap atual, `npm start` apenas valida o entrypoint e emite log estruturado. A interface real de prática será implementada na próxima rodada.

## Configuração

Princípios:

- segredos e configuração host-local não entram no git
- exemplos versionados ficam em `config/*.example.json`
- bancos públicos de questões podem ser versionados em `data/questions/`
- progresso, comentários autorais e bancos privados ficam em `runtime/`

Tabela mínima:

| Entrada | Tipo | Obrigatório | Origem | Exemplo |
| --- | --- | --- | --- | --- |
| `HLIDSKJALF_CONFIG_FILE` | `env` | não | host | `config/settings.local.json` |
| `NODE_ENV` | `env` | não | host | `development` |
| `publicQuestionDbPath` | arquivo | sim | config | `data/questions/tps-comentado-2019-public.db` |
| `progressDbPath` | arquivo | sim | config | `runtime/question-practice/progress.db` |

## Contratos E Fronteiras

Entrada canônica inicial:

- banco SQLite público com grupos de questão, itens/alternativas e gabaritos normalizados

Saída canônica inicial:

- banco SQLite local de progresso com tentativas, classificações de dificuldade e próxima data de revisão

O banco público não deve conter comentários autorais. Quando existir banco privado de comentários em `runtime/`, ele deve usar os mesmos identificadores estáveis, mas continuar opcional e não versionado.

## Validação

Checklist mínimo:

- `npm test`
- `python3 scripts/check_project_gate.py`
- `python3 scripts/project_doctor.py`
- `python3 scripts/project_doctor.py --audit-config`
- `python3 -m py_compile scripts/check_project_gate.py scripts/project_doctor.py`

## Documentação Do Repositório

- `PROJECT_GATE.md`: justificativa de existência e fronteira do repositório
- `docs/ARCHITECTURE.md`: arquitetura real e evolução prevista
- `docs/CONTRACTS.md`: contratos de bancos, identificadores e invariantes
- `docs/OPERATIONS.md`: execução local, runtime, backup e troubleshooting
- `docs/DECISIONS.md`: decisões arquiteturais e tradeoffs
- `START_CHECKLIST.md`: estado do bootstrap e pendências reais

## Riscos E Limites Atuais

- risco principal: importar questões sem preservar textos-base e agrupamento correto
- dependência mais frágil: qualidade do parser e do banco público de questões
- maior dívida técnica conhecida: a interface de prática e a política de repetição espaçada ainda não foram implementadas

## Evolução Do Projeto

### Consolidado

- [x] baseline Skidbladnir aplicada ao repositório remoto existente
- [x] fronteira do projeto documentada
- [x] guardrails locais criados

### Em andamento

- [ ] importar banco público de questões para `data/questions/`
- [ ] criar banco local de progresso em `runtime/`
- [ ] implementar piloto de Língua Portuguesa com uma questão completa por página

### Planejado

- [ ] adicionar correção por item e classificação pós-correção
- [ ] implementar agenda de repetição espaçada
- [ ] expandir para demais disciplinas depois de validar o fluxo de Língua Portuguesa
