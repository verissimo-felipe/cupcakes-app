# Matriz de Rastreabilidade

Liga **História de Usuário → Requisito Funcional → Regra de Negócio → Código**.

Fonte dos artefatos de planejamento: board Miro *Proj Faculdade Loja de cupcakes*
(Frames 1–6: Cartões, Mapa de Afinidade, Backlog, Requisitos, Tarefas, Roadmap).

---

## 1. Correção aplicada ao backlog

Durante a revisão foi identificada uma inconsistência na história **ID 05**.

**Estado anterior:** ID 05 constava como *Pagamento*, com épico próprio
(E4), requisito RF-11 e tarefas T5.1–T5.6.

**Problema:** o cartão de história ID 05 descreve *Adição de Cupcakes ao
Carrinho*. Além disso, RF-08 (adicionar/remover itens) apontava
integralmente para ID 06, cujo título é *Remoção Carrinho* — ou seja, a
ação de **adicionar** não tinha história de origem declarada.

**Correção:**

| Item | Antes | Depois | Justificativa |
|---|---|---|---|
| História ID 05 | Pagamento | **Adicionar ao Carrinho** | Corresponde ao cartão de história |
| RF-08 | Origem ID 06 | **Adicionar → ID 05 · Remover → ID 06** | Separa as duas ações |
| RF-11 (formas de pagamento) | Origem ID 05 | **Origem ID 07** | RF-12 já ancora pagamento no checkout (ID 07) |
| Épico E4 – Pagamento | 5 pts, história 05 | **Dissolvido em E3** | Épico ficaria sem história |
| Épico E3 – Carrinho e Finalização | 11 pts | **16 pts** | Absorve E4 |
| Tarefas T5.1–T5.6 | Grupo G4 | **Grupo G3** | Segue o épico |

Total de pontos preservado: **50**. Nenhum requisito órfão.

**Consequência arquitetural:** pagamento deixa de ser *bounded context*
independente e passa a ser um passo do checkout. Menos abstração para
sustentar, e o fluxo de compra vira um agregado coeso.

### Pendência conhecida

**RF-21** (chat de suporte em tempo real) permanece sem campo *Origem*
preenchido no board. Deveria apontar para **ID 15 – Chat de Suporte**
(tarefas T15.1–T15.5). Fora do escopo desta entrega; registrado para
correção documental.

---

## 2. Escopo implementado — fatia vertical

Das 15 histórias planejadas, esta entrega implementa **5**, escolhidas por
formarem um fluxo contínuo de ponta a ponta (autenticar → navegar →
comprar → acompanhar). O critério não foi ordem de sprint, e sim
continuidade funcional: um recorte horizontal (só os Sprints 1 e 2)
entregaria catálogo sem carrinho, isto é, um e-commerce onde não se compra.

| História | Título | Épico | RFs cobertos |
|---|---|---|---|
| ID 01 / 02 | Cadastro e Login | E1 | RF-01, RF-03 |
| ID 04 | Catálogo | E2 | RF-05, RF-06 |
| ID 05 | Adicionar ao Carrinho | E3 | RF-08, RF-09 |
| ID 06 | Remover do Carrinho | E3 | RF-08 |
| ID 07 | Finalização / Checkout | E3 | RF-12, RF-13 |
| ID 08 | Rastreamento | E5 | RF-14, RF-15 |
| ID 08 (extensão) | Gestão de pedidos pela loja | E5 | RF-15 |

### Backlog priorizado — não implementado nesta sprint

ID 03 (Redefinição de Senha), ID 09 (Avaliação), ID 10 (Histórico),
ID 11 (Cupons), ID 12 (Notificações Push), ID 13 (Perfil),
ID 14 (Pesquisa), ID 15 (Chat de Suporte).

O roadmap completo (5 sprints / 10 semanas) permanece no board Miro.

---

## 3. Regras de negócio no código

Cada regra vive em `backend/app/domain/` e tem teste dedicado em
`backend/tests/` (domínio, serviço ou API, conforme onde a regra é
observável).

