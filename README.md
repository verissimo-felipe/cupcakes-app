# Loja de Cupcakes — Projeto Integrador Transdisciplinar II

Aplicação web de e-commerce para uma loja de cupcakes, desenvolvida como
entrega da Situação Problema 2. O planejamento — histórias de usuário,
backlog, requisitos, UML e roadmap — foi produzido na Situação Problema 1.

**Stack:** Next.js (React/TypeScript) · FastAPI (Python) · PostgreSQL · Docker

---

## Padrão arquitetural: MVC

A aplicação segue **MVC** (*Model-View-Controller*), adaptado para
arquitetura desacoplada.

| Componente | Onde vive | Responsabilidade |
|---|---|---|
| **View** | `frontend/` (Next.js) | Apresentação e captura de entrada |
| **Controller** | `backend/app/api/v1/` | Recebe requisição, invoca o Model, devolve resposta |
| **Model** | `backend/app/domain/` + `backend/app/infra/` | Dados e regras de negócio |
| *(extensão)* | `backend/app/services/` | Casos de uso — evita *fat controller* |

O MVC clássico pressupõe que o servidor renderiza a View. Ao separar a
aplicação em SPA + API REST, a View migra para o cliente e o servidor fica
com Model e Controller — os papéis permanecem, separados por uma fronteira
HTTP.

A camada de serviços é a solução clássica para o modo de falha mais comum
do padrão: o acúmulo de lógica de negócio dentro do controlador.

📄 **Justificativa completa, diagrama e fluxo de requisição:**
[`docs/arquitetura.md`](docs/arquitetura.md)

---

## Como rodar

Pré-requisito: Docker Desktop instalado.

```bash
git clone https://github.com/verissimo-felipe/cupcakes-app.git
cd cupcakes-app

# 1. Configurar o ambiente
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"   # colar em SECRET_KEY

# 2. Subir tudo
docker compose up --build
```

| Serviço | URL |
|---|---|
| API | http://localhost:8000 |
| Documentação interativa (Swagger) | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |

### Testes

**Back-end** — 118 testes (pytest), em quatro camadas:

```bash
docker compose exec backend pytest -q        # ou, fora do Docker:
cd backend && pip install -e ".[dev]" && pytest -q
```

| Arquivo | O que cobre | Precisa de banco? |
|---|---|---|
| `tests/test_dominio.py` | Regras de negócio (RN-01 a RN-13), FSM do pedido | Não |
| `tests/test_services.py` | Casos de uso, com repositórios falsos em memória | Não |
| `tests/test_infra.py` | Tradução tabela ↔ entidade, exclusão lógica | SQLite em memória |
| `tests/test_api.py` | Pilha HTTP inteira: status, cookie, 401/403/404 | SQLite em memória |

Os testes de regra de negócio rodam sem banco e sem servidor — consequência
direta da arquitetura.

**Front-end** — 53 testes (Vitest + React Testing Library):

```bash
cd frontend && npm install && npm test
```

Cobrem o cliente de API, as telas de login, carrinho e loja, e componentes
como o card de produto. Detalhes em [`frontend/README.md`](frontend/README.md).

---

## Estrutura

```
cupcakes-app/
├── docker-compose.yml
├── .env.example              # .env real nunca vai para o Git
├── docs/
│   ├── arquitetura.md        # padrão MVC — justificativa e diagrama
│   ├── rastreabilidade.md    # História → RF → RN → Código
│   └── manual-do-usuario.md
├── backend/
│   ├── app/
│   │   ├── main.py           # app FastAPI + tratamento de erros
│   │   ├── core/             # configuração, segurança
│   │   ├── domain/           # MODEL — entidades e regras (sem framework)
│   │   ├── services/         # casos de uso
│   │   ├── infra/            # MODEL — persistência
│   │   └── api/v1/           # CONTROLLER — routers HTTP
│   └── tests/
└── frontend/                 # VIEW — Next.js
    ├── app/                  # telas (uma pasta por rota)
    ├── componentes/
    ├── lib/                  # cliente de API, tipos, formatação
    └── testes/               # Vitest + React Testing Library
```

---

## Escopo desta entrega

Das 15 histórias planejadas, **6 foram implementadas**, escolhidas por
formarem um fluxo contínuo de compra:

`Cadastro/Login (01, 02) → Catálogo (04) → Carrinho (05, 06) → Checkout (07) → Rastreamento (08)`

Do lado da loja, a **gestão de pedidos** (`/loja/pedidos`) estende o RF-15:
ver os pedidos de todos os clientes, avançar etapa, cancelar, corrigir
endereço e excluir — com exclusão lógica, preservando o registro da venda.

O recorte foi vertical, não horizontal: entregar os Sprints 1 e 2 na ordem
do roadmap produziria catálogo sem carrinho — um e-commerce onde não se
compra.

As 9 histórias restantes permanecem no **backlog priorizado**, documentado
em [`docs/rastreabilidade.md`](docs/rastreabilidade.md) junto com o roadmap
completo de 5 sprints.

---

## Segurança

| Item | Decisão |
|---|---|
| Hash de senha | `bcrypt` com salt por hash — não SHA-256, rápido demais para resistir a força bruta |
| Sessão | JWT em cookie `httpOnly` + `Secure` + `SameSite=Lax` — inacessível a JavaScript, portanto imune a roubo por XSS |
| SQL | SQLAlchemy com parâmetros vinculados; nenhuma query montada por f-string |
| Acesso a pedidos | Pedido de outro cliente responde 404, não 403 — evita IDOR (*Insecure Direct Object Reference*) e não confirma que o id existe |
| Área da loja | Rotas `/api/v1/admin/*` protegidas no router inteiro: anônimo 401, cliente 403 |
| Redirecionamento | `?voltar=` do login só aceita caminho interno — bloqueia *open redirect* (CWE-601) |
| Segredos | `.env` no `.gitignore`; apenas `.env.example` é versionado |
| Container | Processo roda como usuário sem privilégios, não root |
| Política de senha | Comprimento mínimo, sem exigência de caractere especial — conforme **NIST SP 800-63B**, que abandonou regras de composição por produzirem senhas piores |

---

## Documentação

| Documento | Conteúdo |
|---|---|
| [`docs/arquitetura.md`](docs/arquitetura.md) | Padrão MVC, diagrama, fluxo de requisição, testabilidade |
| [`docs/rastreabilidade.md`](docs/rastreabilidade.md) | História → RF → RN → Código; decisões e correções do backlog |
| [`docs/manual-do-usuario.md`](docs/manual-do-usuario.md) | Manual de uso |
| [`frontend/README.md`](frontend/README.md) | Estrutura do front-end, decisões e testes |


## Créditos
Fotos do catálogo: [Unsplash](https://unsplash.com) / [Pexels](https://pexels.com), licença livre.