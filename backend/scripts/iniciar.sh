#!/bin/sh
# Inicializacao em PRODUCAO (Render, ou qualquer host que rode o Dockerfile).
#
# Ordem importa:
#   1. migracoes  - o banco precisa das tabelas antes de tudo
#   2. seed       - catalogo inicial; idempotente, rodar a cada boot e seguro
#   3. servidor   - `exec` troca o shell pelo uvicorn, para o sinal de
#                   desligamento do host chegar direto ao servidor
#
# `set -e`: se a migracao falhar, o servidor NAO sobe com o banco pela
# metade - o deploy falha visivelmente e o log mostra o motivo.
#
# PORT: o host define a porta (o Render usa 10000). Localmente, 8000.
set -e

alembic upgrade head
python -m app.infra.seed
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
