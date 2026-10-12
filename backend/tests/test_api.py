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
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import NOME_COOKIE
from app.infra.db import Base, get_session
from app.infra.models import CupcakeORM, PedidoORM
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
    # Lista FECHADA de propósito: se alguém acrescentar um campo à
    # resposta sem pensar, este teste quebra e obriga a decisão
    # consciente de expor aquele dado.
    assert set(corpo) == {"id", "nome", "email", "admin"}


def test_usuario_comum_nao_vem_marcado_como_admin(client):
    r = client.post(
        f"{BASE}/auth/registrar",
        json={"nome": "Felipe", "email": "felipe@mail.com", "senha": "senha-longa-o-bastante"},
    )
    assert r.json()["admin"] is False


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


# ---------------------------------------------------------------------
# Gestao pela loja - extensao da historia ID 08 / RF-15
# ---------------------------------------------------------------------

ADMIN = f"{BASE}/admin/pedidos"
EMAIL_LOJA = "loja@doceforma.com"


@pytest.fixture
def loja(client, monkeypatch):
    """SEGUNDO navegador, logado como a loja.

    Um `TestClient` guarda os cookies de UMA sessao. Para simular cliente
    e loja ao mesmo tempo, cada um precisa do seu - exatamente como duas
    pessoas em dois computadores. Os dois falam com o mesmo banco porque
    o override de `get_session` (fixture `client`) vale para o app todo.

    `ADMIN_EMAILS` e trocado so durante o teste: `monkeypatch` desfaz a
    alteracao no fim, e nenhum outro teste herda um admin por acidente.
    """
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "ADMIN_EMAILS", [EMAIL_LOJA])
    with TestClient(app) as navegador_da_loja:
        r = navegador_da_loja.post(
            f"{BASE}/auth/registrar",
            json={"nome": "Doce Forma", "email": EMAIL_LOJA, "senha": "senha-da-loja-123"},
        )
        assert r.status_code == 201
        yield navegador_da_loja


@pytest.fixture
def pedido_id(com_carrinho):
    r = com_carrinho.post(f"{BASE}/pedidos", json={"endereco_entrega": "Rua das Flores, 123"})
    return r.json()["id"]


def test_gestao_exige_autenticacao(client):
    assert client.get(ADMIN).status_code == 401


def test_gestao_recusa_cliente_comum_em_todas_as_rotas(com_carrinho, pedido_id):
    """Prova de que a protecao esta no ROUTER, nao rota a rota."""
    chamadas = [
        ("GET", ADMIN, None),
        ("GET", f"{ADMIN}/{pedido_id}", None),
        ("POST", f"{ADMIN}/{pedido_id}/avancar", None),
        ("POST", f"{ADMIN}/{pedido_id}/cancelar", None),
        ("PATCH", f"{ADMIN}/{pedido_id}", {"endereco_entrega": "Rua Invadida, 1"}),
        ("DELETE", f"{ADMIN}/{pedido_id}", None),
    ]
    for metodo, url, corpo in chamadas:
        r = com_carrinho.request(metodo, url, json=corpo)
        assert r.status_code == 403, f"{metodo} {url} deveria ser 403"
        assert r.json()["detail"]["codigo"] == "acesso_negado"


def test_conta_da_loja_vem_marcada_como_admin(loja):
    assert loja.get(f"{BASE}/auth/eu").json()["admin"] is True


def test_loja_lista_pedido_de_outro_cliente_com_id_e_dono(loja, pedido_id):
    corpo = loja.get(ADMIN).json()

    assert len(corpo) == 1
    assert corpo[0]["id"] == pedido_id
    assert corpo[0]["cliente"] == {"nome": "Felipe", "email": "felipe@mail.com"}
    assert corpo[0]["criado_em"] is not None
    assert corpo[0]["acoes"]["proximo_status"] == "em_preparo"
    assert "itens" not in corpo[0]


def test_rota_do_cliente_continua_isolada_ate_para_a_loja(loja, pedido_id):
    """A loja usa /admin. A rota do cliente nao ganhou excecao para admin."""
    assert loja.get(f"{BASE}/pedidos/{pedido_id}").status_code == 404


