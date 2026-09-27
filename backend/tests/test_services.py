"""Testes dos casos de uso.

NENHUM BANCO AQUI. Nem PostgreSQL, nem SQLite, nem arquivo temporario.

Os repositorios abaixo sao dicionarios em memoria que satisfazem os
mesmos `Protocol` de `domain/repositories.py`. Como os servicos dependem
do contrato e nao da implementacao, eles nao percebem a troca.

Isso nao e truque de teste: e a demonstracao pratica de que a inversao
de dependencia funciona. Se algum servico importasse SQLAlchemy, este
arquivo seria impossivel de escrever.
"""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.domain.entities import Carrinho, Cupcake, Pedido, StatusPedido
from app.domain.errors import (
    CarrinhoVazioError,
    CredenciaisInvalidasError,
    CupcakeIndisponivelError,
    CupcakeNaoEncontradoError,
    EmailJaCadastradoError,
    PedidoNaoEncontradoError,
    QuantidadeInvalidaError,
    SenhaFracaError,
    TransicaoStatusInvalidaError,
)
from app.domain.usuario import Usuario
from app.services.autenticacao import AutenticacaoService
from app.services.catalogo import CarrinhoService, CatalogoService
from app.services.pedido import PedidoService

# ---------------------------------------------------------------------
# Repositorios falsos - satisfazem os Protocol sem herdar deles
# ---------------------------------------------------------------------


class UsuariosFake:
    def __init__(self) -> None:
        self.dados: dict[UUID, Usuario] = {}

    def buscar_por_id(self, usuario_id):
        return self.dados.get(usuario_id)

    def buscar_por_email(self, email):
        return next((u for u in self.dados.values() if u.email == email), None)

    def salvar(self, usuario):
        self.dados[usuario.id] = usuario


class CupcakesFake:
    def __init__(self, itens: list[Cupcake]) -> None:
        self.dados = {c.id: c for c in itens}

    def buscar_por_id(self, cupcake_id):
        return self.dados.get(cupcake_id)

    def listar(self, apenas_disponiveis=True):
        itens = list(self.dados.values())
        return [c for c in itens if c.disponivel] if apenas_disponiveis else itens

    def buscar_por_texto(self, termo):
        t = termo.lower()
        return [
            c
            for c in self.dados.values()
            if c.disponivel and (t in c.nome.lower() or t in c.sabor.lower())
        ]


class CarrinhosFake:
    def __init__(self) -> None:
        self.dados: dict[UUID, Carrinho] = {}

    def obter_ou_criar(self, usuario_id):
        return self.dados.setdefault(usuario_id, Carrinho(usuario_id=usuario_id))

    def salvar(self, carrinho):
        self.dados[carrinho.usuario_id] = carrinho

    def limpar(self, usuario_id):
        self.dados[usuario_id] = Carrinho(usuario_id=usuario_id)


class PedidosFake:
    def __init__(self) -> None:
        self.dados: dict[UUID, Pedido] = {}

    def salvar(self, pedido):
        self.dados[pedido.id] = pedido

    def buscar_por_id(self, pedido_id):
        return self.dados.get(pedido_id)

    def listar_por_usuario(self, usuario_id):
        return [p for p in self.dados.values() if p.usuario_id == usuario_id]


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

BAUNILHA = Cupcake(uuid4(), "Baunilha Clássico", "...", "baunilha", Decimal("8.50"), "", True)
CHOCOLATE = Cupcake(uuid4(), "Chocolate Belga", "...", "chocolate", Decimal("10.90"), "", True)
PISTACHE = Cupcake(uuid4(), "Pistache", "...", "pistache", Decimal("14.00"), "", False)


@pytest.fixture
def cupcakes():
    return CupcakesFake([BAUNILHA, CHOCOLATE, PISTACHE])


@pytest.fixture
def usuario_id():
    return uuid4()


# ---------------------------------------------------------------------
# Autenticacao - historias ID 01, 02
# ---------------------------------------------------------------------


def test_cadastro_normaliza_email():
    servico = AutenticacaoService(UsuariosFake())
    usuario = servico.cadastrar("Felipe", "  Felipe@Mail.COM ", "senha-longa-o-bastante")
    assert usuario.email == "felipe@mail.com"


def test_cadastro_nao_guarda_senha_em_texto_puro():
    servico = AutenticacaoService(UsuariosFake())
    usuario = servico.cadastrar("Felipe", "felipe@mail.com", "minha-senha-secreta")
    assert usuario.senha_hash != "minha-senha-secreta"
    assert usuario.senha_hash.startswith("$2")  # prefixo bcrypt


