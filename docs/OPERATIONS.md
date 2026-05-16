# OPERATIONS

## 1. Objetivo

Este documento permite executar, diagnosticar, reiniciar e recuperar o `Hlidskjalf` sem depender de contexto implícito.

## 2. Ambientes

| Ambiente | Objetivo | Runtime | Observações |
| --- | --- | --- | --- |
| `local` | desenvolvimento e estudo real | Node.js 20+ | Ambiente principal no bootstrap. |
| `test` | validação automatizada | Node.js 20+ e Python 3 | Roda smoke Node e guardrails do Skidbladnir. |
| `prod` | não definido | não definido | Não há deploy remoto na primeira versão. |

## 3. Como Executar

### Boot local

```bash
npm install
cp config/settings.example.json config/settings.local.json
```

### Validação

```bash
npm test
python3 scripts/build_tps_question_db.py
python3 scripts/check_project_gate.py
python3 scripts/project_doctor.py
python3 scripts/project_doctor.py --audit-config
```

### Boot principal

```bash
npm start
```

No estado atual, `npm start` apenas valida o bootstrap do entrypoint e emite log estruturado. A interface HTTP local será implementada depois da validação do banco de Língua Portuguesa.

## 4. Configuração Operacional

- arquivo local: `config/settings.local.json`
- variáveis de ambiente críticas:
  - `HLIDSKJALF_CONFIG_FILE`
  - `NODE_ENV`
- path de bancos públicos: `data/questions/`
- path de runtime state: `runtime/`
- path previsto de progresso: `runtime/question-practice/progress.db`
- path previsto de logs: `runtime/logs/`

## 5. Validacao minima

Depois de subir:

```bash
npm test
```

Conferir:

- processo principal executa sem erro
- logs de bootstrap aparecem como JSON
- configuração carrega `config/settings.example.json` quando não há arquivo local
- paths previstos de banco estão documentados

## 6. Dados E Persistência

Versionável:

- schema e código da aplicação
- bancos públicos de questões e gabaritos em `data/questions/`, incluindo `data/questions/tps-comentado-2019-public.db`
- fixtures mínimas sem conteúdo protegido, se forem criadas

Não versionável:

- progresso local do usuário
- comentários autorais
- PDFs, dumps, bancos privados e caches
- `config/settings.local.json`

Rebuild do banco público:

```bash
python3 scripts/build_tps_question_db.py
sqlite3 data/questions/tps-comentado-2019-public.db "pragma integrity_check"
```

O comando também regenera `runtime/books/tps-comentado-2019-comments.db`, que é privado e ignorado pelo git.

## 7. Logs E Diagnóstico

- logger principal: `hlidskjalf/infrastructure/logger.mjs`
- formato dos logs: JSON em linha única
- onde ler logs hoje: stdout
- onde ler logs futuramente: `runtime/logs/`

Sinais de falha comuns:

- banco público ausente em `data/questions/`
- schema de banco incompatível com `docs/CONTRACTS.md`
- progresso local corrompido em `runtime/question-practice/progress.db`
- configuração local apontando para path inexistente

## 8. Restart Policy

Ao mudar:

- `hlidskjalf/domain/`: reiniciar processo Node local
- `hlidskjalf/application/`: reiniciar processo Node local
- `hlidskjalf/infrastructure/`: reiniciar processo Node local
- `hlidskjalf/interfaces/`: reiniciar processo Node local
- `config/settings.local.json`: reiniciar para garantir recarga
- `data/questions/*.db`: reiniciar ou recarregar a conexão do banco
- `docs/` apenas: nenhum restart

## 9. Backup E Limpeza

Backup recomendado:

- copiar `runtime/question-practice/progress.db` antes de resetar ou migrar agenda de revisão

Limpeza segura:

- `runtime/logs/` pode ser limpo se não houver diagnóstico em andamento
- caches futuros podem ser removidos se forem reconstruíveis

Nunca remova sem intenção explícita:

- `runtime/question-practice/progress.db`
- bancos privados de comentários ou anotações locais
- bancos públicos em `data/questions/` sem checar se são versionados

## 10. Incidentes

Checklist mínimo:

1. confirmar `npm test`
2. confirmar que a configuração carregada aponta para bancos existentes
3. confirmar integridade SQLite com `pragma integrity_check`
4. confirmar permissões de escrita em `runtime/`
5. confirmar último erro estruturado no stdout ou em `runtime/logs/`
6. confirmar se houve mudança recente em schema público ou progress db

## 11. Mudanças Que Exigem Update Deste Documento

- novo entrypoint
- novo path de banco público ou progresso
- nova regra de restart
- nova rotina de backup, reset ou migração
- nova integração externa ou modo de deploy
