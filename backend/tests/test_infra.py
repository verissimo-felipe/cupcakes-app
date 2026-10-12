"""Testes da camada de persistencia.

Diferente de `test_dominio.py`, estes testes PRECISAM de banco - e correto
que precisem: o objetivo aqui e justamente verificar a traducao entre
tabela e entidade.

Usam SQLite em memoria em vez de PostgreSQL. Isso e possivel porque
`models.py` usa `sqlalchemy.Uuid` (agnostico de dialeto) em vez do tipo
UUID especifico do Postgres. Consequencia pratica: a suite roda no CI sem
subir container.

Limite honesto desta escolha: SQLite nao reproduz tudo do Postgres
(comportamento de `ilike` com acentos, constraints deferidas, tipos
nativos). Para o que testamos aqui - round-trip de entidades - e
suficiente. Testes que dependam de comportamento especifico do Postgres
precisariam do banco real.
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.domain.entities import Carrinho, Pedido, StatusPedido
from app.domain.usuario import Usuario
from app.infra.db import Base
from app.infra.models import CupcakeORM
from app.infra.repositories import (
    CarrinhoRepositorySQL,
    CupcakeRepositorySQL,
    PedidoRepositorySQL,
    UsuarioRepositorySQL,
)


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def usuario(session) -> Usuario:
    u = Usuario(id=uuid4(), nome="Felipe", email="felipe@mail.com", senha_hash="hash-fake")
    UsuarioRepositorySQL(session).salvar(u)
    return u


@pytest.fixture
def cupcakes(session):
    linhas = [
        CupcakeORM(
            id=uuid4(),
            nome="Cupcake de Baunilha",
            descricao="Massa de baunilha",
            sabor="baunilha",
            preco=Decimal("8.50"),
            imagem_url="/img/baunilha.jpg",
            disponivel=True,
        ),
        CupcakeORM(
            id=uuid4(),
            nome="Cupcake de Chocolate",
            descricao="Massa de cacau",
            sabor="chocolate",
            preco=Decimal("9.00"),
            imagem_url="/img/chocolate.jpg",
            disponivel=True,
        ),
        CupcakeORM(
            id=uuid4(),
            nome="Cupcake de Limao",
            descricao="Esgotado",
            sabor="limao",
            preco=Decimal("8.00"),
            imagem_url="/img/limao.jpg",
            disponivel=False,
        ),
    ]
    session.add_all(linhas)
    session.flush()
    return linhas


# ---------------------------------------------------------------------
# Catalogo - historia ID 04
# ---------------------------------------------------------------------


def test_listar_omite_indisponiveis(session, cupcakes):
    repo = CupcakeRepositorySQL(session)
    assert len(repo.listar()) == 2
    assert len(repo.listar(apenas_disponiveis=False)) == 3


def test_repositorio_devolve_entidade_de_dominio(session, cupcakes):
    """O que sai do repositorio e `Cupcake`, nao `CupcakeORM`."""
    from app.domain.entities import Cupcake

    resultado = CupcakeRepositorySQL(session).listar()[0]
    assert isinstance(resultado, Cupcake)
    assert isinstance(resultado.preco, Decimal)


def test_preco_nao_perde_precisao(session, cupcakes):
    """Numeric, nao Float: 8.50 volta exatamente 8.50."""
    repo = CupcakeRepositorySQL(session)
    baunilha = next(c for c in repo.listar() if "Baunilha" in c.nome)
    assert baunilha.preco == Decimal("8.50")


def test_busca_por_texto_encontra_por_sabor(session, cupcakes):
    assert len(CupcakeRepositorySQL(session).buscar_por_texto("chocolate")) == 1


def test_busca_por_texto_ignora_indisponivel(session, cupcakes):
    assert CupcakeRepositorySQL(session).buscar_por_texto("limao") == []


def test_busca_com_aspas_nao_quebra_a_query(session, cupcakes):
    """Parametro vinculado: o texto viaja separado do SQL."""
    assert CupcakeRepositorySQL(session).buscar_por_texto("' OR 1=1 --") == []


# ---------------------------------------------------------------------
# Usuario - historias ID 01, 02
# ---------------------------------------------------------------------


def test_buscar_por_email(session, usuario):
    encontrado = UsuarioRepositorySQL(session).buscar_por_email("felipe@mail.com")
    assert encontrado is not None
    assert encontrado.nome == "Felipe"


def test_email_inexistente_devolve_none(session, usuario):
    assert UsuarioRepositorySQL(session).buscar_por_email("ninguem@mail.com") is None


# ---------------------------------------------------------------------
# Carrinho - historias ID 05, 06
# ---------------------------------------------------------------------


def test_carrinho_novo_vem_vazio(session, usuario):
    carrinho = CarrinhoRepositorySQL(session).obter_ou_criar(usuario.id)
    assert carrinho.vazio


def test_round_trip_do_carrinho(session, usuario, cupcakes):
    repo_cupcake = CupcakeRepositorySQL(session)
    repo_carrinho = CarrinhoRepositorySQL(session)

    carrinho = Carrinho(usuario_id=usuario.id)
    carrinho.adicionar(repo_cupcake.buscar_por_id(cupcakes[0].id), quantidade=2)
    carrinho.adicionar(repo_cupcake.buscar_por_id(cupcakes[1].id), quantidade=1)
    repo_carrinho.salvar(carrinho)

    recarregado = repo_carrinho.obter_ou_criar(usuario.id)
    assert len(recarregado.itens) == 2
    assert recarregado.total == Decimal("26.00")


def test_salvar_substitui_em_vez_de_acumular(session, usuario, cupcakes):
    """Regravar o mesmo carrinho nao duplica linhas."""
    repo_cupcake = CupcakeRepositorySQL(session)
    repo_carrinho = CarrinhoRepositorySQL(session)

    carrinho = Carrinho(usuario_id=usuario.id)
    carrinho.adicionar(repo_cupcake.buscar_por_id(cupcakes[0].id))
    repo_carrinho.salvar(carrinho)
    repo_carrinho.salvar(carrinho)

    assert len(repo_carrinho.obter_ou_criar(usuario.id).itens) == 1


def test_limpar_esvazia_o_carrinho(session, usuario, cupcakes):
    repo_carrinho = CarrinhoRepositorySQL(session)
    carrinho = Carrinho(usuario_id=usuario.id)
    carrinho.adicionar(CupcakeRepositorySQL(session).buscar_por_id(cupcakes[0].id))
    repo_carrinho.salvar(carrinho)

    repo_carrinho.limpar(usuario.id)

    assert repo_carrinho.obter_ou_criar(usuario.id).vazio


# ---------------------------------------------------------------------
# Pedido - historias ID 07, 08
# ---------------------------------------------------------------------


def test_round_trip_do_pedido(session, usuario, cupcakes):
    carrinho = Carrinho(usuario_id=usuario.id)
    carrinho.adicionar(CupcakeRepositorySQL(session).buscar_por_id(cupcakes[0].id), 3)
    pedido = Pedido.a_partir_do_carrinho(carrinho, "Rua das Flores, 123")

    repo = PedidoRepositorySQL(session)
    repo.salvar(pedido)

    recarregado = repo.buscar_por_id(pedido.id)
    assert recarregado is not None
    assert recarregado.total == Decimal("25.50")
    assert recarregado.status is StatusPedido.RECEBIDO
    assert len(recarregado.itens) == 1


def test_mudanca_de_status_persiste(session, usuario, cupcakes):
    carrinho = Carrinho(usuario_id=usuario.id)
    carrinho.adicionar(CupcakeRepositorySQL(session).buscar_por_id(cupcakes[0].id))
    pedido = Pedido.a_partir_do_carrinho(carrinho, "Rua das Flores, 123")

    repo = PedidoRepositorySQL(session)
    repo.salvar(pedido)
    pedido.mudar_status(StatusPedido.EM_PREPARO)
    repo.salvar(pedido)

    assert repo.buscar_por_id(pedido.id).status is StatusPedido.EM_PREPARO


def test_preco_do_pedido_nao_muda_com_reajuste_no_catalogo(session, usuario, cupcakes):
    """O preco no pedido e fato historico."""
    carrinho = Carrinho(usuario_id=usuario.id)
    carrinho.adicionar(CupcakeRepositorySQL(session).buscar_por_id(cupcakes[0].id), 2)
    pedido = Pedido.a_partir_do_carrinho(carrinho, "Rua das Flores, 123")
    PedidoRepositorySQL(session).salvar(pedido)

    cupcakes[0].preco = Decimal("99.00")
    session.flush()

    recarregado = PedidoRepositorySQL(session).buscar_por_id(pedido.id)
    assert recarregado.total == Decimal("17.00")
    assert recarregado.itens[0].preco_unitario == Decimal("8.50")


# ---------------------------------------------------------------------
# Gestao pela loja - extensao da historia ID 08 / RF-15
# ---------------------------------------------------------------------


def _pedido_de(session, usuario, cupcake_orm, quantidade=1) -> Pedido:
    carrinho = Carrinho(usuario_id=usuario.id)
    carrinho.adicionar(CupcakeRepositorySQL(session).buscar_por_id(cupcake_orm.id), quantidade)
    pedido = Pedido.a_partir_do_carrinho(carrinho, "Rua das Flores, 123")
    PedidoRepositorySQL(session).salvar(pedido)
    return pedido


def test_exclusao_logica_some_das_consultas_mas_fica_no_banco(session, usuario, cupcakes):
    """O coracao da exclusao logica, verificado contra o banco."""
    from app.infra.models import PedidoORM

    repo = PedidoRepositorySQL(session)
    pedido = _pedido_de(session, usuario, cupcakes[0])
    pedido.cancelar()
    pedido.excluir()
    repo.salvar(pedido)

    # Para a aplicacao, nao existe mais...
    assert repo.buscar_por_id(pedido.id) is None
    assert repo.listar_por_usuario(usuario.id) == []
    assert repo.listar_todos() == []

    # ...mas a linha continua la, com itens, para auditoria.
    linha = session.get(PedidoORM, pedido.id)
    assert linha is not None
    assert linha.excluido_em is not None
    assert len(linha.itens) == 1


def test_listar_todos_traz_pedidos_de_todos_os_clientes(session, usuario, cupcakes):
    outro = Usuario(id=uuid4(), nome="Ana", email="ana@mail.com", senha_hash="hash-fake")
    UsuarioRepositorySQL(session).salvar(outro)

    _pedido_de(session, usuario, cupcakes[0])
    _pedido_de(session, outro, cupcakes[1])

    assert len(PedidoRepositorySQL(session).listar_todos()) == 2


def test_listar_todos_filtra_por_status(session, usuario, cupcakes):
    repo = PedidoRepositorySQL(session)
    _pedido_de(session, usuario, cupcakes[0])
    em_preparo = _pedido_de(session, usuario, cupcakes[1])
    em_preparo.avancar()
    repo.salvar(em_preparo)

    resultado = repo.listar_todos(StatusPedido.EM_PREPARO)
    assert [p.id for p in resultado] == [em_preparo.id]


def test_listar_todos_ordena_do_mais_recente(session, usuario, cupcakes):
    from datetime import datetime, timezone

    repo = PedidoRepositorySQL(session)
    antigo = _pedido_de(session, usuario, cupcakes[0])
    recente = _pedido_de(session, usuario, cupcakes[1])

    # Datas explicitas: dois pedidos criados no mesmo milissegundo
    # empatariam, e o teste passaria ou falharia por sorte.
    from app.infra.models import PedidoORM

    session.get(PedidoORM, antigo.id).criado_em = datetime(2026, 10, 1, tzinfo=timezone.utc)
    session.get(PedidoORM, recente.id).criado_em = datetime(2026, 10, 2, tzinfo=timezone.utc)
    session.flush()

    assert [p.id for p in repo.listar_todos()] == [recente.id, antigo.id]


def test_alteracao_de_endereco_persiste(session, usuario, cupcakes):
    repo = PedidoRepositorySQL(session)
    pedido = _pedido_de(session, usuario, cupcakes[0])
    pedido.alterar_endereco("Avenida Central, 900")
    repo.salvar(pedido)

    assert repo.buscar_por_id(pedido.id).endereco_entrega == "Avenida Central, 900"


def test_buscar_varios_usuarios_numa_consulta(session, usuario):
    outro = Usuario(id=uuid4(), nome="Ana", email="ana@mail.com", senha_hash="hash-fake")
    repo = UsuarioRepositorySQL(session)
    repo.salvar(outro)

    encontrados = repo.buscar_por_ids([usuario.id, outro.id, uuid4()])

    assert set(encontrados) == {usuario.id, outro.id}  # o id inexistente some
    assert repo.buscar_por_ids([]) == {}