def test_email_duplicado_e_recusado_mesmo_com_caixa_diferente():
    servico = AutenticacaoService(UsuariosFake())
    servico.cadastrar("Felipe", "felipe@mail.com", "senha-longa-o-bastante")
    with pytest.raises(EmailJaCadastradoError):
        servico.cadastrar("Outro", "FELIPE@MAIL.COM", "outra-senha-longa")


def test_rn07_senha_curta_e_recusada():
    servico = AutenticacaoService(UsuariosFake())
    with pytest.raises(SenhaFracaError):
        servico.cadastrar("Felipe", "felipe@mail.com", "curta")


def test_login_com_credenciais_corretas():
    repo = UsuariosFake()
    servico = AutenticacaoService(repo)
    servico.cadastrar("Felipe", "felipe@mail.com", "senha-longa-o-bastante")

    usuario = servico.autenticar("felipe@mail.com", "senha-longa-o-bastante")
    assert usuario.nome == "Felipe"


def test_rn10_email_inexistente_e_senha_errada_dao_o_mesmo_erro():
    """A mensagem nao pode revelar qual dos dois falhou."""
    servico = AutenticacaoService(UsuariosFake())
    servico.cadastrar("Felipe", "felipe@mail.com", "senha-longa-o-bastante")

    with pytest.raises(CredenciaisInvalidasError) as e1:
        servico.autenticar("ninguem@mail.com", "senha-longa-o-bastante")
    with pytest.raises(CredenciaisInvalidasError) as e2:
        servico.autenticar("felipe@mail.com", "senha-errada-qualquer")

    assert str(e1.value) == str(e2.value)


# ---------------------------------------------------------------------
# Catalogo - historia ID 04
# ---------------------------------------------------------------------


def test_catalogo_omite_esgotados(cupcakes):
    assert len(CatalogoService(cupcakes).listar()) == 2


def test_busca_vazia_devolve_catalogo_inteiro(cupcakes):
    assert len(CatalogoService(cupcakes).buscar("   ")) == 2


def test_detalhar_inexistente(cupcakes):
    with pytest.raises(CupcakeNaoEncontradoError):
        CatalogoService(cupcakes).detalhar(uuid4())


# ---------------------------------------------------------------------
# Carrinho - historias ID 05, 06
# ---------------------------------------------------------------------


def test_adicionar_persiste_no_repositorio(cupcakes, usuario_id):
    carrinhos = CarrinhosFake()
    servico = CarrinhoService(carrinhos, cupcakes)

    servico.adicionar_item(usuario_id, BAUNILHA.id, 2)

    assert carrinhos.obter_ou_criar(usuario_id).total == Decimal("17.00")


def test_rn06_adicionar_repetido_soma(cupcakes, usuario_id):
    servico = CarrinhoService(CarrinhosFake(), cupcakes)
    servico.adicionar_item(usuario_id, BAUNILHA.id, 2)
    carrinho = servico.adicionar_item(usuario_id, BAUNILHA.id, 3)

    assert len(carrinho.itens) == 1
    assert carrinho.itens[0].quantidade == 5


def test_rn02_esgotado_nao_entra(cupcakes, usuario_id):
    servico = CarrinhoService(CarrinhosFake(), cupcakes)
    with pytest.raises(CupcakeIndisponivelError):
        servico.adicionar_item(usuario_id, PISTACHE.id)


def test_rn01_quantidade_zero_recusada(cupcakes, usuario_id):
    servico = CarrinhoService(CarrinhosFake(), cupcakes)
    with pytest.raises(QuantidadeInvalidaError):
        servico.adicionar_item(usuario_id, BAUNILHA.id, 0)


def test_cupcake_inexistente(cupcakes, usuario_id):
    servico = CarrinhoService(CarrinhosFake(), cupcakes)
    with pytest.raises(CupcakeNaoEncontradoError):
        servico.adicionar_item(usuario_id, uuid4())


def test_preco_vem_do_repositorio_nao_do_chamador(cupcakes, usuario_id):
    """O cliente nao tem como injetar o proprio preco."""
    servico = CarrinhoService(CarrinhosFake(), cupcakes)
    carrinho = servico.adicionar_item(usuario_id, BAUNILHA.id)
    assert carrinho.itens[0].preco_unitario == Decimal("8.50")


def test_remover_item(cupcakes, usuario_id):
    servico = CarrinhoService(CarrinhosFake(), cupcakes)
    servico.adicionar_item(usuario_id, BAUNILHA.id)
    assert servico.remover_item(usuario_id, BAUNILHA.id).vazio


# ---------------------------------------------------------------------
# Pedido - historias ID 07, 08
# ---------------------------------------------------------------------


