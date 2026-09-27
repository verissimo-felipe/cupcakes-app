"""Contratos HTTP - o que entra e o que sai da API.

POR QUE ESTES MODELOS NAO SAO AS ENTIDADES DE DOMINIO
-----------------------------------------------------
Sao tres formatos distintos no sistema, e confundi-los custa caro:

    CupcakeORM   (infra)    -> como o dado e ARMAZENADO
    Cupcake      (domain)   -> o que o dado SIGNIFICA
    CupcakeResponse (api)   -> o que o cliente PODE VER

O terceiro e o que impede vazamento. `Usuario` carrega `senha_hash`; se a
rota serializasse a entidade direto, o hash iria para o navegador em toda
resposta de login. `UsuarioResponse` simplesmente nao tem esse campo - a
protecao vem da ausencia, nao de um `del` que alguem pode esquecer.

Os modelos de REQUEST tambem nao sao decorativos: eles rejeitam payload
malformado antes de qualquer codigo nosso rodar, devolvendo 422 com o
caminho exato do campo invalido.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.entities import Carrinho, Cupcake, ItemCarrinho, Pedido, StatusPedido
from app.domain.usuario import Usuario

# ---------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------


class RegistroRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    # min_length=1 apenas: o comprimento REAL (8 a 72 bytes) e validado no
    # dominio, por `Usuario.validar_senha_plana`. Duplicar a regra aqui
    # criaria duas fontes de verdade que divergem na primeira mudanca.
    senha: str = Field(min_length=1)


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1)


class AdicionarItemRequest(BaseModel):
    cupcake_id: UUID
    # ge=1 aqui e RN-01 no dominio dizem a mesma coisa de proposito: o
    # Pydantic rejeita cedo com mensagem clara de campo, e o dominio
    # garante a regra mesmo se a chamada vier de outro lugar (script,
    # CLI, outro servico). Redundancia defensiva, nao duplicacao de logica.
    quantidade: int = Field(default=1, ge=1, le=99)


class AlterarQuantidadeRequest(BaseModel):
    quantidade: int = Field(ge=1, le=99)


class CheckoutRequest(BaseModel):
    endereco_entrega: str = Field(min_length=5, max_length=300)


class MudarStatusRequest(BaseModel):
    status: StatusPedido


# ---------------------------------------------------------------------
# Saida
# ---------------------------------------------------------------------


class UsuarioResponse(BaseModel):
    """SEM `senha_hash`. A ausencia do campo e a protecao."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nome: str
    email: str

    @classmethod
    def de_dominio(cls, usuario: Usuario) -> "UsuarioResponse":
        return cls(id=usuario.id, nome=usuario.nome, email=usuario.email)


class CupcakeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nome: str
    descricao: str
    sabor: str
    preco: Decimal
    imagem_url: str
    disponivel: bool

    @classmethod
    def de_dominio(cls, cupcake: Cupcake) -> "CupcakeResponse":
        return cls(**cupcake.__dict__)


class ItemResponse(BaseModel):
    cupcake_id: UUID
    nome: str
    preco_unitario: Decimal
    quantidade: int
    subtotal: Decimal

    @classmethod
    def de_dominio(cls, item: ItemCarrinho) -> "ItemResponse":
        return cls(
            cupcake_id=item.cupcake_id,
            nome=item.nome,
            preco_unitario=item.preco_unitario,
            quantidade=item.quantidade,
            # `subtotal` e propriedade calculada do dominio, nao coluna.
            # Enviar pronto evita que o front reimplemente a multiplicacao
            # e divirja em arredondamento.
            subtotal=item.subtotal,
        )


class CarrinhoResponse(BaseModel):
    itens: list[ItemResponse]
    total: Decimal
    quantidade_itens: int

    @classmethod
    def de_dominio(cls, carrinho: Carrinho) -> "CarrinhoResponse":
        return cls(
            itens=[ItemResponse.de_dominio(i) for i in carrinho.itens],
            total=carrinho.total,
            quantidade_itens=sum(i.quantidade for i in carrinho.itens),
        )


class PedidoResponse(BaseModel):
    id: UUID
    itens: list[ItemResponse]
    endereco_entrega: str
    total: Decimal
    status: StatusPedido

    @classmethod
    def de_dominio(cls, pedido: Pedido) -> "PedidoResponse":
        return cls(
            id=pedido.id,
            itens=[ItemResponse.de_dominio(i) for i in pedido.itens],
            endereco_entrega=pedido.endereco_entrega,
            total=pedido.total,
            status=pedido.status,
        )


class PedidoResumoResponse(BaseModel):
    """Versao enxuta para listagem. Historia ID 08.

    Sem os itens: a tela "Meus pedidos" mostra numero, valor e status. Se
    o cliente tiver 50 pedidos de 8 itens, a resposta completa carregaria
    400 linhas que ninguem le - e o `lazy="selectin"` do ORM buscaria
    todas elas do banco.
    """

    id: UUID
    total: Decimal
    status: StatusPedido
    quantidade_itens: int

    @classmethod
    def de_dominio(cls, pedido: Pedido) -> "PedidoResumoResponse":
        return cls(
            id=pedido.id,
            total=pedido.total,
            status=pedido.status,
            quantidade_itens=sum(i.quantidade for i in pedido.itens),
        )


class ErroResponse(BaseModel):
    """Formato unico de erro em toda a API.

    Declarado aqui para aparecer no schema OpenAPI - assim o cliente
    TypeScript gerado conhece o formato de erro, nao so o de sucesso.
    """

    codigo: str
    mensagem: str
