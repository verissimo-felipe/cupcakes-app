"""Contratos de persistencia - declarados pelo DOMINIO.

Este e o arquivo que faz a inversao de dependencia acontecer.

O dominio diz "preciso de algo que saiba buscar cupcake por id". Nao diz
como. Quem implementa e a `infra/`, e e ELA que depende daqui - nunca o
contrario.

POR QUE `Protocol` E NAO `ABC`
------------------------------
`ABC` (Abstract Base Class) usa subtipagem NOMINAL: a classe concreta
precisa herdar explicitamente da abstrata. Isso forcaria
`infra/repositories.py` a fazer `from app.domain.repositories import ...`
e herdar.

`Protocol` (PEP 544) usa subtipagem ESTRUTURAL: basta ter os metodos com
a assinatura certa. A implementacao nao precisa importar nem herdar nada.
O mypy verifica a compatibilidade em tempo de checagem.

Resultado: o acoplamento cai a zero. A infra pode ser trocada inteira sem
que uma linha do dominio mude, e o dominio nao exporta nada que a infra
precise buscar.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.entities import Carrinho, Cupcake, Pedido
from app.domain.usuario import Usuario


class CupcakeRepository(Protocol):
    """Catalogo. Historia ID 04."""

    def buscar_por_id(self, cupcake_id: UUID) -> Cupcake | None: ...

    def listar(self, apenas_disponiveis: bool = True) -> list[Cupcake]: ...

    def buscar_por_texto(self, termo: str) -> list[Cupcake]: ...


class UsuarioRepository(Protocol):
    """Identidade. Historias ID 01, 02."""

    def buscar_por_id(self, usuario_id: UUID) -> Usuario | None: ...

    def buscar_por_email(self, email: str) -> Usuario | None: ...

    def salvar(self, usuario: Usuario) -> None: ...


class CarrinhoRepository(Protocol):
    """Carrinho. Historias ID 05, 06.

    `obter_ou_criar` em vez de `buscar`: do ponto de vista do dominio, todo
    usuario SEMPRE tem carrinho - vazio, se nunca adicionou nada. Devolver
    None obrigaria cada chamador a tratar o caso, e alguem esqueceria.
    """

    def obter_ou_criar(self, usuario_id: UUID) -> Carrinho: ...

    def salvar(self, carrinho: Carrinho) -> None: ...

    def limpar(self, usuario_id: UUID) -> None: ...


class PedidoRepository(Protocol):
    """Pedidos. Historias ID 07, 08."""

    def salvar(self, pedido: Pedido) -> None: ...

    def buscar_por_id(self, pedido_id: UUID) -> Pedido | None: ...

    def listar_por_usuario(self, usuario_id: UUID) -> list[Pedido]: ...