@pytest.fixture
def com_carrinho_cheio(cupcakes, usuario_id):
    carrinhos = CarrinhosFake()
    pedidos = PedidosFake()
    CarrinhoService(carrinhos, cupcakes).adicionar_item(usuario_id, BAUNILHA.id, 2)
    return PedidoService(pedidos, carrinhos), carrinhos, pedidos


def test_checkout_cria_pedido_e_esvazia_carrinho(com_carrinho_cheio, usuario_id):
    servico, carrinhos, _ = com_carrinho_cheio

    pedido = servico.finalizar(usuario_id, "Rua das Flores, 123")

    assert pedido.total == Decimal("17.00")
    assert pedido.status is StatusPedido.RECEBIDO
    assert carrinhos.obter_ou_criar(usuario_id).vazio


def test_rn04_checkout_com_carrinho_vazio(cupcakes, usuario_id):
    servico = PedidoService(PedidosFake(), CarrinhosFake())
    with pytest.raises(CarrinhoVazioError):
        servico.finalizar(usuario_id, "Rua das Flores, 123")


def test_idor_pedido_de_outro_usuario_e_invisivel(com_carrinho_cheio, usuario_id):
    """Trocar o id na URL nao da acesso ao pedido alheio."""
    servico, _, _ = com_carrinho_cheio
    pedido = servico.finalizar(usuario_id, "Rua das Flores, 123")

    outro_usuario = uuid4()
    with pytest.raises(PedidoNaoEncontradoError):
        servico.detalhar(pedido.id, outro_usuario)


def test_dono_enxerga_o_proprio_pedido(com_carrinho_cheio, usuario_id):
    servico, _, _ = com_carrinho_cheio
    pedido = servico.finalizar(usuario_id, "Rua das Flores, 123")

    assert servico.detalhar(pedido.id, usuario_id).id == pedido.id


def test_listagem_isola_por_usuario(com_carrinho_cheio, usuario_id):
    servico, _, _ = com_carrinho_cheio
    servico.finalizar(usuario_id, "Rua das Flores, 123")

    assert len(servico.listar_do_usuario(usuario_id)) == 1
    assert servico.listar_do_usuario(uuid4()) == []


def test_rn05_avanco_de_status_respeita_a_fsm(com_carrinho_cheio, usuario_id):
    servico, _, _ = com_carrinho_cheio
    pedido = servico.finalizar(usuario_id, "Rua das Flores, 123")

    servico.avancar_status(pedido.id, StatusPedido.EM_PREPARO)

    with pytest.raises(TransicaoStatusInvalidaError):
        servico.avancar_status(pedido.id, StatusPedido.ENTREGUE)


# ---------------------------------------------------------------------
# Regressao: incompatibilidade passlib x bcrypt >= 4.1
# ---------------------------------------------------------------------


def test_senha_no_limite_de_72_bytes_e_aceita():
    """72 bytes exatos passam - o limite e inclusivo."""
    from app.domain.usuario import LIMITE_BYTES_SENHA

    servico = AutenticacaoService(UsuariosFake())
    senha = "a" * LIMITE_BYTES_SENHA
    usuario = servico.cadastrar("Felipe", "limite@mail.com", senha)

    assert servico.autenticar("limite@mail.com", senha).id == usuario.id


def test_rn07b_senha_acima_de_72_bytes_e_recusada():
    """Antes desta correcao, isto estourava ValueError dentro do bcrypt."""
    from app.domain.errors import SenhaMuitoLongaError

    servico = AutenticacaoService(UsuariosFake())
    with pytest.raises(SenhaMuitoLongaError):
        servico.cadastrar("Felipe", "longa@mail.com", "a" * 73)


def test_limite_conta_bytes_e_nao_caracteres():
    """Acentos ocupam 2 bytes: 40 caracteres acentuados = 80 bytes."""
    from app.domain.errors import SenhaMuitoLongaError

    servico = AutenticacaoService(UsuariosFake())
    senha = "á" * 40  # 40 caracteres, 80 bytes em UTF-8
    assert len(senha) == 40
    assert len(senha.encode("utf-8")) == 80

    with pytest.raises(SenhaMuitoLongaError):
        servico.cadastrar("Felipe", "acento@mail.com", senha)


def test_login_com_senha_gigante_nao_derruba_o_servidor():
    """Entrada invalida e credencial invalida, nao erro 500."""
    servico = AutenticacaoService(UsuariosFake())
    servico.cadastrar("Felipe", "felipe@mail.com", "senha-longa-o-bastante")

    with pytest.raises(CredenciaisInvalidasError):
        servico.autenticar("felipe@mail.com", "x" * 500)
