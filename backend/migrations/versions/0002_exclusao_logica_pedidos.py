"""exclusao logica de pedidos

Acrescenta `pedidos.excluido_em`. NULL significa pedido ativo; uma data
significa que a loja o excluiu - mas a linha continua aqui, com itens,
valores e status, para auditoria.

POR QUE ESTA MIGRACAO E SEGURA EM TABELA COM DADOS
--------------------------------------------------
Coluna NULLABLE e SEM default: no PostgreSQL isso e alteracao so de
catalogo, instantanea, sem reescrever a tabela nem travar escrita por
mais que um instante. Todos os pedidos existentes ficam com NULL, isto
e, ativos - exatamente o significado correto.

Se a coluna fosse NOT NULL, a migracao precisaria de um valor para as
linhas antigas e, conforme o default, reescreveria a tabela inteira.

Revision ID: 0002_exclusao_logica_pedidos
Revises: 0001_schema_inicial
Create Date: 2026-10-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_exclusao_logica_pedidos"
down_revision: str | None = "0001_schema_inicial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "pedidos",
        sa.Column("excluido_em", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    # ATENCAO: o downgrade APAGA a informacao de quais pedidos foram
    # excluidos - todos voltam a aparecer como ativos. Reverter e
    # possivel, mas nao e neutro.
    op.drop_column("pedidos", "excluido_em")
