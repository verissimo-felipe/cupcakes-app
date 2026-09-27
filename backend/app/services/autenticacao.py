"""Casos de uso de identidade. Historias ID 01 (cadastro) e ID 02 (login).

Este servico e o unico ponto do sistema que combina tres coisas que
sozinhas nao resolvem nada: a regra do dominio (formato de e-mail,
comprimento de senha), o repositorio (o e-mail ja existe?) e a
criptografia (`core/security`).
"""

from __future__ import annotations

from uuid import uuid4

from app.core.security import hash_senha, verificar_senha
from app.domain.errors import CredenciaisInvalidasError, EmailJaCadastradoError
from app.domain.repositories import UsuarioRepository
from app.domain.usuario import Usuario


class AutenticacaoService:
    """Recebe o repositorio pelo CONTRATO, nao pela implementacao.

    O tipo anotado e `UsuarioRepository`, que e um `Protocol`. Em
    producao chega um `UsuarioRepositorySQL`; nos testes, um dicionario
    em memoria. O servico nao percebe diferenca - e por isso que os
    testes dele rodam sem banco.
    """

    def __init__(self, usuarios: UsuarioRepository) -> None:
        self._usuarios = usuarios

    def cadastrar(self, nome: str, email: str, senha: str) -> Usuario:
        """Historia ID 01 / RF-01.

        Ordem dos passos importa:

        1. Normalizar o e-mail ANTES de consultar. Buscar por
           "Felipe@Mail.com" nao encontraria "felipe@mail.com" gravado,
           e o cadastro duplicado passaria.
        2. Validar a senha antes de consultar o banco. Consulta e I/O;
           validacao e memoria. Falhar cedo economiza a ida ao banco.
        3. Fazer o hash so no fim, porque bcrypt e deliberadamente lento -
           nao faz sentido gastar esse custo para depois descobrir que o
           e-mail ja existe.
        """
        email_normalizado = Usuario.normalizar_email(email)
        Usuario.validar_senha_plana(senha)

        if self._usuarios.buscar_por_email(email_normalizado) is not None:
            raise EmailJaCadastradoError("Ja existe conta com este e-mail")

        usuario = Usuario(
            id=uuid4(),
            nome=nome.strip(),
            email=email_normalizado,
            senha_hash=hash_senha(senha),
        )
        self._usuarios.salvar(usuario)
        return usuario

    def autenticar(self, email: str, senha: str) -> Usuario:
        """Historia ID 02 / RF-03.

        Devolve o `Usuario`. NAO emite o token: JWT e assunto de
        transporte, e quem cuida disso e a camada de API. Manter o
        servico livre de JWT permite testa-lo sem chave secreta.

        A mesma excecao para e-mail inexistente e senha errada e
        obrigatoria - ver `CredenciaisInvalidasError`.
        """
        try:
            email_normalizado = Usuario.normalizar_email(email)
        except Exception:
            # E-mail malformado no login e apenas credencial invalida.
            # Responder "formato invalido" ja entregaria informacao.
            raise CredenciaisInvalidasError from None

        usuario = self._usuarios.buscar_por_email(email_normalizado)
        if usuario is None:
            # Ainda assim gastamos o tempo do hash, para que a resposta
            # de "usuario inexistente" demore o mesmo que a de "senha
            # errada". Sem isso, a diferenca de tempo revelaria quais
            # e-mails tem conta - um timing side channel.
            verificar_senha(senha, hash_senha("valor-descartavel"))
            raise CredenciaisInvalidasError

        if not verificar_senha(senha, usuario.senha_hash):
            raise CredenciaisInvalidasError

        return usuario
