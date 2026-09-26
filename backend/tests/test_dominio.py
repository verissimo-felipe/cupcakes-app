"""Testes do dominio.

Repare no que NAO existe aqui: nenhuma fixture de banco, nenhum client
HTTP, nenhum mock. O dominio e puro, entao os testes rodam em
milissegundos. Essa velocidade e consequencia direta da arquitetura -
se voce precisasse subir Postgres para testar "quantidade minima e 1",
a regra estaria no lugar errado.

Rodar:  pytest -v
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.entities import Carrinho, Cupcake, Pedido, StatusPedido
from app.domain.errors import (
    CarrinhoVazioError,
    CupcakeIndisponivelError,
    ItemNaoEncontradoError,
    QuantidadeInvalidaError,
    TransicaoStatusInvalidaError,
)


@pytest.fixture
def cupcake_baunilha() -> Cupcake:
    return Cupcake(
        id=uuid4(),
        nome="Cupcake de Baunilha",
        descricao="Massa de baunilha com cobertura de buttercream",
        sabor="baunilha",
        preco=Decimal("8.50"),
        imagem_url="/img/baunilha.jpg",
    )


@pytest.fixture
def carrinho() -> Carrinho:
    return Carrinho(usuario_id=uuid4())


# --------------------------------------------------------------------
# Historia ID 05 - Adicionar ao Carrinho
# --------------------------------------------------------------------


def test_adicionar_cria_linha_nova(carrinho, cupcake_baunilha):
    carrinho.adicionar(cupcake_baunilha, quantidade=2)

    assert len(carrinho.itens) == 1
    assert carrinho.itens[0].quantidade == 2
    assert carrinho.total == Decimal("17.00")


def test_rn06_item_repetido_soma_em_vez_de_duplicar(carrinho, cupcake_baunilha):
    """RN-06 - o erro classico e criar duas linhas do mesmo produto."""
    carrinho.adicionar(cupcake_baunilha, quantidade=2)
    carrinho.adicionar(cupcake_baunilha, quantidade=3)

    assert len(carrinho.itens) == 1
    assert carrinho.itens[0].quantidade == 5


def test_rn01_quantidade_zero_e_recusada(carrinho, cupcake_baunilha):
    with pytest.raises(QuantidadeInvalidaError):
        carrinho.adicionar(cupcake_baunilha, quantidade=0)


def test_rn02_cupcake_indisponivel_e_recusado(carrinho, cupcake_baunilha):
    esgotado = Cupcake(
        **{**cupcake_baunilha.__dict__, "disponivel": False}
    )
    with pytest.raises(CupcakeIndisponivelError):
        carrinho.adicionar(esgotado)


# --------------------------------------------------------------------
# Historia ID 06 - Remover do Carrinho
# --------------------------------------------------------------------


def test_remover_item_existente(carrinho, cupcake_baunilha):
    carrinho.adicionar(cupcake_baunilha)
    carrinho.remover(cupcake_baunilha.id)

    assert carrinho.vazio


def test_rn03_remover_ausente_levanta_erro(carrinho):
    with pytest.raises(ItemNaoEncontradoError):
        carrinho.remover(uuid4())


# --------------------------------------------------------------------
# Historia ID 07 - Finalizacao / Checkout
# --------------------------------------------------------------------


def test_rn04_carrinho_vazio_nao_vira_pedido(carrinho):
    with pytest.raises(CarrinhoVazioError):
        Pedido.a_partir_do_carrinho(carrinho, "Rua das Flores, 123")


def test_pedido_congela_itens_do_carrinho(carrinho, cupcake_baunilha):
    """Esvaziar o carrinho depois nao pode mutilar o pedido gerado."""
    carrinho.adicionar(cupcake_baunilha, quantidade=2)
    pedido = Pedido.a_partir_do_carrinho(carrinho, "Rua das Flores, 123")

    carrinho.remover(cupcake_baunilha.id)

    assert len(pedido.itens) == 1
    assert pedido.total == Decimal("17.00")
    assert carrinho.vazio


# --------------------------------------------------------------------
# Historia ID 08 - Rastreamento (FSM)
# --------------------------------------------------------------------


def test_fsm_fluxo_feliz(carrinho, cupcake_baunilha):
    carrinho.adicionar(cupcake_baunilha)
    pedido = Pedido.a_partir_do_carrinho(carrinho, "Rua das Flores, 123")

    assert pedido.status is StatusPedido.RECEBIDO
    pedido.mudar_status(StatusPedido.EM_PREPARO)
    pedido.mudar_status(StatusPedido.SAIU_PARA_ENTREGA)
    pedido.mudar_status(StatusPedido.ENTREGUE)

    assert pedido.status is StatusPedido.ENTREGUE


def test_rn05_nao_pula_etapa(carrinho, cupcake_baunilha):
    carrinho.adicionar(cupcake_baunilha)
    pedido = Pedido.a_partir_do_carrinho(carrinho, "Rua das Flores, 123")

    with pytest.raises(TransicaoStatusInvalidaError):
        pedido.mudar_status(StatusPedido.ENTREGUE)


def test_rn05_entregue_e_estado_terminal(carrinho, cupcake_baunilha):
    carrinho.adicionar(cupcake_baunilha)
    pedido = Pedido.a_partir_do_carrinho(carrinho, "Rua das Flores, 123")
    pedido.mudar_status(StatusPedido.EM_PREPARO)
    pedido.mudar_status(StatusPedido.SAIU_PARA_ENTREGA)
    pedido.mudar_status(StatusPedido.ENTREGUE)

    with pytest.raises(TransicaoStatusInvalidaError):
        pedido.mudar_status(StatusPedido.CANCELADO)
