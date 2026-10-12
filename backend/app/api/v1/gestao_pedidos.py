"""Rotas da LOJA para gerir pedidos. Extensao da historia ID 08 / RF-15.

TODAS exigem admin - e isso esta declarado UMA vez, no router
-------------------------------------------------------------
`dependencies=[Depends(usuario_admin)]` no `APIRouter` faz o FastAPI
rodar a checagem antes de QUALQUER rota deste arquivo, inclusive as que
alguem acrescentar no futuro. Se a protecao estivesse em cada funcao
(como `_: AdminDep` no parametro), bastaria esquecer em uma rota nova
para abrir a gestao da loja a qualquer cliente logado.

E o principio de padroes seguros (secure by default / fail-safe
defaults): o caminho sem esforco e o caminho protegido. Para uma rota
daqui ficar publica, alguem teria de MOVE-LA de arquivo - uma decisao
visivel na revisao, nao um esquecimento.

Respostas: anonimo -> 401, cliente comum -> 403, admin -> segue.

POR QUE POST EM `avancar` E `cancelar`, E NAO PATCH COM O STATUS
----------------------------------------------------------------
Sao ACOES, nao edicoes de campo. O front nao escolhe o status de
destino: diz "avance" e o dominio decide para onde. Com
`PATCH {"status": "entregue"}`, o front poderia pedir um salto - a FSM
recusaria, mas a API estaria convidando ao erro. E POST porque nao e
idempotente: avancar duas vezes avanca duas etapas.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import GestaoPedidosServiceDep, usuario_admin
from app.api.v1.schemas import (
    AlterarEnderecoRequest,
    PedidoGestaoResponse,
    PedidoGestaoResumoResponse,
)
from app.domain.entities import StatusPedido

router = APIRouter(
    prefix="/admin/pedidos",
    tags=["loja"],
    dependencies=[Depends(usuario_admin)],
)


@router.get("", response_model=list[PedidoGestaoResumoResponse])
def listar(
    servico: GestaoPedidosServiceDep,
    filtro: Annotated[StatusPedido | None, Query(alias="status")] = None,
):
    """Pedidos de TODOS os clientes, mais recentes primeiro.

    `?status=recebido` filtra a fila. Valor fora do enum vira 422 pelo
    Pydantic - nunca chega ao SQL.
    """
    return [PedidoGestaoResumoResponse.de_dominio(p) for p in servico.listar(filtro)]


@router.get("/{pedido_id}", response_model=PedidoGestaoResponse)
def detalhar(pedido_id: UUID, servico: GestaoPedidosServiceDep):
    return PedidoGestaoResponse.de_dominio(servico.detalhar(pedido_id))


@router.post("/{pedido_id}/avancar", response_model=PedidoGestaoResponse)
def avancar(pedido_id: UUID, servico: GestaoPedidosServiceDep):
    """Uma etapa adiante. Pedido finalizado -> 409 (RN-05)."""
    return PedidoGestaoResponse.de_dominio(servico.avancar(pedido_id))


@router.post("/{pedido_id}/cancelar", response_model=PedidoGestaoResponse)
def cancelar(pedido_id: UUID, servico: GestaoPedidosServiceDep):
    """So antes de sair para entrega -> senao 409 (RN-05)."""
    return PedidoGestaoResponse.de_dominio(servico.cancelar(pedido_id))


@router.patch("/{pedido_id}", response_model=PedidoGestaoResponse)
def alterar_endereco(
    pedido_id: UUID, payload: AlterarEnderecoRequest, servico: GestaoPedidosServiceDep
):
    """Corrige o endereco. Depois de sair para entrega -> 409 (RN-11)."""
    return PedidoGestaoResponse.de_dominio(
        servico.alterar_endereco(pedido_id, payload.endereco_entrega)
    )


@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(pedido_id: UUID, servico: GestaoPedidosServiceDep):
    """Exclusao LOGICA. Pedido em andamento -> 409 (RN-13).

    204 sem corpo: nao ha o que devolver de um recurso que deixou de
    existir para a aplicacao. Uma segunda chamada devolve 404 - o efeito
    no servidor e o mesmo (pedido excluido), que e o que a RFC 9110
    exige de um DELETE idempotente.
    """
    servico.excluir(pedido_id)
