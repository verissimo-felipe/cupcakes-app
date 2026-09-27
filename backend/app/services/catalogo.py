"""Casos de uso de catalogo e carrinho. Historias ID 04, 05, 06."""

from __future__ import annotations

from uuid import UUID

from app.domain.entities import Carrinho, Cupcake
from app.domain.errors import CupcakeNaoEncontradoError
from app.domain.repositories import CarrinhoRepository, CupcakeRepository


class CatalogoService:
    """Historia ID 04 / RF-05, RF-06.

    Servico fino de proposito. Listar catalogo e leitura pura: nao ha
    regra a aplicar, nada a orquestrar. Uma camada que so repassa a
    chamada pode parecer desperdicio, e algumas arquiteturas deixariam o
    controller falar direto com o repositorio.

    Mantemos por consistencia: se amanha entrar cache, ordenacao por
    popularidade ou filtro por regiao de entrega, existe um lugar obvio
    onde isso vai - e nenhum controller precisa mudar.
    """

    def __init__(self, cupcakes: CupcakeRepository) -> None:
        self._cupcakes = cupcakes

    def listar(self) -> list[Cupcake]:
        return self._cupcakes.listar(apenas_disponiveis=True)

    def buscar(self, termo: str) -> list[Cupcake]:
        """RNF-04 - busca em ate 1 segundo.

        Termo vazio devolve o catalogo inteiro em vez de lista vazia: e o
        que o usuario espera ao limpar o campo de busca.
        """
        if not termo.strip():
            return self.listar()
        return self._cupcakes.buscar_por_texto(termo)

    def detalhar(self, cupcake_id: UUID) -> Cupcake:
        cupcake = self._cupcakes.buscar_por_id(cupcake_id)
        if cupcake is None:
            raise CupcakeNaoEncontradoError(str(cupcake_id))
        return cupcake


class CarrinhoService:
    """Historias ID 05 (adicionar) e ID 06 (remover) / RF-08, RF-09.

    Repare que NENHUM metodo abaixo contem regra de negocio. Nao ha
    verificacao de quantidade minima, nem de disponibilidade, nem logica
    de somar item repetido. Tudo isso esta em `Carrinho.adicionar()`, no
    dominio.

    O que este servico faz e so o roteiro: carrega, delega, salva.
    """

    def __init__(self, carrinhos: CarrinhoRepository, cupcakes: CupcakeRepository) -> None:
        self._carrinhos = carrinhos
        self._cupcakes = cupcakes

    def ver(self, usuario_id: UUID) -> Carrinho:
        return self._carrinhos.obter_ou_criar(usuario_id)

    def adicionar_item(
        self, usuario_id: UUID, cupcake_id: UUID, quantidade: int = 1
    ) -> Carrinho:
        """Historia ID 05.

        O cupcake e buscado no repositorio, nao recebido pronto do
        chamador. Se o controller pudesse passar um `Cupcake` montado a
        partir do JSON da requisicao, o cliente escolheria o proprio
        preco - e a validacao de disponibilidade seria inutil, porque
        viria do proprio atacante.

        Regra de ouro: preco e disponibilidade SEMPRE vem do banco.
        """
        cupcake = self._cupcakes.buscar_por_id(cupcake_id)
        if cupcake is None:
            raise CupcakeNaoEncontradoError(str(cupcake_id))

        carrinho = self._carrinhos.obter_ou_criar(usuario_id)
        carrinho.adicionar(cupcake, quantidade)  # RN-01, RN-02, RN-06
        self._carrinhos.salvar(carrinho)
        return carrinho

    def alterar_quantidade(
        self, usuario_id: UUID, cupcake_id: UUID, quantidade: int
    ) -> Carrinho:
        """RF-09 - atualizacao do total em tempo real."""
        carrinho = self._carrinhos.obter_ou_criar(usuario_id)
        carrinho.alterar_quantidade(cupcake_id, quantidade)  # RN-01, RN-03
        self._carrinhos.salvar(carrinho)
        return carrinho

    def remover_item(self, usuario_id: UUID, cupcake_id: UUID) -> Carrinho:
        """Historia ID 06."""
        carrinho = self._carrinhos.obter_ou_criar(usuario_id)
        carrinho.remover(cupcake_id)  # RN-03
        self._carrinhos.salvar(carrinho)
        return carrinho
