"""Conexao com o banco - engine, sessao e Base declarativa.

Este e o unico arquivo do projeto que sabe QUAL banco estamos usando.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    # Testa a conexao com um ping antes de entregar do pool. Sem isso, se o
    # Postgres reiniciar ou o firewall derrubar conexoes ociosas, o pool
    # devolve um socket morto e a proxima request falha com
    # "server closed the connection unexpectedly" - erro intermitente,
    # dificil de reproduzir e classico em ambiente com Docker.
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    # Por padrao o SQLAlchemy EXPIRA os objetos apos commit: o proximo
    # acesso a qualquer atributo dispara nova consulta. Como convertemos
    # para entidades de dominio e a sessao fecha logo depois, isso causaria
    # DetachedInstanceError. Desligar e o comportamento correto aqui.
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base das tabelas. Vive em infra/ porque E um detalhe de infra."""


def get_session() -> Iterator[Session]:
    """Dependencia do FastAPI: uma sessao por request.

    O padrao commit-no-sucesso / rollback-na-excecao e uma Unit of Work
    minima: ou a request inteira persiste, ou nada persiste. Nao existe
    estado meio-gravado quando uma regra de negocio falha no meio.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
