# Contratos

## 1. Objetivo

Registrar as entradas, saídas, identificadores e invariantes que permitem ao `Hlidskjalf` praticar questões completas sem depender de material autoral privado.

## 2. Entradas canônicas

| Nome | Origem | Formato | Obrigatório | Observações |
| --- | --- | --- | --- | --- |
| `public_question_db` | `data/questions/tps-comentado-2019-public.db` | SQLite | sim | Banco público versionável com 631 grupos e 2586 itens/alternativas. |
| `settings` | `config/settings.example.json` ou `config/settings.local.json` | JSON | sim | Define paths de banco público e progresso local. |
| `private_comment_db` | `runtime/books/*.db` ou outro path local | SQLite | não | Banco privado opcional; não pode ser requisito para corrigir questões. |

## 3. Saídas canônicas

| Nome | Destino | Formato | Garantias |
| --- | --- | --- | --- |
| `progress_db` | `runtime/question-practice/progress.db` | SQLite | Guarda tentativas, resultado e agenda local; não deve ser versionado. |
| `structured_logs` | stdout e futuro `runtime/logs/` | JSONL | Eventos parseáveis com `ts`, `lvl`, `svc`, `mod`, `evt` e `msg`. |

## 4. Schema público esperado

O banco público inicial deve expor pelo menos:

- `question_groups`
  - `id`
  - `source_name`
  - `source_file`
  - `chapter_number`
  - `chapter_title`
  - `ordinal`
  - `start_line`
  - `end_line`
  - `exam_name`
  - `exam_year`
  - `board`
  - `header_raw`
  - `support_text`
  - `prompt`
  - `question_type`
  - `answer_key_raw`
  - `confidence`
  - `needs_review`
  - `review_notes`
- `question_items`
  - `id`
  - `group_id`
  - `item_label`
  - `item_order`
  - `item_text`
  - `answer_normalized`
  - `is_annulled`
  - `confidence`

Estado validado em 2026-05-16:

- `question_groups`: 631 registros
- `question_items`: 2586 registros
- `question_items.answer_normalized IS NULL`: 0 registros
- `question_groups.needs_review`: 0 registros marcados
- grupos de Língua Portuguesa: 126 registros

## 5. Identificadores e chaves

| Conceito | Campo canônico | Observações |
| --- | --- | --- |
| Grupo de questão | `question_groups.id` | Identificador estável usado para tela, tentativa e agenda. |
| Item ou alternativa | `question_items.id` | Identificador estável para resposta marcada e correção. |
| Disciplina | `question_groups.chapter_number` e `question_groups.chapter_title` | O piloto começa por `chapter_number = 1`, Língua Portuguesa. |
| Gabarito | `question_items.answer_normalized` | Valores esperados: `correct`, `wrong`, `annulled` ou alternativas convertidas para acerto/erro em múltipla escolha. |

## 6. Banco de progresso

O schema local é criado de forma idempotente em `runtime/question-practice/progress.db` e representa:

- `attempts`: tentativa por grupo de questão, data, resultado agregado e classificação do usuário
- `attempt_answers`: resposta marcada por item ou alternativa
- `review_cards`: estado de repetição por grupo de questão, próxima revisão, intervalo e fator de facilidade
- `schema_migrations`: controle de migrações idempotentes

## 7. Eventos ou etapas de pipeline

| Etapa | Entrada | Saída | Falhas esperadas |
| --- | --- | --- | --- |
| `load_question` | banco público e filtro de disciplina | grupo completo para renderização | banco ausente, schema incompatível, questão sem itens |
| `submit_attempt` | respostas do usuário | tentativa persistida e resultado calculado | resposta incompleta, item desconhecido, gabarito ausente |
| `schedule_review` | resultado e dificuldade percebida | próxima data de revisão | dificuldade inválida, banco de progresso indisponível |

## 8. Assunções ainda não validadas

- o banco público importado preserva todos os textos-base necessários para Língua Portuguesa
- o schema atual de `question_groups` e `question_items` será suficiente para evoluir o piloto sem migração pública
- uma agenda por grupo de questão é melhor para o usuário do que uma agenda por item isolado

## 9. Quebras de contrato

Registre aqui mudanças que exigem:

- migração de dados
- ajuste de integração
- restart operacional
- versão nova de cliente

Formato:

- `YYYY-MM-DD`: descrição da quebra de contrato
