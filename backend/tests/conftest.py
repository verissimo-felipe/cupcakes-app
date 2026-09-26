"""Configuracao compartilhada da suite.

O pytest importa este arquivo ANTES de qualquer modulo de teste, o que o
torna o lugar certo para preparar o ambiente.

Por que ele precisa existir: `core/config.py` nao define default para
`SECRET_KEY` nem `DATABASE_URL` - ausencia derruba a aplicacao no boot.
Esse comportamento e deliberado e nao deve ser afrouxado: e melhor a
aplicacao morrer na inicializacao do que subir em producao com chave
vazia e falhar silenciosamente.

A consequencia e que os testes precisam fornecer esses valores. Os
valores abaixo sao ficticios e locais - `setdefault` garante que um
`.env` real ou variaveis do CI tenham precedencia.
"""

import os

os.environ.setdefault("SECRET_KEY", "chave-de-teste-nao-usar-em-producao")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("DEBUG", "false")
