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

```bash
cd backend
pip install -e ".[dev]"
pytest -v
```

Resultado esperado: **11 passed in 0.03s**. Os testes de regra de negócio
rodam sem banco e sem servidor — consequência direta da arquitetura.

---

## Estrutura

```
cupcakes-app/
├── docker-compose.yml
├── .env.example              # .env real nunca vai para o Git
├── docs/
│   ├── arquitetura.md        # padrão MVC — justificativa e diagrama
│   ├── rastreabilidade.md    # História → RF → RN → Código
│   ├── manual-do-usuario.md
│   └── RECAP.md
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
```

---

## Escopo desta entrega

Das 15 histórias planejadas, **6 foram implementadas**, escolhidas por
formarem um fluxo contínuo de compra:

`Cadastro/Login (01, 02) → Catálogo (04) → Carrinho (05, 06) → Checkout (07) → Rastreamento (08)`

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
| [`docs/RECAP.md`](docs/RECAP.md) | Reconstituição do desenvolvimento |


## Créditos
Fotos do catálogo: [Unsplash](https://unsplash.com) / [Pexels](https://pexels.com), licença livre.