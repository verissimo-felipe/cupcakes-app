"""Entidade de identidade. Historias ID 01 (cadastro) e ID 02 (login).

O `Usuario` guarda `senha_hash` como string OPACA. O dominio nao sabe
fazer hash e nao deve saber: isso e detalhe de biblioteca
(`core/security.py` usa passlib). O dominio so sabe que existe um segredo
verificavel associado ao usuario.

Essa separacao e o que permite trocar bcrypt por argon2 sem tocar em
nenhuma regra de negocio.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.errors import EmailInvalidoError, SenhaFracaError

COMPRIMENTO_MINIMO_SENHA = 8


@dataclass
class Usuario:
    id: UUID
    nome: str
    email: str
    senha_hash: str

    @staticmethod
    def normalizar_email(email: str) -> str:
        """RN-08 - e-mail e case-insensitive e sem espacos nas bordas.

        Sem isso, "Felipe@Mail.com" e "felipe@mail.com" criariam duas
        contas distintas. A normalizacao acontece no dominio, nao no
        formulario, para valer em qualquer ponto de entrada - API, script
        de carga, linha de comando.
        """
        limpo = email.strip().lower()
        if "@" not in limpo or "." not in limpo.split("@")[-1]:
            raise EmailInvalidoError(email)
        return limpo

    @staticmethod
    def validar_senha_plana(senha: str) -> None:
        """RN-07 - comprimento minimo, sem exigencia de caractere especial.

        Conforme NIST SP 800-63B: regras de composicao produzem senhas
        piores, porque o usuario responde a elas com padroes previsiveis
        (`Senha@123`). O que protege e comprimento.

        Recebe a senha PLANA e nao a armazena - apenas valida e descarta.
        """
        if len(senha) < COMPRIMENTO_MINIMO_SENHA:
            raise SenhaFracaError(COMPRIMENTO_MINIMO_SENHA)
