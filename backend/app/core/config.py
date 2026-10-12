"""Configuracao central - nenhum segredo no codigo."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Prefixos que provedores de Postgres (Neon, Render, Heroku) entregam.
# Sem o "+psycopg", o SQLAlchemy tenta o driver psycopg2 - que nao esta
# instalado - e a aplicacao morre no boot com ModuleNotFoundError.
_PREFIXOS_SEM_DRIVER = ("postgres://", "postgresql://")
_PREFIXO_COM_DRIVER = "postgresql+psycopg://"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Cupcakes API"
    DEBUG: bool = False

    # Sem default: ausencia derruba a aplicacao no boot, que e o desejado.
    SECRET_KEY: str
    DATABASE_URL: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # False em desenvolvimento: o navegador DESCARTA cookie Secure sobre
    # HTTP, e o login falharia em silencio. True obrigatoriamente em
    # producao, onde o trafego e HTTPS.
    COOKIE_SECURE: bool = False

    # Sem sistema de perfis (ver `deps.usuario_admin`). Lista de e-mails
    # autorizados a usar a gestao da loja (rotas /api/v1/admin/...).
    ADMIN_EMAILS: list[str] = []

    @field_validator("DATABASE_URL")
    @classmethod
    def _usar_driver_psycopg(cls, url: str) -> str:
        """Aceita a URL exatamente como o provedor entrega.

        O painel do Neon copia `postgresql://...`; o Render e o Heroku
        antigos usam `postgres://`. Os dois viram `postgresql+psycopg://`,
        o driver instalado no projeto. Corrigir aqui evita um erro de
        deploy que so aparece no log do servidor.
        """
        for prefixo in _PREFIXOS_SEM_DRIVER:
            if url.startswith(prefixo):
                return _PREFIXO_COM_DRIVER + url[len(prefixo):]
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
