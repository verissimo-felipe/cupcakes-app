"""Entidade de identidade. Historias ID 01 (cadastro) e ID 02 (login)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.errors import (
    EmailInvalidoError,
    SenhaFracaError,
    SenhaMuitoLongaError,
)

COMPRIMENTO_MINIMO_SENHA = 8
# BYTES, nao caracteres: acentos ocupam 2 bytes em UTF-8, emoji ocupam 4.
LIMITE_BYTES_SENHA = 72


@dataclass
class Usuario:
    """Guarda `senha_hash` como string OPACA.

    O dominio nao sabe fazer hash e nao deve saber - isso e detalhe de
    biblioteca (`core/security.py`). Essa separacao permite trocar bcrypt
    por argon2 sem tocar em nenhuma regra de negocio.
    """

    id: UUID
    nome: str
    email: str
    senha_hash: str

    @staticmethod
    def normalizar_email(email: str) -> str:
        """RN-08 - e-mail e case-insensitive e sem espacos nas bordas.

        Sem isso, "Felipe@Mail.com" e "felipe@mail.com" criariam contas
        distintas. A normalizacao vive no dominio, nao no formulario, para
        valer em qualquer ponto de entrada - API, script de carga, CLI.
        """
        limpo = email.strip().lower()
        if "@" not in limpo or "." not in limpo.split("@")[-1]:
            raise EmailInvalidoError(email)
        return limpo

    @staticmethod
    def validar_senha_plana(senha: str) -> None:
        """RN-07 - comprimento minimo; RN-07b - limite superior.

        Sem exigencia de caractere especial, conforme NIST SP 800-63B:
        regras de composicao produzem senhas piores, porque o usuario
        responde a elas com padroes previsiveis (`Senha@123`). O que
        protege e comprimento.

        Recebe a senha PLANA e nao a armazena - apenas valida e descarta.
        """
        if len(senha) < COMPRIMENTO_MINIMO_SENHA:
            raise SenhaFracaError(COMPRIMENTO_MINIMO_SENHA)
        if len(senha.encode("utf-8")) > LIMITE_BYTES_SENHA:
            raise SenhaMuitoLongaError(LIMITE_BYTES_SENHA)
