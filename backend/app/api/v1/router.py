"""Agregador das rotas da v1.

O prefixo `/api/v1` fica AQUI, num lugar so. Cada router filho declara
apenas o proprio recurso (`/auth`, `/cupcakes`). Versionar a API depois
vira criar `v2/router.py` e montar os dois - sem tocar em nenhuma rota.
"""

from fastapi import APIRouter

from app.api.v1 import auth, pedido
from app.api.v1.catalogo import carrinho_router, catalogo_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(catalogo_router)
api_router.include_router(carrinho_router)
api_router.include_router(pedido.router)
