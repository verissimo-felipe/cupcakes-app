"""schema inicial

Cria as cinco tabelas do sistema, na ordem exigida pelas chaves
estrangeiras: primeiro as independentes (usuarios, cupcakes), depois as
que as referenciam.

O `downgrade` derruba na ordem inversa. Migracao sem downgrade testavel e
migracao que voce nao consegue reverter as tres da manha.

Revision ID: 0001_schema_inicial
Revises:
Create Date: 2026-09-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_schema_inicial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        # Constraint UNICA no banco, nao apenas checagem no service.
        # Duas requisicoes simultaneas passariam as duas pela verificacao
        # em Python e criariam contas duplicadas. So o banco resolve essa
        # condicao de corrida.
        sa.UniqueConstraint("email", name="uq_usuarios_email"),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"])

    op.create_table(
        "cupcakes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("sabor", sa.String(length=60), nullable=False),
        # Numeric(10, 2) e decimal EXATO. Float acumularia erro de
        # arredondamento ao somar itens - ver test_preco_nao_perde_precisao.
        sa.Column("preco", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("imagem_url", sa.String(length=500), nullable=False),
        sa.Column("disponivel", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    # Indices em nome e sabor: sao as colunas do `ilike` da busca (RNF-04).
    op.create_index("ix_cupcakes_nome", "cupcakes", ["nome"])
    op.create_index("ix_cupcakes_sabor", "cupcakes", ["sabor"])

    op.create_table(
        "itens_carrinho",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("cupcake_id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("preco_unitario", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        # CASCADE: apagar o usuario leva junto o carrinho dele. Sem isso,
        # sobrariam linhas orfas apontando para um id inexistente.
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cupcake_id"], ["cupcakes.id"]),
    )
    op.create_index("ix_itens_carrinho_usuario_id", "itens_carrinho", ["usuario_id"])

    op.create_table(
        "pedidos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("endereco_entrega", sa.String(length=300), nullable=False),
        sa.Column("total", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        # SEM cascade aqui, de proposito: pedido e registro fiscal. Apagar
        # um usuario nao pode evaporar o historico de vendas da loja.
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
    )
    op.create_index("ix_pedidos_usuario_id", "pedidos", ["usuario_id"])

    op.create_table(
        "itens_pedido",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pedido_id", sa.Uuid(), nullable=False),
        # Sem FK para `cupcakes`: se o produto sair do catalogo, o item do
        # pedido antigo continua valido. Nome e preco estao copiados
        # abaixo justamente para o historico sobreviver ao catalogo.
        sa.Column("cupcake_id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("preco_unitario", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedidos.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_itens_pedido_pedido_id", "itens_pedido", ["pedido_id"])


def downgrade() -> None:
    op.drop_table("itens_pedido")
    op.drop_table("pedidos")
    op.drop_table("itens_carrinho")
    op.drop_table("cupcakes")
    op.drop_table("usuarios")
