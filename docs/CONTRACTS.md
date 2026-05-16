# CONTRACTS

## 1. Objetivo

Registrar as entradas, saídas, identificadores e invariantes que permitem ao `Hlidskjalf` praticar questões completas sem depender de material autoral privado.

## 2. Entradas canonicas

| Nome | Origem | Formato | Obrigatório | Observações |
| --- | --- | --- | --- | --- |
| `public_question_db` | `data/questions/*.db` | SQLite | sim | Banco público versionável com grupos de questão, itens/alternativas e gabaritos normalizados. |
| `settings` | `config/settings.example.json` ou `config/settings.local.json` | JSON | sim | Define paths de banco público e progresso local. |
| `private_comment_db` | `runtime/books/*.db` ou outro path local | SQLite | não | Banco privado opcional; não pode ser requisito para corrigir questões. |

## 3. Saidas canonicas

| Nome | Destino | Formato | Garantias |
| --- | --- | --- | --- |
| `progress_db` | `runtime/question-practice/progress.db` | SQLite | Guarda tentativas, resultado e agenda local; não deve ser versionado. |
| `structured_logs` | stdout e futuro `runtime/logs/` | JSONL | Eventos parseáveis com `ts`, `lvl`, `svc`, `mod`, `evt` e `msg`. |

## 4. Schema Público Esperado

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

## 5. Identificadores E Chaves

| Conceito | Campo canônico | Observações |
| --- | --- | --- |
| Grupo de questão | `question_groups.id` | Identificador estável usado para tela, tentativa e agenda. |
| Item ou alternativa | `question_items.id` | Identificador estável para resposta marcada e correção. |
| Disciplina | `question_groups.chapter_number` e `chapter_groups.chapter_title` | O piloto começa por `chapter_number = 1`, Língua Portuguesa. |
| Gabarito | `question_items.answer_normalized` | Valores esperados: `correct`, `wrong`, `annulled` ou alternativas convertidas para acerto/erro em múltipla escolha. |

## 6. Banco De Progresso Previsto

O schema local ainda será materializado, mas deve representar:

- `attempts`: tentativa por grupo de questão, data, resultado agregado e classificação do usuário
- `attempt_answers`: resposta marcada por item ou alternativa
- `review_cards`: estado de repetição por grupo de questão, próxima revisão, intervalo e fator de facilidade
- `schema_migrations`: controle de migrações idempotentes

## 7. Eventos Ou Etapas De Pipeline

| Etapa | Entrada | Saída | Falhas esperadas |
| --- | --- | --- | --- |
| `load_question` | banco público e filtro de disciplina | grupo completo para renderização | banco ausente, schema incompatível, questão sem itens |
| `submit_attempt` | respostas do usuário | tentativa persistida e resultado calculado | resposta incompleta, item desconhecido, gabarito ausente |
| `schedule_review` | resultado e dificuldade percebida | próxima data de revisão | dificuldade inválida, banco de progresso indisponível |

## 8. Assunções Ainda Não Validadas

- o banco público importado preserva todos os textos-base necessários para Língua Portuguesa
- o schema atual de `question_groups` e `question_items` será suficiente para o piloto sem migração
- uma agenda por grupo de questão é melhor para o usuário do que uma agenda por item isolado

## 9. Quebras De Contrato

Registre aqui mudanças que exigem:

- migração de dados
- ajuste de integração
- restart operacional
- versão nova de cliente

Formato:

- `YYYY-MM-DD`: descrição da quebra de contrato