def test_loja_detalha_com_itens_e_endereco(loja, pedido_id):
    corpo = loja.get(f"{ADMIN}/{pedido_id}").json()

    assert corpo["endereco_entrega"] == "Rua das Flores, 123"
    assert corpo["itens"][0]["quantidade"] == 2
    assert corpo["total"] == "17.00"


def test_avancar_uma_etapa_e_o_cliente_ve_a_mudanca(loja, com_carrinho, pedido_id):
    r = loja.post(f"{ADMIN}/{pedido_id}/avancar")

    assert r.status_code == 200
    assert r.json()["status"] == "em_preparo"
    assert r.json()["acoes"]["proximo_status"] == "saiu_para_entrega"
    assert com_carrinho.get(f"{BASE}/pedidos/{pedido_id}").json()["status"] == "em_preparo"


def test_rn05_avancar_pedido_entregue_devolve_409(loja, pedido_id):
    for _ in range(3):
        loja.post(f"{ADMIN}/{pedido_id}/avancar")

    r = loja.post(f"{ADMIN}/{pedido_id}/avancar")
    assert r.status_code == 409
    assert r.json()["codigo"] == "transicao_invalida"


def test_corrigir_endereco_reflete_para_o_cliente(loja, com_carrinho, pedido_id):
    r = loja.patch(f"{ADMIN}/{pedido_id}", json={"endereco_entrega": "Avenida Central, 900"})

    assert r.status_code == 200
    detalhe = com_carrinho.get(f"{BASE}/pedidos/{pedido_id}").json()
    assert detalhe["endereco_entrega"] == "Avenida Central, 900"


def test_edicao_ignora_campos_que_nao_sao_o_endereco(loja, pedido_id):
    """Mandar `total` ou `status` no corpo nao altera nada."""
    r = loja.patch(
        f"{ADMIN}/{pedido_id}",
        json={"endereco_entrega": "Avenida Central, 900", "total": "0.01", "status": "entregue"},
    )
    assert r.json()["total"] == "17.00"
    assert r.json()["status"] == "recebido"


def test_rn11_endereco_travado_depois_de_sair_devolve_409(loja, pedido_id):
    loja.post(f"{ADMIN}/{pedido_id}/avancar")
    loja.post(f"{ADMIN}/{pedido_id}/avancar")  # saiu_para_entrega

    r = loja.patch(f"{ADMIN}/{pedido_id}", json={"endereco_entrega": "Avenida Central, 900"})
    assert r.status_code == 409
    assert r.json()["codigo"] == "pedido_nao_editavel"


def test_rn13_excluir_pedido_em_andamento_devolve_409(loja, pedido_id):
    r = loja.delete(f"{ADMIN}/{pedido_id}")
    assert r.status_code == 409
    assert r.json()["codigo"] == "pedido_nao_excluivel"


def test_exclusao_logica_esconde_de_todos_mas_preserva_no_banco(
    loja, com_carrinho, pedido_id, session_factory
):
    loja.post(f"{ADMIN}/{pedido_id}/cancelar")
    assert loja.delete(f"{ADMIN}/{pedido_id}").status_code == 204

    # Sumiu para a loja e para o cliente...
    assert loja.get(ADMIN).json() == []
    assert com_carrinho.get(f"{BASE}/pedidos").json() == []
    assert com_carrinho.get(f"{BASE}/pedidos/{pedido_id}").status_code == 404

    # ...mas a venda continua registrada no banco.
    with session_factory() as s:
        linha = s.get(PedidoORM, UUID(pedido_id))
        assert linha is not None
        assert linha.excluido_em is not None

    # Excluir de novo: o recurso ja nao existe para a API.
    assert loja.delete(f"{ADMIN}/{pedido_id}").status_code == 404


def test_filtro_por_status(loja, pedido_id):
    assert loja.get(ADMIN, params={"status": "em_preparo"}).json() == []
    assert len(loja.get(ADMIN, params={"status": "recebido"}).json()) == 1


def test_filtro_com_status_inexistente_devolve_422(loja):
    assert loja.get(ADMIN, params={"status": "voando"}).status_code == 422


def test_pedido_inexistente_devolve_404_para_a_loja(loja):
    r = loja.post(f"{ADMIN}/{uuid4()}/avancar")
    assert r.status_code == 404
    assert r.json()["codigo"] == "pedido_nao_encontrado"