| RN | Descrição | História | Implementação | Teste |
|---|---|---|---|---|
| RN-01 | Quantidade mínima por item é 1 | ID 05 | `Carrinho.adicionar` | `test_rn01_quantidade_zero_e_recusada` |
| RN-02 | Cupcake indisponível é recusado | ID 05 | `Carrinho.adicionar` | `test_rn02_cupcake_indisponivel_e_recusado` |
| RN-03 | Remover item ausente é erro | ID 06 | `Carrinho.remover` | `test_rn03_remover_ausente_levanta_erro` |
| RN-04 | Carrinho vazio não vira pedido | ID 07 | `Pedido.a_partir_do_carrinho` | `test_rn04_carrinho_vazio_nao_vira_pedido` |
| RN-05 | Status do pedido segue FSM | ID 08 | `TRANSICOES_PERMITIDAS` | `test_rn05_nao_pula_etapa` |
| RN-06 | Item repetido soma, não duplica | ID 05 | `Carrinho.adicionar` | `test_rn06_item_repetido_soma_em_vez_de_duplicar` |
| RN-07 | Senha com no mínimo 8 caracteres | ID 01 | `Usuario.validar_senha_plana` | `test_rn07_senha_curta_e_recusada` |
| RN-07b | Senha com no máximo 72 bytes | ID 01 | `Usuario.validar_senha_plana` | `test_rn07b_senha_acima_de_72_bytes_e_recusada` |
| RN-08 | E-mail normalizado (minúsculas, sem espaços) | ID 01 | `Usuario.normalizar_email` | `test_cadastro_normaliza_email` |
| RN-09 | Um e-mail, uma conta | ID 01 | `AutenticacaoService.cadastrar` + índice único | `test_email_duplicado_e_recusado_mesmo_com_caixa_diferente` |
| RN-10 | Login falho não revela qual campo errou | ID 02 | `CredenciaisInvalidasError` | `test_rn10_email_inexistente_e_senha_errada_dao_o_mesmo_erro` |
| RN-11 | Endereço só muda antes de o pedido sair para entrega | ID 08 | `Pedido.alterar_endereco` | `test_rn11_endereco_travado_depois_de_sair_para_entrega` |
| RN-12 | Endereço precisa de ao menos 5 caracteres úteis | ID 07, 08 | `_validar_endereco` | `test_rn12_checkout_tambem_recusa_endereco_vazio` |
| RN-13 | Só pedido entregue ou cancelado pode ser excluído; a exclusão é lógica | ID 08 | `Pedido.excluir` | `test_rn13_pedido_em_andamento_nao_pode_ser_excluido` |

### Extensão do RF-15 — gestão de pedidos pela loja

O RF-15 previa que a loja atualizasse o status do pedido. Na validação do
fluxo, ficou claro que a loja precisa de mais do que isso para operar:
ver os pedidos de **todos** os clientes, identificar cada um pelo número,
corrigir endereço digitado errado e retirar da lista pedidos de teste ou
duplicados.

| Necessidade da loja | Rota | Regra |
|---|---|---|
| Ver todos os pedidos, com cliente, data e número | `GET /api/v1/admin/pedidos` | — |
| Filtrar a fila por etapa | `GET /api/v1/admin/pedidos?status=` | — |
| Avançar uma etapa ("acelerar a entrega") | `POST /api/v1/admin/pedidos/{id}/avancar` | RN-05 |
| Cancelar | `POST /api/v1/admin/pedidos/{id}/cancelar` | RN-05 |
| Corrigir o endereço | `PATCH /api/v1/admin/pedidos/{id}` | RN-11, RN-12 |
| Excluir (lógico) | `DELETE /api/v1/admin/pedidos/{id}` | RN-13 |

Não há cartão de história próprio para esta extensão. Fica registrada
como candidata a **ID 16 – Gestão de Pedidos pela Loja** no backlog, para
reconciliação com o board.

**Por que exclusão lógica:** pedido é registro de venda. A linha continua
no banco com `excluido_em` preenchido, e só deixa de aparecer na
aplicação. Apagar fisicamente faria o faturamento deixar de bater com o
caixa e eliminaria a trilha de auditoria.

---

## 4. Requisitos não funcionais — decisões técnicas

| RNF | Exigência | Decisão | Justificativa |
|---|---|---|---|
| RNF-01 | Login ≤ 2s | JWT stateless | Sem consulta a sessão no banco por request |
| RNF-04 | Busca ≤ 1s | PostgreSQL FTS (`tsvector` + GIN) | Catálogo de dezenas de itens; Elasticsearch seria cluster ocioso |
| RNF-05 | Carrinho instantâneo | Estado otimista no cliente | Atualiza UI antes da confirmação do servidor |
| RNF-06 | Transações cifradas | HTTPS/TLS em produção | Local usa HTTP; documentado no README |
| RNF-11 | Senha sem caractere especial | Comprimento mínimo 8 | **NIST SP 800-63B** abandonou regras de composição: elas produzem senhas piores (`Senha@123`) |

### Substituições em relação ao plano original

O board previa Elasticsearch, WebSockets, Firebase Cloud Messaging,
Zendesk e três gateways de pagamento. Dimensionamento incompatível com
uma entrega de 2 semanas por um desenvolvedor. Substituições:

| Planejado | Adotado | Razão |
|---|---|---|
| Elasticsearch | PostgreSQL FTS | Volume não justifica cluster separado |
| WebSocket (rastreio) | SSE — Server-Sent Events | Fluxo é unidirecional; WS é full-duplex desnecessário |
| Stripe/PagSeguro/PIX | Stripe modo teste | PIX real exige contrato com PSP e CNPJ |
| Firebase Cloud Messaging | Notificação in-app | Evita service account key adicional |
| Zendesk/Intercom | Fora de escopo | Backlog |

Escolher o mecanismo mais simples que satisfaz o requisito é decisão de
arquitetura, e está registrada aqui como tal.
