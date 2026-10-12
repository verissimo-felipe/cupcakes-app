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


# --------------------------------------------------------------------
# Gestao pela loja - extensao da historia ID 08 / RF-15
# --------------------------------------------------------------------


@pytest.fixture
def pedido(carrinho, cupcake_baunilha) -> Pedido:
    carrinho.adicionar(cupcake_baunilha, quantidade=2)
    return Pedido.a_partir_do_carrinho(carrinho, "Rua das Flores, 123")


def test_proxima_etapa_e_subconjunto_da_fsm():
    """Teste de INVARIANTE: as duas tabelas nunca podem divergir.

    Se alguem acrescentar uma etapa em PROXIMA_ETAPA sem libera-la em
    TRANSICOES_PERMITIDAS, o botao "avancar" levaria 409 para sempre.
    Este teste quebra antes disso chegar a tela.
    """
    from app.domain.entities import PROXIMA_ETAPA, TRANSICOES_PERMITIDAS

    for origem, destino in PROXIMA_ETAPA.items():
        assert destino in TRANSICOES_PERMITIDAS[origem]


def test_avancar_percorre_o_caminho_feliz_uma_etapa_por_vez(pedido):
    assert pedido.avancar() is StatusPedido.EM_PREPARO
    assert pedido.avancar() is StatusPedido.SAIU_PARA_ENTREGA
    assert pedido.avancar() is StatusPedido.ENTREGUE
    assert pedido.proximo_status is None


def test_rn05_avancar_pedido_finalizado_e_recusado(pedido):
    pedido.cancelar()
    with pytest.raises(TransicaoStatusInvalidaError):
        pedido.avancar()


def test_criado_em_e_preenchido_no_checkout(pedido):
    assert pedido.criado_em is not None


def test_rn11_endereco_editavel_enquanto_esta_na_loja(pedido):
    pedido.avancar()  # em_preparo - ainda na cozinha
    pedido.alterar_endereco("  Rua Nova, 456  ")
    assert pedido.endereco_entrega == "Rua Nova, 456"


def test_rn11_endereco_travado_depois_de_sair_para_entrega(pedido):
    from app.domain.errors import PedidoNaoEditavelError

    pedido.avancar()
    pedido.avancar()  # saiu_para_entrega
    with pytest.raises(PedidoNaoEditavelError):
        pedido.alterar_endereco("Rua Nova, 456")
    assert pedido.endereco_entrega == "Rua das Flores, 123"


def test_rn12_endereco_so_com_espacos_e_recusado(pedido):
    from app.domain.errors import EnderecoInvalidoError

    with pytest.raises(EnderecoInvalidoError):
        pedido.alterar_endereco("        ")


def test_rn12_checkout_tambem_recusa_endereco_vazio(carrinho, cupcake_baunilha):
    from app.domain.errors import EnderecoInvalidoError

    carrinho.adicionar(cupcake_baunilha)
    with pytest.raises(EnderecoInvalidoError):
        Pedido.a_partir_do_carrinho(carrinho, "     ")


def test_rn13_pedido_em_andamento_nao_pode_ser_excluido(pedido):
    from app.domain.errors import PedidoNaoExcluivelError

    with pytest.raises(PedidoNaoExcluivelError):
        pedido.excluir()
    assert pedido.excluido_em is None


def test_rn13_exclusao_logica_de_pedido_cancelado(pedido):
    pedido.cancelar()
    pedido.excluir()

    assert pedido.excluido_em is not None
    # Nada mais foi apagado: itens, total e status continuam no objeto.
    assert pedido.total == Decimal("17.00")
    assert pedido.status is StatusPedido.CANCELADO


def test_excluir_duas_vezes_preserva_a_data_original(pedido):
    from datetime import datetime, timezone

    primeira = datetime(2026, 10, 1, tzinfo=timezone.utc)
    pedido.cancelar()
    pedido.excluir(quando=primeira)
    pedido.excluir()

    assert pedido.excluido_em == primeira


def test_acoes_acompanham_o_estado(pedido):
    """As flags que o front usa para desenhar botoes vem do dominio."""
    assert pedido.pode_cancelar and pedido.pode_editar_endereco
    assert not pedido.pode_excluir

    pedido.avancar()
    pedido.avancar()  # saiu_para_entrega
    assert not pedido.pode_cancelar
    assert not pedido.pode_editar_endereco
    assert not pedido.pode_excluir

    pedido.avancar()  # entregue
    assert pedido.pode_excluir
    assert pedido.proximo_status is None
