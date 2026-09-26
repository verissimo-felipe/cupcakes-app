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
