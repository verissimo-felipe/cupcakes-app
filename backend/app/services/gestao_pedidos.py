"""Casos de uso da LOJA sobre pedidos. Extensao da historia ID 08 / RF-15.

POR QUE UM SERVICO SEPARADO DE `PedidoService`
----------------------------------------------
Os dois mexem em pedido, mas servem a ATORES diferentes:

    PedidoService        -> o cliente: fechar, listar e ver os PROPRIOS
    GestaoPedidosService -> a loja: ver TODOS, avancar, corrigir, excluir

E a definicao de SRP (Single Responsibility Principle) na formulacao de
Robert Martin: um modulo deve responder a um unico ator. Se os dois
casos de uso morassem na mesma classe, uma mudanca pedida pela cozinha
("quero filtrar por status") mexeria no codigo que protege o cliente
("so ve o que e seu") - e e nesse tipo de mudanca que o filtro de dono
some sem ninguem perceber.

A separacao tambem deixa a seguranca visivel na assinatura: nenhum
metodo aqui recebe `usuario_id`. Isso NAO e falha de IDOR - e a loja
enxergando a loja inteira. A barreira esta antes: so rota de admin
consegue construir este servico (ver `api/v1/gestao_pedidos.py`).
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.entities import Pedido, StatusPedido
from app.domain.errors import PedidoNaoEncontradoError
from app.domain.repositories import PedidoRepository, UsuarioRepository
from app.domain.usuario import Usuario

CLIENTE_REMOVIDO = "(conta removida)"


@dataclass(frozen=True)
class PedidoComCliente:
    """Pedido + quem comprou. Formato de LEITURA para a tela da loja.

    Nao e entidade de dominio: nao tem regra, so junta dados de dois
    agregados para exibicao. Por isso mora no servico, e nao em
    `domain/entities.py`.
    """

    pedido: Pedido
    cliente_nome: str
    cliente_email: str


class GestaoPedidosService:
    def __init__(self, pedidos: PedidoRepository, usuarios: UsuarioRepository) -> None:
        self._pedidos = pedidos
        self._usuarios = usuarios

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def listar(self, status: StatusPedido | None = None) -> list[PedidoComCliente]:
        """Todos os pedidos ativos, mais recentes primeiro.

        Total de consultas: pedidos (1) + itens (1, `selectin`) + clientes
        (1, `IN`) = 3, seja com 5 ou com 5.000 pedidos. Ver
        `UsuarioRepositorySQL.buscar_por_ids`.
        """
        pedidos = self._pedidos.listar_todos(status)
        clientes = self._usuarios.buscar_por_ids({p.usuario_id for p in pedidos})
        return [self._montar(p, clientes) for p in pedidos]

    def detalhar(self, pedido_id: UUID) -> PedidoComCliente:
        return self._com_cliente(self._obter(pedido_id))

    # ------------------------------------------------------------------
    # Escrita - cada metodo e: carregar, pedir ao dominio, gravar.
    # Nenhuma regra mora aqui; todas estao em `Pedido`.
    # ------------------------------------------------------------------

    def avancar(self, pedido_id: UUID) -> PedidoComCliente:
        """Acelera a entrega: uma etapa por clique, nunca um salto. RN-05."""
        pedido = self._obter(pedido_id)
        pedido.avancar()
        self._pedidos.salvar(pedido)
        return self._com_cliente(pedido)

    def cancelar(self, pedido_id: UUID) -> PedidoComCliente:
        pedido = self._obter(pedido_id)
        pedido.cancelar()
        self._pedidos.salvar(pedido)
        return self._com_cliente(pedido)

    def alterar_endereco(self, pedido_id: UUID, endereco: str) -> PedidoComCliente:
        """RN-11, RN-12."""
        pedido = self._obter(pedido_id)
        pedido.alterar_endereco(endereco)
        self._pedidos.salvar(pedido)
        return self._com_cliente(pedido)

    def excluir(self, pedido_id: UUID) -> None:
        """RN-13 - exclusao logica. Depois disto, `_obter` nao o encontra mais."""
        pedido = self._obter(pedido_id)
        pedido.excluir()
        self._pedidos.salvar(pedido)

    # ------------------------------------------------------------------

    def _obter(self, pedido_id: UUID) -> Pedido:
        pedido = self._pedidos.buscar_por_id(pedido_id)
        if pedido is None:
            raise PedidoNaoEncontradoError(str(pedido_id))
        return pedido

    def _com_cliente(self, pedido: Pedido) -> PedidoComCliente:
        return self._montar(pedido, self._usuarios.buscar_por_ids({pedido.usuario_id}))

    @staticmethod
    def _montar(pedido: Pedido, clientes: dict[UUID, Usuario]) -> PedidoComCliente:
        cliente = clientes.get(pedido.usuario_id)
        return PedidoComCliente(
            pedido=pedido,
            cliente_nome=cliente.nome if cliente else CLIENTE_REMOVIDO,
            cliente_email=cliente.email if cliente else "",
        )
