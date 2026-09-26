"""Carga inicial do catalogo.

Rodar:
    docker compose exec backend python -m app.infra.seed

IDEMPOTENTE: pode rodar quantas vezes quiser. Cupcakes ja existentes (por
nome) sao ignorados. Isso importa mais do que parece - script de carga que
duplica dados a cada execucao vira armadilha no dia da gravacao do video.

Um dos itens entra com `disponivel=False` DE PROPOSITO: e ele que permite
demonstrar, na interface, o tratamento do erro `CupcakeIndisponivelError`
exigido pelo enunciado. Sem um produto esgotado no banco, o caminho de
erro nao tem como ser filmado.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infra.db import SessionLocal
from app.infra.models import CupcakeORM

CATALOGO_INICIAL: list[dict] = [
    {
        "nome": "Baunilha Clássico",
        "descricao": "Massa de baunilha Bourbon com buttercream aveludado e granulado de açúcar.",
        "sabor": "baunilha",
        "preco": Decimal("8.50"),
        "imagem_url": "/images/cupcakes/baunilha.jpg",
        "disponivel": True,
    },
    {
        "nome": "Chocolate Belga",
        "descricao": "Cacau 55% com ganache firme e raspas de chocolate meio amargo.",
        "sabor": "chocolate",
        "preco": Decimal("10.90"),
        "imagem_url": "/images/cupcakes/chocolate.jpg",
        "disponivel": True,
    },
    {
        "nome": "Red Velvet",
        "descricao": "Massa aveludada com cobertura de cream cheese e farofa da própria massa.",
        "sabor": "red velvet",
        "preco": Decimal("12.00"),
        "imagem_url": "/images/cupcakes/red-velvet.jpg",
        "disponivel": True,
    },
    {
        "nome": "Limão Siciliano",
        "descricao": "Massa cítrica com curd de limão no recheio e merengue maçaricado.",
        "sabor": "limão",
        "preco": Decimal("9.50"),
        "imagem_url": "/images/cupcakes/limao.jpg",
        "disponivel": True,
    },
    {
        "nome": "Doce de Leite",
        "descricao": "Massa amanteigada com recheio de doce de leite argentino e flor de sal.",
        "sabor": "doce de leite",
        "preco": Decimal("9.90"),
        "imagem_url": "/images/cupcakes/doce-de-leite.jpg",
        "disponivel": True,
    },
    {
        "nome": "Morango com Chantilly",
        "descricao": "Massa branca com pedaços de morango, chantilly e fruta fresca no topo.",
        "sabor": "morango",
        "preco": Decimal("11.50"),
        "imagem_url": "/images/cupcakes/morango.jpg",
        "disponivel": True,
    },
    {
        # Esgotado de proposito - ver docstring do modulo.
        "nome": "Pistache",
        "descricao": "Massa de pistache siciliano com creme da própria castanha.",
        "sabor": "pistache",
        "preco": Decimal("14.00"),
        "imagem_url": "/images/cupcakes/pistache.jpg",
        "disponivel": False,
    },
]


def executar(session: Session) -> tuple[int, int]:
    """Insere o que falta. Devolve (criados, ignorados)."""
    existentes = set(session.scalars(select(CupcakeORM.nome)))

    criados = 0
    for dados in CATALOGO_INICIAL:
        if dados["nome"] in existentes:
            continue
        session.add(CupcakeORM(**dados))
        criados += 1

    session.flush()
    return criados, len(CATALOGO_INICIAL) - criados


def main() -> None:
    with SessionLocal() as session:
        criados, ignorados = executar(session)
        session.commit()

    print(f"Catalogo: {criados} cupcake(s) criado(s), {ignorados} ja existia(m).")
    if criados:
        print("Lembre-se de colocar as imagens em frontend/public/images/cupcakes/")


if __name__ == "__main__":
    main()
