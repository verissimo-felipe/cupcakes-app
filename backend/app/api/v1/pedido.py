"""Rotas de pedido DO CLIENTE. Historias ID 07 (checkout) e ID 08 (rastreamento).

Tudo aqui opera sobre os pedidos de QUEM ESTA LOGADO. As operacoes da
loja ficam em `gestao_pedidos.py`, sob `/admin/pedidos` - prefixo
separado para que nenhuma rota de cliente precise de "excecao para admin".
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import PedidoServiceDep, UsuarioDep
from app.api.v1.schemas import (
    CheckoutRequest,
    PedidoResponse,
    PedidoResumoResponse,
)

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


@router.post("", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def finalizar(payload: CheckoutRequest, usuario: UsuarioDep, servico: PedidoServiceDep):
    """Historia ID 07 / RF-12, RF-13.

    O pedido e montado a partir do CARRINHO no servidor - o cliente envia
    apenas o endereco. Aceitar a lista de itens do payload permitiria ao
    cliente montar o proprio pedido com precos escolhidos por ele.

    Carrinho vazio sobe `CarrinhoVazioError` -> 422 (RN-04).
    """
    return PedidoResponse.de_dominio(servico.finalizar(usuario.id, payload.endereco_entrega))


@router.get("", response_model=list[PedidoResumoResponse])
def listar(usuario: UsuarioDep, servico: PedidoServiceDep):
    """Historia ID 08. Resumo, sem os itens - ver `PedidoResumoResponse`."""
    return [PedidoResumoResponse.de_dominio(p) for p in servico.listar_do_usuario(usuario.id)]


@router.get("/{pedido_id}", response_model=PedidoResponse)
def detalhar(pedido_id: UUID, usuario: UsuarioDep, servico: PedidoServiceDep):
    """Historia ID 08 / RF-14.

    IDOR (Insecure Direct Object Reference): o id vem da URL, entao trocar
    um caractere tentaria abrir o pedido de outro cliente - endereco,
    itens e valor gasto.

    A defesa nao esta aqui: `servico.detalhar` EXIGE `usuario_id` na
    assinatura. Nao existe forma de chamar o caso de uso sem decidir de
    quem e o pedido. Pedido alheio devolve 404, nao 403 - 403 confirmaria
    que o id existe.
    """
    return PedidoResponse.de_dominio(servico.detalhar(pedido_id, usuario.id))
