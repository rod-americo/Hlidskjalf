# PROJECT GATE

Este arquivo justifica por que o `Hlidskjalf` merece existir como repositório próprio e define a fronteira mínima para não virar um depósito genérico de estudo, OCR ou automações educacionais.

## 1. Por que este projeto existe?

- problema real: estudar questões longas em formato ativo exige preservar grupos de questão, textos-base, itens, alternativas, gabaritos e histórico de revisão; usar apenas cartões simples perde contexto e não mede a execução real da questão.
- usuario ou operador alvo: estudante que treina provas discursivas e objetivas, começando pelo CACD/TPS, e precisa de fluxo local auditável para resolver, corrigir e reagendar questões.
- resultado esperado: entregar um sistema local de prática de questões com uma questão completa por tela, correção imediata, classificação de dificuldade e agenda de repetição espaçada baseada no desempenho.

## 2. Por que isto NÃO deveria ser um módulo?

- repositorio candidato que poderia absorver isso: `Skidbladnir` poderia gerar a estrutura, mas não deve carregar o produto de estudo; outros repositórios operacionais não têm relação de domínio com treino de questões.
- por que esse acoplamento seria inadequado: o ciclo de evolução envolve UX de estudo, dados públicos de provas, SQLite local, estado de progresso e eventualmente exportação para Anki, o que tem dependências e decisões próprias.
- fronteira que justifica um repositório separado: `Hlidskjalf` é dono do modelo de prática ativa, do agendamento de revisão e da interface de estudo; fontes de questões e extratores são insumos, não o domínio central.

## 3. O que este projeto compartilha com o ecossistema?

- configuracao: usa exemplos versionados em `config/*.example.json` e configuração host-local ignorada por git quando necessário.
- logging: usa eventos JSON em linha única para bootstrap, diagnósticos e futuras rotinas de importação.
- runtime: usa Node.js 20+ para a aplicação local e SQLite como persistência dos bancos de questões e de progresso.
- contratos: consome bancos públicos de questões em `data/questions/*.db` e mantém estado local de revisão em `runtime/`.
- autenticacao ou transporte: a primeira versão não exige autenticação nem transporte externo; qualquer sincronização futura deve ser tratada como contrato novo.

Se a resposta for "quase tudo", provavelmente isso ainda não deveria nascer como repositório.

## 4. O que este projeto NÃO pode carregar?

- responsabilidades fora de escopo: OCR de livros, curadoria jurídica de direitos autorais, geração automática irrestrita de conteúdo, LMS completo, rede social de estudos ou marketplace de questões.
- integrações que pertencem a outro sistema: importadores específicos de PDF podem nascer como scripts auxiliares, mas a aplicação principal não deve depender de um livro privado nem de comentários autorais para funcionar.
- dados que nao devem morar aqui: comentários protegidos por direito autoral, PDFs de livros, bancos privados de anotações, segredos, sessões de usuário, dumps e progresso local de estudo.

## 5. Qual É O Custo De Manutenção Esperado?

- host ou ambiente principal: execução local no computador do usuário, com possibilidade futura de empacotamento ou deploy local simples.
- dependencia externa mais fragil: qualidade estrutural do banco de questões importado, especialmente textos-base e agrupamento correto de itens.
- necessidade de restart: mudanças em código Node exigem reinício do processo local; mudanças em dados públicos exigem recarregar a aplicação ou reiniciar o servidor local; docs isoladas não exigem restart.
- necessidade de backup: o banco de progresso em `runtime/` deve ser copiável pelo usuário, porque contém histórico e agenda de revisão; o banco público pode ser reconstruído.
- risco operacional: corromper ou perder agenda de revisão prejudica o estudo, mas não afeta sistemas externos; o risco principal é mostrar questão incompleta ou corrigir item com gabarito mal normalizado.

## 6. Condição de saída

Este repositório só deveria existir se:

- houver fronteira de escopo defensável
- houver contrato de entrada e saída identificável
- houver operação própria ou ciclo de evolução independente
- o custo de mais um repo for menor que o custo de acoplamento
