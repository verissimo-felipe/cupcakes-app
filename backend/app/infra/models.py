"""Modelos ORM - o formato de TABELA.

Repare no sufixo `ORM` em cada classe. Nao e enfeite: existe um
`Cupcake` no dominio e um `CupcakeORM` aqui, e confundir os dois e o erro
mais comum nesta arquitetura. O sufixo torna o engano visivel na revisao.

POR QUE DUAS CLASSES PARA A MESMA COISA
---------------------------------------
Se o dominio usasse `CupcakeORM` diretamente, ele importaria SQLAlchemy -
e a camada "pura" deixaria de ser pura. Os testes passariam a exigir
banco, e o argumento arquitetural inteiro cairia.

O custo e real: codigo de traducao entre os dois formatos, que fica em
`repositories.py`. O beneficio e testabilidade e independencia.

Django e Rails fazem o oposto (Active Record: um modelo que e tabela E
regra ao mesmo tempo). E menos codigo e funciona bem para CRUD. A escolha
aqui foi deliberada, nao ignorancia da alternativa.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db import Base


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class UsuarioORM(Base):
    __tablename__ = "usuarios"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    # `unique=True` cria indice unico no banco. A checagem no service e
    # conveniencia para dar mensagem boa; a GARANTIA e esta constraint.
    # Sem ela, duas requisicoes simultaneas passariam as duas pela
    # verificacao e criariam contas duplicadas - condicao de corrida
    # classica que so o banco resolve.
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)


class CupcakeORM(Base):
    __tablename__ = "cupcakes"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(Text, default="")
    sabor: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    # Numeric, NUNCA Float. Ponto flutuante binario nao representa 0.10
    # exatamente: em Python, 0.1 + 0.2 == 0.30000000000000004. Somar
    # centenas de itens em float acumula centavos de erro. Numeric(10, 2)
    # e decimal exato, e mapeia para `Decimal` no Python.
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    imagem_url: Mapped[str] = mapped_column(String(500), default="")
    disponivel: Mapped[bool] = mapped_column(default=True)


class ItemCarrinhoORM(Base):
    """Linha do carrinho.

    Nao existe tabela `carrinhos`. O carrinho de um usuario E o conjunto
    de linhas com o `usuario_id` dele - se nao ha linhas, o carrinho esta
    vazio. Uma tabela so para guardar o id do dono seria uma juncao a mais
    sem informacao adicional.
    """

    __tablename__ = "itens_carrinho"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("usuarios.id", ondelete="CASCADE"), index=True
    )
    cupcake_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("cupcakes.id"))
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)


class PedidoORM(Base):
    __tablename__ = "pedidos"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    usuario_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("usuarios.id"), index=True
    )
    endereco_entrega: Mapped[str] = mapped_column(String(300), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="recebido")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    # Exclusao logica. NULL = ativo. Ver `Pedido.excluir` e a migracao 0002.
    excluido_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # `cascade="all, delete-orphan"` faz o SQLAlchemy apagar os itens
    # quando o pedido some. `lazy="selectin"` carrega todos os itens em UMA
    # consulta extra em vez de uma por pedido - e a defesa contra o
    # problema N+1, que so aparece quando a tabela cresce.
    itens: Mapped[list[ItemPedidoORM]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan", lazy="selectin"
    )


class ItemPedidoORM(Base):
    """Linha do pedido.

    Duplica nome e preco do cupcake de proposito. Sao dados HISTORICOS: o
    preco pago naquela compra. Se fosse apenas uma FK para `cupcakes`, um
    reajuste no catalogo mudaria retroativamente o valor de pedidos
    antigos - e a nota fiscal deixaria de bater.
    """

    __tablename__ = "itens_pedido"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pedido_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("pedidos.id", ondelete="CASCADE"), index=True
    )
    cupcake_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)

    pedido: Mapped[PedidoORM] = relationship(back_populates="itens")
