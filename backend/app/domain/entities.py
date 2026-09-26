"""Entidades de dominio - Python puro, sem imports de framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from app.domain.errors import (
    CarrinhoVazioError,
    CupcakeIndisponivelError,
    ItemNaoEncontradoError,
    QuantidadeInvalidaError,
    TransicaoStatusInvalidaError,
)

QUANTIDADE_MINIMA = 1


@dataclass(frozen=True)
class Cupcake:
    """Produto do catalogo. Historia ID 04 / RF-05."""
    id: UUID
    nome: str
    descricao: str
    sabor: str
    preco: Decimal
    imagem_url: str
    disponivel: bool = True


@dataclass
class ItemCarrinho:
    """Linha do carrinho. Historias ID 05, 06."""
    cupcake_id: UUID
    nome: str
    preco_unitario: Decimal
    quantidade: int

    def __post_init__(self) -> None:
        if self.quantidade < QUANTIDADE_MINIMA:
            raise QuantidadeInvalidaError(self.quantidade)

    @property
    def subtotal(self) -> Decimal:
        return self.preco_unitario * self.quantidade


@dataclass
class Carrinho:
    """Agregado do carrinho. Historias ID 05, 06 / RF-08, RF-09."""
    usuario_id: UUID
    itens: list[ItemCarrinho] = field(default_factory=list)

    def adicionar(self, cupcake: Cupcake, quantidade: int = 1) -> None:
        """RN-01 quantidade minima, RN-02 disponibilidade, RN-06 soma."""
        if quantidade < QUANTIDADE_MINIMA:
            raise QuantidadeInvalidaError(quantidade)
        if not cupcake.disponivel:
            raise CupcakeIndisponivelError(cupcake.nome)

        existente = self._buscar(cupcake.id)
        if existente is not None:
            existente.quantidade += quantidade
            return

        self.itens.append(
            ItemCarrinho(cupcake.id, cupcake.nome, cupcake.preco, quantidade)
        )

    def remover(self, cupcake_id: UUID) -> None:
        item = self._buscar(cupcake_id)
        if item is None:
            raise ItemNaoEncontradoError(str(cupcake_id))
        self.itens.remove(item)

    def alterar_quantidade(self, cupcake_id: UUID, quantidade: int) -> None:
        item = self._buscar(cupcake_id)
        if item is None:
            raise ItemNaoEncontradoError(str(cupcake_id))
        if quantidade < QUANTIDADE_MINIMA:
            raise QuantidadeInvalidaError(quantidade)
        item.quantidade = quantidade

    @property
    def total(self) -> Decimal:
        return sum((i.subtotal for i in self.itens), Decimal("0"))

    @property
    def vazio(self) -> bool:
        return len(self.itens) == 0

    def _buscar(self, cupcake_id: UUID) -> ItemCarrinho | None:
        return next((i for i in self.itens if i.cupcake_id == cupcake_id), None)


class StatusPedido(str, Enum):
    """Estados do pedido. Historia ID 08 / RF-14, RF-15."""
    RECEBIDO = "recebido"
    EM_PREPARO = "em_preparo"
    SAIU_PARA_ENTREGA = "saiu_para_entrega"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"


TRANSICOES_PERMITIDAS: dict[StatusPedido, set[StatusPedido]] = {
    StatusPedido.RECEBIDO: {StatusPedido.EM_PREPARO, StatusPedido.CANCELADO},
    StatusPedido.EM_PREPARO: {StatusPedido.SAIU_PARA_ENTREGA, StatusPedido.CANCELADO},
    StatusPedido.SAIU_PARA_ENTREGA: {StatusPedido.ENTREGUE},
    StatusPedido.ENTREGUE: set(),
    StatusPedido.CANCELADO: set(),
}


@dataclass
class Pedido:
    """Pedido fechado. Historias ID 07, 08."""
    id: UUID
    usuario_id: UUID
    itens: list[ItemCarrinho]
    endereco_entrega: str
    total: Decimal
    status: StatusPedido = StatusPedido.RECEBIDO

    @classmethod
    def a_partir_do_carrinho(cls, carrinho: Carrinho, endereco_entrega: str) -> "Pedido":
        """RN-04 - carrinho vazio nao vira pedido. Itens sao COPIADOS."""
        if carrinho.vazio:
            raise CarrinhoVazioError("Carrinho vazio nao pode ser finalizado")

        return cls(
            id=uuid4(),
            usuario_id=carrinho.usuario_id,
            itens=[
                ItemCarrinho(i.cupcake_id, i.nome, i.preco_unitario, i.quantidade)
                for i in carrinho.itens
            ],
            endereco_entrega=endereco_entrega,
            total=carrinho.total,
        )

    def mudar_status(self, novo: StatusPedido) -> None:
        """RN-05 - valida a transicao contra a FSM antes de aplicar."""
        if novo not in TRANSICOES_PERMITIDAS[self.status]:
            raise TransicaoStatusInvalidaError(self.status.value, novo.value)
        self.status = novo
