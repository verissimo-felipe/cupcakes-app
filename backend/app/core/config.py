"""Configuracao central - nenhum segredo no codigo."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    # autorizados a mudar status de pedido.
    ADMIN_EMAILS: list[str] = []


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
