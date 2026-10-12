"""Configuracao: a URL do banco como os provedores a entregam."""

import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        # Neon copia assim, com parametros de SSL na query.
        (
            "postgresql://u:s@ep-x.sa-east-1.aws.neon.tech/neondb?sslmode=require",
            "postgresql+psycopg://u:s@ep-x.sa-east-1.aws.neon.tech/neondb?sslmode=require",
        ),
        # Formato antigo de Render e Heroku.
        ("postgres://u:s@host:5432/db", "postgresql+psycopg://u:s@host:5432/db"),
        # Ja correta: fica intacta.
        ("postgresql+psycopg://u:s@db:5432/db", "postgresql+psycopg://u:s@db:5432/db"),
        # Outros bancos (testes usam SQLite) nao sao tocados.
        ("sqlite://", "sqlite://"),
    ],
)
def test_database_url_recebe_o_driver_instalado(entrada, esperado):
    config = Settings(SECRET_KEY="x" * 32, DATABASE_URL=entrada)
    assert config.DATABASE_URL == esperado
