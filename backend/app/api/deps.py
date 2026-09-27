"""Dependencias do FastAPI - a raiz de composicao (composition root).

ESTE ARQUIVO E ONDE A FIACAO ACONTECE.

Em toda a aplicacao, os servicos declaram que precisam de um
`CupcakeRepository` - um `Protocol`. Nenhum deles sabe que existe
SQLAlchemy. Alguem, em algum lugar, precisa decidir qual implementacao
concreta entra. Esse lugar e aqui, e so aqui.

Concentrar a fiacao num ponto unico e o que torna a troca viavel: para
rodar a suite inteira contra outro banco, ou contra repositorios falsos,
basta sobrescrever estas funcoes - `app.dependency_overrides` do FastAPI
faz exatamente isso, e e como `tests/test_api.py` funciona.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decodificar_token
from app.domain.usuario import Usuario
from app.infra.db import get_session
from app.infra.repositories import (
    CarrinhoRepositorySQL,
    CupcakeRepositorySQL,
    PedidoRepositorySQL,
    UsuarioRepositorySQL,
)
from app.services.autenticacao import AutenticacaoService
from app.services.catalogo import CarrinhoService, CatalogoService
from app.services.pedido import PedidoService

NOME_COOKIE = "acesso"

SessionDep = Annotated[Session, Depends(get_session)]


# ---------------------------------------------------------------------
# Fabricas de servico - repositorio concreto entra aqui
# ---------------------------------------------------------------------


def get_auth_service(session: SessionDep) -> AutenticacaoService:
    return AutenticacaoService(UsuarioRepositorySQL(session))


def get_catalogo_service(session: SessionDep) -> CatalogoService:
    return CatalogoService(CupcakeRepositorySQL(session))


def get_carrinho_service(session: SessionDep) -> CarrinhoService:
    return CarrinhoService(CarrinhoRepositorySQL(session), CupcakeRepositorySQL(session))


def get_pedido_service(session: SessionDep) -> PedidoService:
    return PedidoService(PedidoRepositorySQL(session), CarrinhoRepositorySQL(session))


AuthServiceDep = Annotated[AutenticacaoService, Depends(get_auth_service)]
CatalogoServiceDep = Annotated[CatalogoService, Depends(get_catalogo_service)]
CarrinhoServiceDep = Annotated[CarrinhoService, Depends(get_carrinho_service)]
PedidoServiceDep = Annotated[PedidoService, Depends(get_pedido_service)]


# ---------------------------------------------------------------------
# Autenticacao
# ---------------------------------------------------------------------


def usuario_atual(
    session: SessionDep,
    acesso: Annotated[str | None, Cookie(alias=NOME_COOKIE)] = None,
) -> Usuario:
    """Extrai o usuario do JWT guardado em cookie httpOnly.

    POR QUE COOKIE E NAO CABECALHO `Authorization`
    ----------------------------------------------
    Token em `localStorage` e legivel por qualquer JavaScript da pagina.
    Um unico XSS - inclusive vindo de dependencia npm comprometida - rouba
    a sessao inteira. Cookie `httpOnly` e invisivel ao JavaScript: o
    navegador o envia sozinho e a pagina nunca o ve.

    O contra de cookie e CSRF, e a defesa esta em `SameSite=Lax` (ver
    `montar_cookie` em `auth.py`).

    Qualquer falha - cookie ausente, assinatura invalida, token expirado,
    usuario apagado - resulta no MESMO 401. Distinguir "token expirado" de
    "assinatura invalida" ajudaria quem esta forjando tokens.
    """
    nao_autenticado = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"codigo": "nao_autenticado", "mensagem": "Autenticacao necessaria"},
    )

    if not acesso:
        raise nao_autenticado

    payload = decodificar_token(acesso)
    if payload is None or payload.get("type") != "access":
        raise nao_autenticado

    try:
        usuario_id = UUID(payload["sub"])
    except (KeyError, ValueError):
        raise nao_autenticado from None

    # O usuario e recarregado do banco a cada requisicao, em vez de
    # reconstruido do payload. Custa uma consulta, e paga: conta apagada
    # ou desativada para de funcionar imediatamente, sem esperar o token
    # expirar.
    usuario = UsuarioRepositorySQL(session).buscar_por_id(usuario_id)
    if usuario is None:
        raise nao_autenticado

    return usuario


UsuarioDep = Annotated[Usuario, Depends(usuario_atual)]


def usuario_admin(usuario: UsuarioDep) -> Usuario:
    """Restringe rotas administrativas. Historia ID 08 / RF-15.

    LIMITACAO CONHECIDA E DELIBERADA: nao ha sistema de perfis. A lista de
    administradores vem de `ADMIN_EMAILS` no ambiente.

    Para este escopo e suficiente e honesto - a alternativa seria uma
    tabela de papeis que nenhuma historia do backlog pediu. Em producao,
    isto vira RBAC (Role-Based Access Control) com papel persistido.

    O que NAO era aceitavel: deixar a mudanca de status aberta a qualquer
    usuario autenticado. Qualquer cliente marcaria o proprio pedido como
    entregue.
    """
    settings = get_settings()
    if usuario.email not in {e.strip().lower() for e in settings.ADMIN_EMAILS}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"codigo": "acesso_negado", "mensagem": "Operacao restrita"},
        )
    return usuario


AdminDep = Annotated[Usuario, Depends(usuario_admin)]
