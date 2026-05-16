# DECISIONS

Use este arquivo para registrar decisões arquiteturais de forma leve. O objetivo não é burocracia; é evitar que o repositório mude de forma silenciosa.

## 2026-05-16 - Criar Hlidskjalf como repositório de prática ativa

**Contexto**

O trabalho de banco de questões começou por engano em outro repositório. O domínio correto é um sistema de estudo, com uma questão completa por página, correção ativa e repetição espaçada.

**Decisão**

Criar `Hlidskjalf` como repositório próprio a partir do bootstrap do `Skidbladnir`, usando Node.js 20+ para a aplicação local e SQLite para bancos públicos de questões e progresso local.

**Impacto**

- o repositório passa a ter fronteira própria e não depende de sistemas operacionais de outros domínios
- o piloto pode começar por Língua Portuguesa antes de expandir para outras disciplinas
- bancos públicos e privados devem ser tratados separadamente desde a origem

**Tradeoff**

- criar um repositório novo tem custo de manutenção, mas evita acoplar UX de estudo e agenda de revisão a projetos que não têm esse domínio
- escolher Node.js favorece uma interface local web simples, mas scripts de extração existentes em Python precisarão ser portados ou mantidos como ferramentas auxiliares conscientes

**Alternativas rejeitadas**

- continuar no repositório errado e tentar separar por pasta
- transformar tudo em baralhos Anki simples antes de validar a resolução ativa

## 2026-05-16 - Separar bancos públicos e privados

**Contexto**

Questões e gabaritos de prova são públicos, mas comentários de obra comentada podem ter direito autoral.

**Decisão**

Versionar apenas bancos públicos em `data/questions/` e manter comentários autorais, PDFs, extrações privadas e progresso de usuário em `runtime/`.

**Impacto**

- a aplicação deve funcionar sem banco privado de comentários
- o schema precisa usar identificadores estáveis para permitir enriquecimento local opcional
- validações devem confirmar que `runtime/` não entra no git

**Tradeoff**

- a separação aumenta a complexidade de importação, mas reduz risco jurídico e mantém o núcleo de estudo reproduzível

**Alternativas rejeitadas**

- versionar banco único com questões e comentários
- não persistir comentários privados, perdendo a possibilidade de uso local legítimo

## 2026-05-16 - Importar TPS Comentado 2019 como primeiro banco público

**Contexto**

O extrator e os bancos foram produzidos inicialmente no repositório errado. O trabalho útil precisava ser migrado para `Hlidskjalf`, mantendo público e privado separados.

**Decisão**

Importar `scripts/build_tps_question_db.py` e versionar `data/questions/tps-comentado-2019-public.db`. Manter Markdown intermediário, textos extraídos e banco de comentários em `runtime/books/`.

**Impacto**

- o piloto pode começar por `chapter_number = 1`, Língua Portuguesa
- a aplicação passa a ter um banco público real para leitura
- a extração continua reproduzível localmente enquanto os insumos privados permanecerem em `runtime/books/`

**Tradeoff**

- o banco SQLite versionado aumenta o tamanho do repositório, mas elimina dependência de extração no fluxo normal de uso
- o extrator ainda depende de Markdown local privado para rebuild completo, o que é aceitável enquanto o banco público for o contrato versionado

**Alternativas rejeitadas**

- importar apenas o script e exigir rebuild local para todos os usuários
- versionar também o banco de comentários para simplificar a interface
