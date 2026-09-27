"""Testes da camada HTTP.

Estes sao os unicos testes que exercitam a pilha INTEIRA: rota, schema,
dependencia, servico, repositorio, banco. Sao tambem os mais lentos -
por isso ficam no topo da piramide, em menor numero.

`app.dependency_overrides` substitui `get_session` por uma sessao SQLite
em memoria. Isso so e possivel porque toda a fiacao mora em `api/deps.py`:
trocar uma funcao troca o banco da aplicacao inteira.

O que estes testes cobrem e que os de servico NAO cobrem:
  - status codes corretos
  - o cookie httpOnly realmente sendo gravado e lido
  - `senha_hash` nao vazando na resposta
  - rotas protegidas recusando quem nao esta logado
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import NOME_COOKIE
from app.infra.db import Base, get_session
from app.infra.models import CupcakeORM
from app.main import app

BASE = "/api/v1"


@pytest.fixture
def session_factory():
    # StaticPool mantem UMA conexao para o banco em memoria; sem ele cada
    # conexao do pool veria um SQLite vazio e diferente.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def cupcakes(session_factory):
    disponivel = CupcakeORM(
        id=uuid4(), nome="Baunilha Clássico", descricao="Massa de baunilha",
        sabor="baunilha", preco=Decimal("8.50"), imagem_url="/img/b.jpg", disponivel=True,
    )
    esgotado = CupcakeORM(
        id=uuid4(), nome="Pistache", descricao="Esgotado",
        sabor="pistache", preco=Decimal("14.00"), imagem_url="/img/p.jpg", disponivel=False,
    )
    with session_factory() as s:
        s.add_all([disponivel, esgotado])
        s.commit()
    return {"disponivel": disponivel, "esgotado": esgotado}


@pytest.fixture
def client(session_factory):
    def _session():
        s: Session = session_factory()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    app.dependency_overrides[get_session] = _session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def logado(client):
    """Cliente autenticado. O TestClient guarda o cookie entre chamadas."""
    r = client.post(
        f"{BASE}/auth/registrar",
        json={"nome": "Felipe", "email": "felipe@mail.com", "senha": "senha-longa-o-bastante"},
    )
    assert r.status_code == 201
    return client


# ---------------------------------------------------------------------
# Infra
# ---------------------------------------------------------------------


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


# ---------------------------------------------------------------------
# Autenticacao - historias ID 01, 02
# ---------------------------------------------------------------------


def test_registro_devolve_201_e_grava_cookie(client):
    r = client.post(
        f"{BASE}/auth/registrar",
        json={"nome": "Felipe", "email": "felipe@mail.com", "senha": "senha-longa-o-bastante"},
    )
    assert r.status_code == 201
    assert NOME_COOKIE in r.cookies


def test_resposta_nunca_expoe_o_hash_da_senha(client):
    r = client.post(
        f"{BASE}/auth/registrar",
        json={"nome": "Felipe", "email": "felipe@mail.com", "senha": "senha-longa-o-bastante"},
    )
    corpo = r.json()
    assert "senha_hash" not in corpo
    assert "senha" not in corpo
    assert set(corpo) == {"id", "nome", "email"}


def test_cookie_e_httponly(client):
    r = client.post(
        f"{BASE}/auth/registrar",
        json={"nome": "Felipe", "email": "felipe@mail.com", "senha": "senha-longa-o-bastante"},
    )
    set_cookie = r.headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie


def test_rn09_email_duplicado_devolve_409(client):
    dados = {"nome": "Felipe", "email": "felipe@mail.com", "senha": "senha-longa-o-bastante"}
    client.post(f"{BASE}/auth/registrar", json=dados)
    r = client.post(f"{BASE}/auth/registrar", json=dados)

    assert r.status_code == 409
    assert r.json()["codigo"] == "email_ja_cadastrado"


def test_rn07_senha_curta_devolve_422(client):
    r = client.post(
        f"{BASE}/auth/registrar",
        json={"nome": "Felipe", "email": "felipe@mail.com", "senha": "curta"},
    )
    assert r.status_code == 422
    assert r.json()["codigo"] == "senha_fraca"


def test_email_malformado_barrado_pelo_pydantic(client):
    r = client.post(
        f"{BASE}/auth/registrar",
        json={"nome": "Felipe", "email": "nao-e-email", "senha": "senha-longa-o-bastante"},
    )
    assert r.status_code == 422


def test_rn10_login_errado_devolve_401(logado):
    r = logado.post(
        f"{BASE}/auth/login",
        json={"email": "felipe@mail.com", "senha": "senha-errada-qualquer"},
    )
    assert r.status_code == 401
    assert r.json()["codigo"] == "credenciais_invalidas"


def test_eu_exige_autenticacao(client):
    assert client.get(f"{BASE}/auth/eu").status_code == 401


def test_eu_devolve_o_usuario_logado(logado):
    r = logado.get(f"{BASE}/auth/eu")
    assert r.status_code == 200
    assert r.json()["email"] == "felipe@mail.com"


def test_logout_encerra_a_sessao(logado):
    assert logado.post(f"{BASE}/auth/logout").status_code == 204
    assert logado.get(f"{BASE}/auth/eu").status_code == 401


# ---------------------------------------------------------------------
# Catalogo - historia ID 04
# ---------------------------------------------------------------------


def test_catalogo_e_publico(client, cupcakes):
    r = client.get(f"{BASE}/cupcakes")
    assert r.status_code == 200
    assert len(r.json()) == 1  # o esgotado nao aparece


def test_busca_na_mesma_rota(client, cupcakes):
    assert len(client.get(f"{BASE}/cupcakes", params={"busca": "baunilha"}).json()) == 1
    assert client.get(f"{BASE}/cupcakes", params={"busca": "inexistente"}).json() == []


def test_detalhar_inexistente_devolve_404(client, cupcakes):
    r = client.get(f"{BASE}/cupcakes/{uuid4()}")
    assert r.status_code == 404
    assert r.json()["codigo"] == "cupcake_nao_encontrado"


def test_id_invalido_devolve_422(client):
    assert client.get(f"{BASE}/cupcakes/nao-e-uuid").status_code == 422


# ---------------------------------------------------------------------
# Carrinho - historias ID 05, 06
# ---------------------------------------------------------------------


def test_carrinho_exige_autenticacao(client):
    assert client.get(f"{BASE}/carrinho").status_code == 401


def test_adicionar_devolve_carrinho_completo(logado, cupcakes):
    r = logado.post(
        f"{BASE}/carrinho/itens",
        json={"cupcake_id": str(cupcakes["disponivel"].id), "quantidade": 2},
    )
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["total"] == "17.00"
    assert corpo["quantidade_itens"] == 2
    assert corpo["itens"][0]["subtotal"] == "17.00"


def test_rn06_repetido_soma(logado, cupcakes):
    dados = {"cupcake_id": str(cupcakes["disponivel"].id), "quantidade": 2}
    logado.post(f"{BASE}/carrinho/itens", json=dados)
    r = logado.post(f"{BASE}/carrinho/itens", json=dados)

    assert len(r.json()["itens"]) == 1
    assert r.json()["quantidade_itens"] == 4


def test_rn02_esgotado_devolve_409(logado, cupcakes):
    r = logado.post(
        f"{BASE}/carrinho/itens",
        json={"cupcake_id": str(cupcakes["esgotado"].id), "quantidade": 1},
    )
    assert r.status_code == 409
    assert r.json()["codigo"] == "cupcake_indisponivel"


def test_rn01_quantidade_zero_barrada_pelo_pydantic(logado, cupcakes):
    r = logado.post(
        f"{BASE}/carrinho/itens",
        json={"cupcake_id": str(cupcakes["disponivel"].id), "quantidade": 0},
    )
    assert r.status_code == 422


def test_remover_item(logado, cupcakes):
    cid = str(cupcakes["disponivel"].id)
    logado.post(f"{BASE}/carrinho/itens", json={"cupcake_id": cid, "quantidade": 1})
    r = logado.delete(f"{BASE}/carrinho/itens/{cid}")

    assert r.status_code == 200
    assert r.json()["itens"] == []


def test_carrinho_e_isolado_por_usuario(client, logado, cupcakes):
    logado.post(
        f"{BASE}/carrinho/itens",
        json={"cupcake_id": str(cupcakes["disponivel"].id), "quantidade": 3},
    )
    logado.post(f"{BASE}/auth/logout")
    logado.post(
        f"{BASE}/auth/registrar",
        json={"nome": "Outro", "email": "outro@mail.com", "senha": "senha-longa-o-bastante"},
    )

    assert logado.get(f"{BASE}/carrinho").json()["itens"] == []


# ---------------------------------------------------------------------
# Pedido - historias ID 07, 08
# ---------------------------------------------------------------------


@pytest.fixture
def com_carrinho(logado, cupcakes):
    logado.post(
        f"{BASE}/carrinho/itens",
        json={"cupcake_id": str(cupcakes["disponivel"].id), "quantidade": 2},
    )
    return logado


def test_checkout_cria_pedido_e_esvazia_carrinho(com_carrinho):
    r = com_carrinho.post(f"{BASE}/pedidos", json={"endereco_entrega": "Rua das Flores, 123"})

    assert r.status_code == 201
    assert r.json()["status"] == "recebido"
    assert r.json()["total"] == "17.00"
    assert com_carrinho.get(f"{BASE}/carrinho").json()["itens"] == []


def test_rn04_checkout_vazio_devolve_422(logado):
    r = logado.post(f"{BASE}/pedidos", json={"endereco_entrega": "Rua das Flores, 123"})
    assert r.status_code == 422
    assert r.json()["codigo"] == "carrinho_vazio"


def test_listagem_traz_resumo_sem_itens(com_carrinho):
    com_carrinho.post(f"{BASE}/pedidos", json={"endereco_entrega": "Rua das Flores, 123"})
    corpo = com_carrinho.get(f"{BASE}/pedidos").json()

    assert len(corpo) == 1
    assert "itens" not in corpo[0]
    assert corpo[0]["quantidade_itens"] == 2


def test_idor_pedido_alheio_devolve_404(com_carrinho):
    """404, nao 403 - 403 confirmaria que o id existe."""
    pedido_id = com_carrinho.post(
        f"{BASE}/pedidos", json={"endereco_entrega": "Rua das Flores, 123"}
    ).json()["id"]

    com_carrinho.post(f"{BASE}/auth/logout")
    com_carrinho.post(
        f"{BASE}/auth/registrar",
        json={"nome": "Bisbilhoteiro", "email": "outro@mail.com", "senha": "senha-longa-o-bastante"},
    )

    r = com_carrinho.get(f"{BASE}/pedidos/{pedido_id}")
    assert r.status_code == 404


def test_mudar_status_exige_admin(com_carrinho):
    pedido_id = com_carrinho.post(
        f"{BASE}/pedidos", json={"endereco_entrega": "Rua das Flores, 123"}
    ).json()["id"]

    r = com_carrinho.patch(f"{BASE}/pedidos/{pedido_id}/status", json={"status": "em_preparo"})
    assert r.status_code == 403
    assert r.json()["detail"]["codigo"] == "acesso_negado"
