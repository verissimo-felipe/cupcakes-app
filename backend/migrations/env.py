"""Ambiente de execucao do Alembic.

Duas responsabilidades:

1. Fornecer a URL do banco - lida de `app.core.config`, nunca duplicada
   no `alembic.ini`. Assim a migracao aponta sempre para o mesmo banco
   que a aplicacao, e nenhuma credencial vai para o Git.

2. Expor o metadata das tabelas para o `--autogenerate` comparar contra o
   banco real.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.infra.db import Base

# ATENCAO: este import parece inutil e NAO e.
#
# As classes ORM so se registram em `Base.metadata` quando o modulo que as
# define e importado. Sem esta linha, `target_metadata` fica vazio e o
# `alembic revision --autogenerate` gera uma migracao sem nenhuma tabela -
# ou, pior, uma migracao que MANDA APAGAR todas as tabelas existentes,
# por concluir que o codigo nao declara nenhuma.
#
# E o erro numero um de quem configura Alembic pela primeira vez.
import app.infra.models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Gera o SQL sem conectar ao banco.

    Util quando o DBA precisa revisar o script antes de aplicar em
    producao: `alembic upgrade head --sql` imprime o DDL em vez de
    executa-lo.
    """
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Aplica as migracoes conectando ao banco."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Sem isto, o autogenerate ignora mudancas de tipo (String(120)
            # para String(200), por exemplo) e a migracao sai incompleta.
            compare_type=True,
            # SQLite nao suporta ALTER TABLE completo. O batch mode recria
            # a tabela por tras dos panos. Inofensivo no PostgreSQL, e o
            # que permite rodar a mesma migracao nos dois bancos.
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
