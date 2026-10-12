"""Rotas de identidade. Historias ID 01 (cadastro) e ID 02 (login).

Camada de CONTROLLER no mapeamento MVC. Cada funcao aqui faz tres coisas
e nada mais: recebe, delega ao servico, responde. Nenhuma regra de
negocio - elas vivem em `domain/`.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.api.deps import NOME_COOKIE, AuthServiceDep, UsuarioDep
from app.api.v1.schemas import LoginRequest, RegistroRequest, UsuarioResponse
from app.core.config import get_settings
from app.core.security import criar_access_token

router = APIRouter(prefix="/auth", tags=["autenticacao"])


def _e_admin(email: str) -> bool:
    """Mesma regra de `deps.usuario_admin`, so que para INFORMAR o front.

    A duplicacao e consciente e limitada: aqui o resultado vira um campo
    de resposta; la ele barra a requisicao. Se um dia virar RBAC
    (Role-Based Access Control) com papel no banco, as duas passam a ler
    a mesma coluna e esta funcao some.
    """
    alvos = {e.strip().lower() for e in get_settings().ADMIN_EMAILS}
    return email in alvos


def _gravar_cookie(response: Response, usuario_id: str) -> None:
    """Emite o JWT e grava no cookie de sessao.

    Cada flag resolve um ataque especifico:

    `httponly=True`  -> JavaScript nao le o cookie. Neutraliza roubo de
                        sessao por XSS (Cross-Site Scripting).

    `samesite="lax"` -> o navegador nao envia o cookie em requisicao
                        POST originada de outro site. E a defesa contra
                        CSRF (Cross-Site Request Forgery), o contra
                        classico de usar cookie. "lax" permite navegacao
                        de link vinda de fora, que e o comportamento que
                        o usuario espera.

    `secure`         -> so trafega sobre HTTPS. CONFIGURAVEL de proposito:
                        em HTTP local o navegador descartaria um cookie
                        Secure, e o login pareceria nao funcionar sem
                        nenhuma mensagem de erro. Em producao vai True.

    `max_age`        -> expiracao no navegador, casada com a do token.
                        Sem isso o cookie sobreviveria ao JWT e o usuario
                        levaria 401 com cookie aparentemente valido.

    Nota sobre o front em outra porta: localhost:3000 e localhost:8000 sao
    origens diferentes mas o MESMO site, entao `SameSite=Lax` funciona.
    Se front e back ficarem em dominios distintos em producao, sera
    preciso `SameSite=None; Secure` e revisar a protecao CSRF.
    """
    settings = get_settings()
    response.set_cookie(
        key=NOME_COOKIE,
        value=criar_access_token(usuario_id),
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


@router.post("/registrar", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar(payload: RegistroRequest, response: Response, servico: AuthServiceDep):
    """Historia ID 01 / RF-01.

    Ja autentica apos o cadastro: obrigar o usuario a preencher e-mail e
    senha de novo, dois segundos depois de te-los digitado, e atrito sem
    ganho de seguranca.
    """
    usuario = servico.cadastrar(payload.nome, payload.email, payload.senha)
    _gravar_cookie(response, str(usuario.id))
    return UsuarioResponse.de_dominio(usuario, admin=_e_admin(usuario.email))


@router.post("/login", response_model=UsuarioResponse)
def login(payload: LoginRequest, response: Response, servico: AuthServiceDep):
    """Historia ID 02 / RF-03.

    Credencial invalida sobe como `CredenciaisInvalidasError` e vira 401
    pelo tratador central de `main.py` - sem `try/except` aqui.
    """
    usuario = servico.autenticar(payload.email, payload.senha)
    _gravar_cookie(response, str(usuario.id))
    return UsuarioResponse.de_dominio(usuario, admin=_e_admin(usuario.email))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    """Apaga o cookie.

    `delete_cookie` precisa do MESMO `path` usado na gravacao. Com path
    divergente o navegador cria um segundo cookie vazio e mantem o
    original - o usuario clica em sair e continua logado.

    Como o JWT e stateless, o token em si continua valido ate expirar. Uma
    revogacao real exigiria lista de tokens invalidados no servidor, o que
    anularia boa parte da vantagem do stateless. Para este escopo, apagar
    o cookie basta e esta documentado como tal.
    """
    response.delete_cookie(key=NOME_COOKIE, path="/")


@router.get("/eu", response_model=UsuarioResponse)
def eu(usuario: UsuarioDep):
    """Quem esta logado.

    O front chama isto no carregamento para decidir entre mostrar a tela
    de login ou a sessao ativa - ele nao consegue ler o cookie httpOnly
    para descobrir sozinho.
    """
    return UsuarioResponse.de_dominio(usuario, admin=_e_admin(usuario.email))
