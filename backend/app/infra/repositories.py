"""Implementacoes concretas dos repositorios.

Cada classe aqui satisfaz um Protocol de `domain/repositories.py` sem
herdar dele - subtipagem estrutural. O mypy confere; o runtime nem
precisa saber que o contrato existe.

Toda funcao `_para_dominio` e um TRADUTOR: recebe o formato de tabela e
devolve o formato de negocio. E o preco da separacao entre as duas
camadas, concentrado num lugar so.
"""

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import Select, delete, or_, select
from sqlalchemy.orm import Session

from app.domain.entities import Carrinho, Cupcake, ItemCarrinho, Pedido, StatusPedido
from app.domain.usuario import Usuario
from app.infra.models import (
    CupcakeORM,
    ItemCarrinhoORM,
    ItemPedidoORM,
    PedidoORM,
    UsuarioORM,
)

# ---------------------------------------------------------------------
# Tradutores ORM -> dominio
# ---------------------------------------------------------------------


def _cupcake_para_dominio(linha: CupcakeORM) -> Cupcake:
    return Cupcake(
        id=linha.id,
        nome=linha.nome,
        descricao=linha.descricao,
        sabor=linha.sabor,
        preco=linha.preco,
        imagem_url=linha.imagem_url,
        disponivel=linha.disponivel,
    )


def _usuario_para_dominio(linha: UsuarioORM) -> Usuario:
    return Usuario(
        id=linha.id,
        nome=linha.nome,
        email=linha.email,
        senha_hash=linha.senha_hash,
    )


def _item_para_dominio(linha: ItemCarrinhoORM | ItemPedidoORM) -> ItemCarrinho:
    return ItemCarrinho(
        cupcake_id=linha.cupcake_id,
        nome=linha.nome,
        preco_unitario=linha.preco_unitario,
        quantidade=linha.quantidade,
    )


# ---------------------------------------------------------------------
# Repositorios
# ---------------------------------------------------------------------


class CupcakeRepositorySQL:
    """Satisfaz `CupcakeRepository`. Historia ID 04."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def buscar_por_id(self, cupcake_id: UUID) -> Cupcake | None:
        linha = self._session.get(CupcakeORM, cupcake_id)
        return _cupcake_para_dominio(linha) if linha else None

    def listar(self, apenas_disponiveis: bool = True) -> list[Cupcake]:
        stmt = select(CupcakeORM)
        if apenas_disponiveis:
            stmt = stmt.where(CupcakeORM.disponivel.is_(True))
        stmt = stmt.order_by(CupcakeORM.nome)
        return [_cupcake_para_dominio(l) for l in self._session.scalars(stmt)]

    def buscar_por_texto(self, termo: str) -> list[Cupcake]:
        """Busca por nome ou sabor. RNF-04 - resposta em ate 1 segundo.

        `ilike` com parametro vinculado: o valor viaja separado da query,
        entao aspas ou `OR 1=1` dentro de `termo` sao tratados como texto,
        nunca como SQL. Montar a mesma consulta com f-string seria a
        vulnerabilidade de injecao classica.

        Para o volume deste catalogo, `ilike` com indice resolve em
        milissegundos. Se o catalogo crescesse a dezenas de milhares de
        itens, o passo seguinte seria `tsvector` + indice GIN - e so
        entao Elasticsearch.
        """
        padrao = f"%{termo.strip()}%"
        stmt = (
            select(CupcakeORM)
            .where(CupcakeORM.disponivel.is_(True))
            .where(or_(CupcakeORM.nome.ilike(padrao), CupcakeORM.sabor.ilike(padrao)))
            .order_by(CupcakeORM.nome)
        )
        return [_cupcake_para_dominio(l) for l in self._session.scalars(stmt)]


class UsuarioRepositorySQL:
    """Satisfaz `UsuarioRepository`. Historias ID 01, 02."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def buscar_por_id(self, usuario_id: UUID) -> Usuario | None:
        linha = self._session.get(UsuarioORM, usuario_id)
        return _usuario_para_dominio(linha) if linha else None

    def buscar_por_email(self, email: str) -> Usuario | None:
        stmt = select(UsuarioORM).where(UsuarioORM.email == email)
        linha = self._session.scalars(stmt).first()
        return _usuario_para_dominio(linha) if linha else None

    def buscar_por_ids(self, ids: Iterable[UUID]) -> dict[UUID, Usuario]:
        """UMA consulta com `IN (...)`, qualquer que seja a quantidade.

        A alternativa ingenua - `buscar_por_id` dentro de um laco - e o
        problema N+1: 50 pedidos na tela da loja virariam 50 consultas so
        para descobrir o nome de cada cliente.
        """
        alvos = set(ids)
        if not alvos:
            return {}
        stmt = select(UsuarioORM).where(UsuarioORM.id.in_(alvos))
        return {l.id: _usuario_para_dominio(l) for l in self._session.scalars(stmt)}

    def salvar(self, usuario: Usuario) -> None:
        linha = self._session.get(UsuarioORM, usuario.id)
        if linha is None:
            linha = UsuarioORM(id=usuario.id)
            self._session.add(linha)
        linha.nome = usuario.nome
        linha.email = usuario.email
        linha.senha_hash = usuario.senha_hash
        self._session.flush()


