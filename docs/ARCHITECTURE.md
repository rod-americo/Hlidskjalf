# ARCHITECTURE

## 1. Objetivo

O `Hlidskjalf` é uma aplicação local para prática ativa de questões. Ele deve mostrar uma questão completa por vez, incluindo texto-base quando existir, registrar respostas do usuário, corrigir por item ou alternativa e reagendar a próxima revisão conforme desempenho e dificuldade percebida.

## 2. Escopo

Inclui:

- leitura de bancos SQLite públicos com grupos de questão, itens, alternativas e gabaritos
- interface local para resolver uma questão completa por página
- persistência de tentativas, resultado e agenda de repetição espaçada em banco local ignorado pelo git
- importação controlada de bancos públicos versionáveis em `data/questions/`

Não inclui:

- OCR de PDFs ou extração editorial como responsabilidade principal da aplicação
- versionamento de comentários autorais, PDFs de livros ou bancos privados
- sincronização entre dispositivos, autenticação, ranking, LMS ou marketplace
- curadoria jurídica de direitos autorais

## 3. Contexto Do Sistema

Entradas externas:

- banco público de questões em SQLite, inicialmente `data/questions/tps-comentado-2019-public.db`
- configuração local opcional em `config/settings.local.json`

Saídas externas:

- banco local de progresso em `runtime/question-practice/progress.db`
- logs estruturados em stdout e, futuramente, em `runtime/logs/`

Dependências críticas:

- Node.js 20+
- SQLite legível pela aplicação
- qualidade estrutural do banco público importado

## 4. Módulos Principais

### 4.1 Domain

Entidades e regras centrais:

- `question_group`: cabeçalho, texto-base, comando e conjunto de itens/alternativas
- `question_item`: item certo/errado ou alternativa marcada
- `answer_key`: gabarito normalizado por item
- `attempt`: respostas do usuário e resultado da correção
- `review_schedule`: próxima data de revisão, intervalo, facilidade e estado de aprendizagem

### 4.2 Application

Casos de uso previstos:

- selecionar próxima questão vencida ou nunca respondida
- montar a página completa da questão
- registrar respostas do usuário
- corrigir respostas contra gabarito público
- receber classificação pós-correção
- atualizar agenda de repetição espaçada

### 4.3 Infrastructure

Responsabilidades:

- abrir banco público de questões em modo leitura
- reconstruir o banco público com `scripts/build_tps_question_db.py` quando houver atualização controlada dos Markdown locais em `runtime/books/`
- criar e migrar banco local de progresso em `runtime/`
- carregar configuração
- emitir logs estruturados
- servir arquivos estáticos ou endpoints locais quando a interface HTTP nascer

### 4.4 Interfaces

Interfaces previstas:

- servidor HTTP local para piloto web
- CLI mínima para smoke, inspeção e eventual reset controlado de progresso
- exportação futura para Anki ou formato intermediário, se fizer sentido depois do piloto

## 5. Fluxo principal

1. A aplicação carrega configuração e abre o banco público de questões.
2. A aplicação cria ou abre o banco local de progresso.
3. O caso de uso seleciona a próxima questão de Língua Portuguesa vencida ou nunca respondida.
4. A interface renderiza texto-base, comando e todos os itens/alternativas do grupo.
5. O usuário marca respostas e aciona a correção.
6. A aplicação compara respostas com o gabarito normalizado, preservando itens anulados como anulados.
7. A interface mostra acertos, erros e gabarito por item.
8. O usuário classifica a questão como difícil, boa ou fácil.
9. A aplicação persiste tentativa e agenda a próxima revisão.

## 6. Contratos E Invariantes

- entrada canônica: `question_groups` e `question_items` no banco público
- saída canônica: `attempts` e `review_cards` no banco local de progresso
- identificador primário: `question_groups.id` para grupos e `question_items.id` para itens
- invariantes:
  - uma tela de prática corresponde a um `question_group`
  - texto-base pertence ao grupo, não a um item isolado
  - toda correção usa apenas gabarito público normalizado
  - comentário autoral nunca é necessário para corrigir questão
  - progresso local nunca deve ser versionado

## 7. Persistência

- armazenamento público: SQLite versionável em `data/questions/`
- armazenamento local: SQLite em `runtime/question-practice/`
- estratégia de backup: copiar o banco de progresso local quando o usuário quiser preservar histórico
- política de migração: migrations idempotentes no bootstrap da aplicação antes de acessar progresso

## 8. Configuração

- fonte de configuração: arquivo JSON local ou env `HLIDSKJALF_CONFIG_FILE`
- arquivo versionado de exemplo: `config/settings.example.json`
- configuração host-local ignorada: `config/settings.local.json`
- paths padrão devem funcionar sem configuração extra depois que o banco público existir

## 9. Observabilidade

- logger central: `hlidskjalf/infrastructure/logger.mjs`
- formato de logs: JSON em linha única
- métricas mínimas futuras: questão carregada, tentativa registrada, correção executada, erro de banco e latência de resposta
- smoke test atual: `npm test`

## 10. Riscos E Tradeoffs

- risco técnico principal: banco público incompleto ou mal agrupado gerar tela de questão incompleta
- acoplamento consciente: o piloto pode começar acoplado ao schema SQLite atual para acelerar aprendizado do domínio
- parte ainda experimental: algoritmo de repetição espaçada e UX de correção por item

## 11. Decisões Abertas

- escolher algoritmo inicial de repetição espaçada entre intervalos simples e variação inspirada em SM-2
- definir se comentários privados serão exibidos localmente no futuro ou permanecerão fora da interface
- definir formato de exportação para Anki depois do fluxo ativo estar validado
