"""Rotas de catalogo e carrinho. Historias ID 04, 05, 06."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import CarrinhoServiceDep, CatalogoServiceDep, UsuarioDep
from app.api.v1.schemas import (
    AdicionarItemRequest,
    AlterarQuantidadeRequest,
    CarrinhoResponse,
    CupcakeResponse,
)

catalogo_router = APIRouter(prefix="/cupcakes", tags=["catalogo"])


@catalogo_router.get("", response_model=list[CupcakeResponse])
def listar(
    servico: CatalogoServiceDep,
    busca: str | None = Query(default=None, max_length=100),
):
    """Historia ID 04 / RF-05, RF-06.

    Catalogo e busca na MESMA rota, com parametro opcional, em vez de
    `/cupcakes` e `/cupcakes/busca` separadas.

    Nao e so estetica: rota literal e rota com parametro de caminho
    colidem. `/cupcakes/busca` e `/cupcakes/{cupcake_id}` casam com a
    mesma URL, e o FastAPI resolve pela ORDEM de registro - se a
    parametrizada vier antes, "busca" seria interpretado como UUID e
    devolveria 422. Bug que aparece semanas depois, quando alguem
    reordena os decoradores.

    Nao exige autenticacao: vitrine e publica.
    """
    if busca:
        return [CupcakeResponse.de_dominio(c) for c in servico.buscar(busca)]
    return [CupcakeResponse.de_dominio(c) for c in servico.listar()]


@catalogo_router.get("/{cupcake_id}", response_model=CupcakeResponse)
def detalhar(cupcake_id: UUID, servico: CatalogoServiceDep):
    """Inexistente sobe `CupcakeNaoEncontradoError` -> 404 pelo tratador."""
    return CupcakeResponse.de_dominio(servico.detalhar(cupcake_id))


carrinho_router = APIRouter(prefix="/carrinho", tags=["carrinho"])


@carrinho_router.get("", response_model=CarrinhoResponse)
def ver(usuario: UsuarioDep, servico: CarrinhoServiceDep):
    """O carrinho e SEMPRE o de quem esta logado.

    Nao existe `GET /carrinho/{usuario_id}`. Se existisse, alguem
    esqueceria de comparar o id da URL com o da sessao, e o carrinho
    alheio ficaria legivel. Tirar o id da URL elimina a classe inteira de
    erro - nao ha o que validar.
    """
    return CarrinhoResponse.de_dominio(servico.ver(usuario.id))


@carrinho_router.post("/itens", response_model=CarrinhoResponse, status_code=status.HTTP_201_CREATED)
def adicionar(payload: AdicionarItemRequest, usuario: UsuarioDep, servico: CarrinhoServiceDep):
    """Historia ID 05.

    Devolve o CARRINHO inteiro, nao so o item criado. Poupa o front de
    uma segunda requisicao para atualizar contador e total, e elimina a
    chance de a tela mostrar soma calculada por conta propria que diverge
    da do servidor.
    """
    return CarrinhoResponse.de_dominio(
        servico.adicionar_item(usuario.id, payload.cupcake_id, payload.quantidade)
    )


@carrinho_router.patch("/itens/{cupcake_id}", response_model=CarrinhoResponse)
def alterar_quantidade(
    cupcake_id: UUID,
    payload: AlterarQuantidadeRequest,
    usuario: UsuarioDep,
    servico: CarrinhoServiceDep,
):
    """RF-09.

    PATCH, nao PUT: altera um campo da linha, nao substitui o recurso.
    """
    return CarrinhoResponse.de_dominio(
        servico.alterar_quantidade(usuario.id, cupcake_id, payload.quantidade)
    )


@carrinho_router.delete("/itens/{cupcake_id}", response_model=CarrinhoResponse)
def remover(cupcake_id: UUID, usuario: UsuarioDep, servico: CarrinhoServiceDep):
    """Historia ID 06.

    Devolve 200 com o carrinho atualizado, nao 204 vazio. A tela precisa
    do novo total imediatamente.
    """
    return CarrinhoResponse.de_dominio(servico.remover_item(usuario.id, cupcake_id))
