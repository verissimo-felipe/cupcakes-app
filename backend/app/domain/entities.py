"""Entidades de dominio - Python puro, sem imports de framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from app.domain.errors import (
    CarrinhoVazioError,
    CupcakeIndisponivelError,
    EnderecoInvalidoError,
    ItemNaoEncontradoError,
    PedidoNaoEditavelError,
    PedidoNaoExcluivelError,
    QuantidadeInvalidaError,
    TransicaoStatusInvalidaError,
)

QUANTIDADE_MINIMA = 1
ENDERECO_MINIMO = 5


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _validar_endereco(texto: str) -> str:
    """RN-12 - devolve o endereco limpo ou recusa."""
    limpo = texto.strip()
    if len(limpo) < ENDERECO_MINIMO:
        raise EnderecoInvalidoError(ENDERECO_MINIMO)
    return limpo


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

# O "caminho feliz" da FSM: para cada estado, a UNICA etapa seguinte.
#
# Nao substitui `TRANSICOES_PERMITIDAS` - e um subconjunto dela, sem os
# desvios (cancelar). Existe para o botao "avancar" da loja nao precisar
# escolher o destino: quem escolhe e o dominio. Assim nao ha como o
# front pedir um salto de `recebido` direto para `entregue`.
#
# `test_proxima_etapa_e_subconjunto_da_fsm` garante que as duas tabelas
# nunca divirjam.
PROXIMA_ETAPA: dict[StatusPedido, StatusPedido] = {
    StatusPedido.RECEBIDO: StatusPedido.EM_PREPARO,
    StatusPedido.EM_PREPARO: StatusPedido.SAIU_PARA_ENTREGA,
    StatusPedido.SAIU_PARA_ENTREGA: StatusPedido.ENTREGUE,
}

# RN-11 - enquanto o pedido esta na loja, o endereco ainda pode mudar.
STATUS_ENDERECO_EDITAVEL = frozenset({StatusPedido.RECEBIDO, StatusPedido.EM_PREPARO})


@dataclass
class Pedido:
    """Pedido fechado. Historias ID 07, 08."""
    id: UUID
    usuario_id: UUID
    itens: list[ItemCarrinho]
    endereco_entrega: str
    total: Decimal
    status: StatusPedido = StatusPedido.RECEBIDO
    criado_em: datetime | None = None
    # Exclusao LOGICA (soft delete): preenchido = excluido. A linha
    # continua no banco; so deixa de aparecer na aplicacao. Ver `excluir`.
    excluido_em: datetime | None = None

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
            endereco_entrega=_validar_endereco(endereco_entrega),  # RN-12
            total=carrinho.total,
            criado_em=_agora(),
        )

    def mudar_status(self, novo: StatusPedido) -> None:
        """RN-05 - valida a transicao contra a FSM antes de aplicar."""
        if novo not in TRANSICOES_PERMITIDAS[self.status]:
            raise TransicaoStatusInvalidaError(self.status.value, novo.value)
        self.status = novo

    # ------------------------------------------------------------------
    # O que a loja pode fazer AGORA.
    #
    # Estas propriedades sao lidas por DOIS consumidores: os metodos
    # abaixo (para validar) e a API (para dizer ao front quais botoes
    # desenhar). Uma regra, uma fonte. O front nao reimplementa a FSM.
    # ------------------------------------------------------------------

    @property
    def proximo_status(self) -> StatusPedido | None:
        return PROXIMA_ETAPA.get(self.status)

    @property
    def pode_cancelar(self) -> bool:
        return StatusPedido.CANCELADO in TRANSICOES_PERMITIDAS[self.status]

    @property
    def pode_editar_endereco(self) -> bool:
        return self.status in STATUS_ENDERECO_EDITAVEL

    @property
    def finalizado(self) -> bool:
        """Estado terminal: a FSM nao tem saida dele."""
        return not TRANSICOES_PERMITIDAS[self.status]

    @property
    def pode_excluir(self) -> bool:
        return self.finalizado and self.excluido_em is None

    # ------------------------------------------------------------------
    # Operacoes da loja
    # ------------------------------------------------------------------

    def avancar(self) -> StatusPedido:
        """Uma etapa por vez, sempre pelo caminho feliz. RN-05.

        Delega a `mudar_status`, entao a FSM continua sendo a unica
        guardia. Pedido entregue ou cancelado nao tem proxima etapa.
        """
        proximo = self.proximo_status
        if proximo is None:
            raise TransicaoStatusInvalidaError(self.status.value, "proxima etapa")
        self.mudar_status(proximo)
        return proximo

    def cancelar(self) -> None:
        self.mudar_status(StatusPedido.CANCELADO)

    def alterar_endereco(self, novo: str) -> None:
        """RN-11 (status) e RN-12 (conteudo).

        So o endereco e editavel. Itens e total NAO: sao o que o cliente
        pagou. Mudar a composicao exigiria estornar ou cobrar a diferenca,
        e isso e um fluxo de pagamento, nao uma edicao.
        """
        if not self.pode_editar_endereco:
            raise PedidoNaoEditavelError(self.status.value)
        self.endereco_entrega = _validar_endereco(novo)

    def excluir(self, quando: datetime | None = None) -> None:
        """RN-13 - exclusao LOGICA, e so de pedido finalizado.

        POR QUE NAO APAGAR A LINHA
        --------------------------
        Pedido e registro de venda. Apagar fisicamente destroi a trilha de
        auditoria: o faturamento do mes deixaria de bater com o caixa, e
        nao haveria como responder a um cliente que contesta a cobranca.
        Aqui a linha fica; so ganha a data de exclusao.

        Chamar duas vezes nao muda a data original - a operacao e
        idempotente.
        """
        if not self.finalizado:
            raise PedidoNaoExcluivelError(self.status.value)
        if self.excluido_em is None:
            self.excluido_em = quando or _agora()
