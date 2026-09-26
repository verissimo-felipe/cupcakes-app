"""Seguranca: hash de senha e JWT (JSON Web Token).

DECISOES E PORQUES
------------------
1. bcrypt, nao SHA-256. SHA foi projetado para ser RAPIDO - exatamente o
   oposto do que se quer contra forca bruta. bcrypt tem custo ajustavel
   (work factor) e salt embutido por hash.

2. Comparacao de hash e feita pelo passlib, que usa comparacao em tempo
   constante. Comparar com `==` vazaria informacao por timing side channel.

3. O token nao carrega dados sensiveis. JWT e assinado, NAO criptografado -
   qualquer um decodifica o payload em jwt.io. Coloque `sub` e `exp`, nunca
   senha, CPF ou endereco.

RNF-11 / NIST SP 800-63B: nao exigimos caractere especial. A norma
americana abandonou regras de composicao porque produzem senhas piores
(`Senha@123`). O que vale e comprimento minimo.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

COMPRIMENTO_MINIMO_SENHA = 8

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_senha(senha_plana: str) -> str:
    return _pwd_context.hash(senha_plana)


def verificar_senha(senha_plana: str, hash_armazenado: str) -> bool:
    return _pwd_context.verify(senha_plana, hash_armazenado)


def criar_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Emite access token de vida curta. Historia ID 02 / RF-03."""
    settings = get_settings()
    expira = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expira, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token(token: str) -> dict[str, Any] | None:
    """Retorna o payload ou None. Nunca levanta para o chamador decidir.

    `jwt.decode` valida assinatura E expiracao. Passar
    `options={"verify_signature": False}` seria abrir a porta para
    qualquer um forjar identidade - nunca faca isso.
    """
    settings = get_settings()
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None
