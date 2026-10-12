FROM python:3.12-slim

# Nao rodar como root. Se a aplicacao for comprometida, o atacante herda
# um usuario sem privilegios em vez de dono do container.
RUN useradd --create-home --shell /bin/bash app

WORKDIR /code

# Copiar so o manifesto primeiro: o Docker cacheia esta camada e so
# reinstala dependencias quando o pyproject muda, nao a cada edicao de
# codigo. Economiza minutos por build.
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir ".[dev]"

COPY --chown=app:app . .

USER app
EXPOSE 8000

# Padrao = PRODUCAO: migra, carrega o catalogo e sobe na porta do host.
# O docker-compose substitui este comando por um com --reload para
# desenvolvimento (ver `command:` la).
CMD ["sh", "scripts/iniciar.sh"]
