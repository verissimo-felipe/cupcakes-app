"""Ponto de entrada da API.

Esta camada e a UNICA que conhece HTTP. O papel dela e traduzir:
    erro de dominio  ->  status code
    entidade         ->  JSON

O `exception_handler` abaixo e a fronteira. Sem ele, cada router teria
try/except repetido - e alguem esqueceria um, devolvendo 500 para o que
deveria ser 400.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.domain.errors import (
    CarrinhoVazioError,
    CupcakeIndisponivelError,
    DomainError,
    ItemNaoEncontradoError,
    QuantidadeInvalidaError,
    TransicaoStatusInvalidaError,
)

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="API da loja de cupcakes - Situacao Problema 2",
)

# CORS - Cross-Origin Resource Sharing.
# `allow_credentials=True` exige lista explicita de origens; o navegador
# recusa o par ("*", credentials). Nao e capricho do FastAPI, e a spec.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mapa erro de dominio -> status HTTP.
# Tabela em vez de if/elif: adicionar um erro novo e uma linha, e fica
# obvio na revisao de codigo qual contrato HTTP mudou.
_STATUS_POR_ERRO: dict[type[DomainError], int] = {
    QuantidadeInvalidaError: 422,
    CupcakeIndisponivelError: 409,
    ItemNaoEncontradoError: 404,
    CarrinhoVazioError: 422,
    TransicaoStatusInvalidaError: 409,
}


@app.exception_handler(DomainError)
async def tratar_erro_dominio(_: Request, exc: DomainError) -> JSONResponse:
    status = _STATUS_POR_ERRO.get(type(exc), 400)
    return JSONResponse(
        status_code=status,
        content={"codigo": exc.codigo, "mensagem": str(exc)},
    )


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    """Usado pelo healthcheck do docker-compose."""
    return {"status": "ok"}
