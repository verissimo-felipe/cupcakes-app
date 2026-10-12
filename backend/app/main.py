"""Ponto de entrada da API.

Esta camada e a UNICA que conhece HTTP. Traduz:
    erro de dominio  ->  status code
    entidade         ->  JSON
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.domain.errors import (
    CarrinhoVazioError,
    CredenciaisInvalidasError,
    CupcakeIndisponivelError,
    CupcakeNaoEncontradoError,
    DomainError,
    EmailInvalidoError,
    EmailJaCadastradoError,
    EnderecoInvalidoError,
    ItemNaoEncontradoError,
    PedidoNaoEditavelError,
    PedidoNaoEncontradoError,
    PedidoNaoExcluivelError,
    QuantidadeInvalidaError,
    SenhaFracaError,
    SenhaMuitoLongaError,
    TransicaoStatusInvalidaError,
)

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="API da loja de cupcakes - Situacao Problema 2",
)

# CORS - Cross-Origin Resource Sharing.
# `allow_credentials=True` exige lista EXPLICITA de origens; o navegador
# recusa o par ("*", credentials). Nao e limitacao do FastAPI, e a spec -
# e sem credentials o cookie de sessao nunca chegaria ao backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


# Mapa erro de dominio -> status HTTP.
#
# Tabela em vez de if/elif: acrescentar um erro e uma linha, e fica
# explicito na revisao qual contrato HTTP mudou.
#
# Sobre as escolhas:
#   422 - entrada sintaticamente valida mas semanticamente errada
#   409 - conflito com o estado atual do recurso
#   404 - inexistente OU invisivel para quem pergunta
#   401 - nao autenticado
_STATUS_POR_ERRO: dict[type[DomainError], int] = {
    QuantidadeInvalidaError: 422,
    CupcakeIndisponivelError: 409,
    ItemNaoEncontradoError: 404,
    CarrinhoVazioError: 422,
    TransicaoStatusInvalidaError: 409,
    SenhaFracaError: 422,
    SenhaMuitoLongaError: 422,
    EmailInvalidoError: 422,
    EmailJaCadastradoError: 409,
    CredenciaisInvalidasError: 401,
    CupcakeNaoEncontradoError: 404,
    PedidoNaoEncontradoError: 404,
    EnderecoInvalidoError: 422,
    PedidoNaoEditavelError: 409,
    PedidoNaoExcluivelError: 409,
}


@app.exception_handler(DomainError)
async def tratar_erro_dominio(_: Request, exc: DomainError) -> JSONResponse:
    """Fronteira unica entre dominio e HTTP.

    Sem isto, cada router repetiria try/except - e alguem esqueceria um,
    devolvendo 500 para o que deveria ser 400. O default 400 cobre erro
    de dominio novo que ninguem mapeou: resposta errada, mas nunca 500.
    """
    return JSONResponse(
        status_code=_STATUS_POR_ERRO.get(type(exc), 400),
        content={"codigo": exc.codigo, "mensagem": str(exc)},
    )


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    """Healthcheck do docker-compose. Nao toca no banco de proposito:
    responde se o processo esta vivo, nao se o banco esta."""
    return {"status": "ok"}
