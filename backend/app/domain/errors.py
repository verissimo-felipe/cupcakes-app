"""Erros de dominio - sem conhecimento de HTTP."""


class DomainError(Exception):
    codigo = "erro_dominio"


class QuantidadeInvalidaError(DomainError):
    """RN-01 - quantidade minima por item e 1."""
    codigo = "quantidade_invalida"

    def __init__(self, quantidade: int) -> None:
        super().__init__(f"Quantidade deve ser >= 1, recebido: {quantidade}")
        self.quantidade = quantidade


class CupcakeIndisponivelError(DomainError):
    """RN-02 - cupcake fora de estoque nao entra no carrinho."""
    codigo = "cupcake_indisponivel"

    def __init__(self, nome: str) -> None:
        super().__init__(f"Cupcake indisponivel: {nome}")
        self.nome = nome


class ItemNaoEncontradoError(DomainError):
    """RN-03 - remover item ausente e erro, nao no-op silencioso."""
    codigo = "item_nao_encontrado"


class CarrinhoVazioError(DomainError):
    """RN-04 - nao se fecha pedido sem itens."""
    codigo = "carrinho_vazio"


class TransicaoStatusInvalidaError(DomainError):
    """RN-05 - o ciclo de vida do pedido e uma FSM (Finite State Machine)."""
    codigo = "transicao_invalida"

    def __init__(self, de: str, para: str) -> None:
        super().__init__(f"Transicao invalida: {de} -> {para}")
        self.de = de
        self.para = para


class SenhaFracaError(DomainError):
    """RN-07 - comprimento minimo de senha."""
    codigo = "senha_fraca"

    def __init__(self, minimo: int) -> None:
        super().__init__(f"A senha deve ter pelo menos {minimo} caracteres")
        self.minimo = minimo


class EmailInvalidoError(DomainError):
    """RN-08 - formato de e-mail."""
    codigo = "email_invalido"

    def __init__(self, email: str) -> None:
        super().__init__("E-mail em formato invalido")
        self.email = email


class EmailJaCadastradoError(DomainError):
    """RN-09 - um e-mail, uma conta."""
    codigo = "email_ja_cadastrado"


class CredenciaisInvalidasError(DomainError):
    """RN-10 - login falho NAO revela se o erro foi no e-mail ou na senha.

    Mensagem generica de proposito: distinguir permitiria enumerar quais
    e-mails possuem conta no sistema.
    """
    codigo = "credenciais_invalidas"

    def __init__(self) -> None:
        super().__init__("E-mail ou senha invalidos")


class CupcakeNaoEncontradoError(DomainError):
    """Cupcake inexistente no catalogo."""
    codigo = "cupcake_nao_encontrado"

    def __init__(self, cupcake_id: str) -> None:
        super().__init__("Cupcake nao encontrado")
        self.cupcake_id = cupcake_id


class PedidoNaoEncontradoError(DomainError):
    """Pedido inexistente OU pertencente a outro usuario.

    Uma excecao so para os dois casos e proposital. Distinguir
    "nao existe" de "existe mas nao e seu" permitiria a um atacante
    descobrir quais ids de pedido sao validos no sistema, apenas
    observando qual mensagem volta.
    """
    codigo = "pedido_nao_encontrado"

    def __init__(self, pedido_id: str) -> None:
        super().__init__("Pedido nao encontrado")
        self.pedido_id = pedido_id


class SenhaMuitoLongaError(DomainError):
    """RN-07b - limite superior de senha.

    O numero 72 vem do bcrypt (chave maxima do Blowfish), mas o tratamos
    como regra de PRODUTO: "senha entre 8 e 72 caracteres" e restricao
    comum em sistemas reais e nao incomoda usuario nenhum.

    Reconhecendo o vazamento: o dominio nao deveria conhecer limite de
    biblioteca de criptografia. A alternativa purista seria pre-hashear
    com SHA-256 + base64 antes do bcrypt, aceitando qualquer tamanho. A
    escolha aqui foi pela simplicidade, e esta registrada como tal.
    """
    codigo = "senha_muito_longa"

    def __init__(self, maximo_bytes: int) -> None:
        super().__init__(f"A senha nao pode exceder {maximo_bytes} bytes")
        self.maximo_bytes = maximo_bytes


class EnderecoInvalidoError(DomainError):
    """RN-12 - endereco precisa ter conteudo util, nao so espacos.

    O Pydantic confere `min_length=5` no texto BRUTO, entao cinco espacos
    passariam por ele. O dominio confere depois do `strip()`, e vale para
    qualquer porta de entrada - checkout do cliente ou edicao da loja.
    """
    codigo = "endereco_invalido"

    def __init__(self, minimo: int) -> None:
        super().__init__(f"O endereco precisa ter pelo menos {minimo} caracteres")
        self.minimo = minimo


class PedidoNaoEditavelError(DomainError):
    """RN-11 - o endereco so muda enquanto o pedido esta na loja.

    Depois de `saiu_para_entrega`, o entregador ja esta na rua com o
    endereco antigo. Trocar no sistema nao muda para onde ele vai - so
    cria um registro que nao bate com o que aconteceu.
    """
    codigo = "pedido_nao_editavel"

    def __init__(self, status: str) -> None:
        super().__init__(
            f"O endereco nao pode mais ser alterado: o pedido esta '{status}'"
        )
        self.status = status


class PedidoNaoExcluivelError(DomainError):
    """RN-13 - so pedido FINALIZADO (entregue ou cancelado) pode ser excluido.

    Excluir um pedido em andamento faria ele sumir da tela do cliente
    enquanto a cozinha ainda prepara os cupcakes. O caminho correto e
    cancelar primeiro - o cancelamento fica registrado - e so entao
    tirar da lista.
    """
    codigo = "pedido_nao_excluivel"

    def __init__(self, status: str) -> None:
        super().__init__(
            "Apenas pedidos entregues ou cancelados podem ser excluidos. "
            f"Este esta '{status}': cancele antes de excluir."
        )
        self.status = status
