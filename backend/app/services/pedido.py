"""Casos de uso de pedido. Historias ID 07 (checkout) e ID 08 (rastreamento).

Este e o servico que MAIS justifica a existencia da camada, porque o
checkout toca DOIS agregados: cria o pedido e esvazia o carrinho.

Nenhuma entidade de dominio pode fazer isso sozinha. `Carrinho` nao
conhece `Pedido`, e nao deve conhecer - sao ciclos de vida diferentes.
Coordenar os dois e responsabilidade de caso de uso, nao de regra.
"""

from __future__ import annotations

from uuid import UUID

from app.domain.entities import Pedido, StatusPedido
from app.domain.errors import PedidoNaoEncontradoError
from app.domain.repositories import CarrinhoRepository, PedidoRepository


class PedidoService:
    def __init__(self, pedidos: PedidoRepository, carrinhos: CarrinhoRepository) -> None:
        self._pedidos = pedidos
        self._carrinhos = carrinhos

    def finalizar(self, usuario_id: UUID, endereco_entrega: str) -> Pedido:
        """Historia ID 07 / RF-12, RF-13.

        ATOMICIDADE: as duas escritas - gravar o pedido e limpar o
        carrinho - precisam valer juntas. Se a segunda falhasse depois da
        primeira, o cliente teria pedido feito E carrinho cheio, e
        compraria de novo sem querer.

        A garantia nao esta aqui: esta em `infra/db.py:get_session`, que
        so faz commit se a requisicao inteira terminar sem excecao. Este
        metodo pode escrever nas duas linhas seguintes com tranquilidade
        porque a transacao envolve as duas.
        """
        carrinho = self._carrinhos.obter_ou_criar(usuario_id)

        # RN-04 (carrinho vazio) e aplicada aqui dentro, no dominio.
        pedido = Pedido.a_partir_do_carrinho(carrinho, endereco_entrega.strip())

        self._pedidos.salvar(pedido)
        self._carrinhos.limpar(usuario_id)
        return pedido

    def listar_do_usuario(self, usuario_id: UUID) -> list[Pedido]:
        """Historia ID 08.

        O filtro por usuario esta na CONSULTA, nao numa checagem depois.
        Trazer todos os pedidos e filtrar em Python funcionaria - e
        bastaria alguem esquecer o filtro uma vez para vazar o historico
        de compras de toda a base.
        """
        return self._pedidos.listar_por_usuario(usuario_id)

    def detalhar(self, pedido_id: UUID, usuario_id: UUID) -> Pedido:
        """Historia ID 08 / RF-14.

        SEGURANCA - IDOR (Insecure Direct Object Reference).

        Buscar o pedido pelo id e devolve-lo seria a implementacao
        obvia... e a falha numero 1 do OWASP API Security Top 10
        (Broken Object Level Authorization). Como o id vem da URL, trocar
        um caractere daria acesso ao pedido de outro cliente: endereco de
        entrega, itens comprados e valor gasto.

        Exigir `usuario_id` no parametro torna impossivel escrever este
        caso de uso sem decidir de quem e o pedido. A assinatura da
        funcao obriga o cuidado.

        E quando o pedido e de outro, levantamos a MESMA excecao de
        "nao encontrado" - ver o docstring de `PedidoNaoEncontradoError`.
        """
        pedido = self._pedidos.buscar_por_id(pedido_id)
        if pedido is None or pedido.usuario_id != usuario_id:
            raise PedidoNaoEncontradoError(str(pedido_id))
        return pedido

    def avancar_status(self, pedido_id: UUID, novo_status: StatusPedido) -> Pedido:
        """Historia ID 08 / RF-15 - operacao administrativa.

        Sem `usuario_id`: quem avanca o status e a loja, nao o cliente.
        A restricao de quem pode chamar isto e feita na camada de API,
        por perfil de acesso.

        A validacao da transicao NAO esta aqui - esta na FSM do dominio,
        em `Pedido.mudar_status()`. Este metodo nem sabe quais transicoes
        existem.
        """
        pedido = self._pedidos.buscar_por_id(pedido_id)
        if pedido is None:
            raise PedidoNaoEncontradoError(str(pedido_id))

        pedido.mudar_status(novo_status)  # RN-05
        self._pedidos.salvar(pedido)
        return pedido
