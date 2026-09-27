"""Seguranca: hash de senha e JWT (JSON Web Token).

POR QUE BCRYPT DIRETO, SEM PASSLIB
----------------------------------
O passlib era um involucro sobre varios algoritmos de hash. Sua ultima
versao (1.7.4) e de outubro de 2020, e ele quebra com bcrypt >= 4.1:

  1. passlib le `bcrypt.__about__.__version__` para detectar a versao
  2. bcrypt 4.1 removeu `__about__` -> AttributeError
  3. sem a versao, passlib roda `detect_wrap_bug()`, que hasheia uma
     string de sondagem com mais de 72 bytes
  4. bcrypt antigo truncava em silencio; bcrypt >= 4.1 levanta ValueError
  5. a propria sondagem estoura, e todo hash falha

Chamar o bcrypt diretamente remove a camada quebrada: menos codigo e uma
dependencia morta a menos.

O LIMITE DE 72 BYTES
--------------------
Nao e capricho da biblioteca: o algoritmo Blowfish, base do bcrypt, usa
chave de no maximo 72 bytes. BYTES, nao caracteres - "acao" ocupa 6 bytes
em UTF-8, um emoji ocupa 4.

Tratamos isso como regra de produto em `domain/usuario.py` (senha entre 8
e 72 bytes), limite que nenhum usuario real encontra.

A alternativa, para aceitar senha de qualquer tamanho, e pre-hashear com
SHA-256 e codificar em base64 antes do bcrypt - o base64 e necessario
porque o digest bruto pode conter byte nulo, e o bcrypt trunca no
primeiro nulo. Nao adotamos porque 72 bytes nao incomoda ninguem aqui.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings


def hash_senha(senha_plana: str) -> str:
    """Gera o hash. O salt e aleatorio e fica embutido no resultado.

    `gensalt()` usa custo 12 por padrao - cerca de 200ms por hash em
    hardware atual. A lentidao E o recurso: torna forca bruta inviavel.
    SHA-256 faria o mesmo em microssegundos, e e por isso que NAO serve
    para senha.
    """
    return bcrypt.hashpw(senha_plana.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verificar_senha(senha_plana: str, hash_armazenado: str) -> bool:
    """Compara em tempo constante (o `checkpw` cuida disso).

    Devolve False em vez de propagar excecao quando o hash esta malformado
    ou a senha excede 72 bytes. Login com entrada invalida e credencial
    invalida, nao erro 500 - deixar estourar entregaria ao atacante um
    oraculo sobre o formato armazenado.
    """
    try:
        return bcrypt.checkpw(
            senha_plana.encode("utf-8"), hash_armazenado.encode("ascii")
        )
    except (ValueError, UnicodeEncodeError):
        return False


def criar_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Emite o token. Historia ID 02 / RF-03.

    JWT e ASSINADO, nao criptografado: qualquer um decodifica o payload em
    jwt.io. Por isso so vao `sub`, `exp` e o tipo - nunca senha nem dado
    pessoal.
    """
    settings = get_settings()
    expira = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expira, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token(token: str) -> dict[str, Any] | None:
    """Devolve o payload ou None.

    `jwt.decode` valida assinatura E expiracao.
    """
    settings = get_settings()
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None