class CarrinhoRepositorySQL:
    """Satisfaz `CarrinhoRepository`. Historias ID 05, 06."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def obter_ou_criar(self, usuario_id: UUID) -> Carrinho:
        stmt = select(ItemCarrinhoORM).where(ItemCarrinhoORM.usuario_id == usuario_id)
        itens = [_item_para_dominio(l) for l in self._session.scalars(stmt)]
        return Carrinho(usuario_id=usuario_id, itens=itens)

    def salvar(self, carrinho: Carrinho) -> None:
        """Apaga as linhas do usuario e regrava.

        Parece desperdicio, e para uma tabela grande seria. Aqui e a opcao
        certa: o carrinho e um AGREGADO pequeno (poucas linhas) e precisa
        ser persistido como unidade. Fazer diff item a item - quais
        sumiram, quais mudaram de quantidade - introduziria estados
        intermediarios invalidos se a request falhasse no meio.

        Como tudo roda dentro da transacao aberta por `get_session`, o
        delete e o insert sao atomicos: ninguem enxerga o carrinho vazio
        no intervalo.
        """
        self._session.execute(
            delete(ItemCarrinhoORM).where(ItemCarrinhoORM.usuario_id == carrinho.usuario_id)
        )
        for item in carrinho.itens:
            self._session.add(
                ItemCarrinhoORM(
                    usuario_id=carrinho.usuario_id,
                    cupcake_id=item.cupcake_id,
                    nome=item.nome,
                    preco_unitario=item.preco_unitario,
                    quantidade=item.quantidade,
                )
            )
        self._session.flush()

    def limpar(self, usuario_id: UUID) -> None:
        """Chamado apos o checkout. Historia ID 07."""
        self._session.execute(
            delete(ItemCarrinhoORM).where(ItemCarrinhoORM.usuario_id == usuario_id)
        )
        self._session.flush()


class PedidoRepositorySQL:
    """Satisfaz `PedidoRepository`. Historias ID 07, 08."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def salvar(self, pedido: Pedido) -> None:
        linha = self._session.get(PedidoORM, pedido.id)
        if linha is None:
            linha = PedidoORM(id=pedido.id, usuario_id=pedido.usuario_id)
            if pedido.criado_em is not None:
                linha.criado_em = pedido.criado_em
            self._session.add(linha)
            # Itens so sao gravados na criacao. Pedido fechado nao muda de
            # composicao - so de status. Regravar itens em cada mudanca de
            # status abriria porta para adulterar historico.
            for item in pedido.itens:
                linha.itens.append(
                    ItemPedidoORM(
                        cupcake_id=item.cupcake_id,
                        nome=item.nome,
                        preco_unitario=item.preco_unitario,
                        quantidade=item.quantidade,
                    )
                )
        linha.endereco_entrega = pedido.endereco_entrega
        linha.total = pedido.total
        linha.status = pedido.status.value
        linha.excluido_em = pedido.excluido_em
        self._session.flush()

    def buscar_por_id(self, pedido_id: UUID) -> Pedido | None:
        linha = self._session.get(PedidoORM, pedido_id)
        if linha is None or linha.excluido_em is not None:
            return None
        return self._para_dominio(linha)

    def listar_por_usuario(self, usuario_id: UUID) -> list[Pedido]:
        stmt = (
            self._ativos()
            .where(PedidoORM.usuario_id == usuario_id)
            .order_by(PedidoORM.criado_em.desc())
        )
        return [self._para_dominio(l) for l in self._session.scalars(stmt)]

    def listar_todos(self, status: StatusPedido | None = None) -> list[Pedido]:
        """Visao da loja. Sem filtro de usuario - por isso so e chamado por
        `GestaoPedidosService`, que so e alcancavel por rota de admin."""
        stmt = self._ativos()
        if status is not None:
            stmt = stmt.where(PedidoORM.status == status.value)
        stmt = stmt.order_by(PedidoORM.criado_em.desc())
        return [self._para_dominio(l) for l in self._session.scalars(stmt)]

    @staticmethod
    def _ativos() -> Select[tuple[PedidoORM]]:
        """Ponto de partida de TODA consulta de leitura de pedidos.

        O risco classico da exclusao logica e esquecer o filtro em uma
        consulta nova: o pedido "excluido" reaparece numa tela qualquer.
        Concentrar o `WHERE excluido_em IS NULL` aqui reduz esse risco a
        lembrar de partir de `_ativos()` em vez de `select(PedidoORM)`.

        Em escala maior, a garantia sobe de nivel: um filtro global do
        ORM (`with_loader_criteria`) ou uma VIEW no banco com RLS
        (Row-Level Security), para que nem SQL escrito a mao enxergue os
        excluidos.
        """
        return select(PedidoORM).where(PedidoORM.excluido_em.is_(None))

    @staticmethod
    def _para_dominio(linha: PedidoORM) -> Pedido:
        return Pedido(
            id=linha.id,
            usuario_id=linha.usuario_id,
            itens=[_item_para_dominio(i) for i in linha.itens],
            endereco_entrega=linha.endereco_entrega,
            total=linha.total,
            status=StatusPedido(linha.status),
            criado_em=linha.criado_em,
            excluido_em=linha.excluido_em,
        )
