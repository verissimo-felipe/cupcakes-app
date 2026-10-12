# Front-end — Doce Forma

Interface web da loja de cupcakes. No mapeamento MVC do projeto, é a
**View**: apresenta os dados e captura a entrada do usuário, enquanto
regras de negócio e autorização vivem no back-end
(ver [`../docs/arquitetura.md`](../docs/arquitetura.md)).

**Stack:** Next.js 16 (App Router) · React 19 · TypeScript · Tailwind CSS 4

---

## Como rodar

Pré-requisito: Node.js **20.19+** ou **22.13+** (exigência do Vite e do
jsdom usados nos testes) e a API rodando em `http://localhost:8000`.

```bash
npm install
npm run dev                          # http://localhost:3000
```

**Como o front encontra a API.** O navegador chama `/api/v1/...` no
próprio endereço do front, e o Next repassa para a API (proxy definido
em `next.config.ts`). Assim o cookie de sessão fica no mesmo site do
front — requisito para o login funcionar quando front e API estão em
domínios diferentes, como em produção.

| Variável | Onde é lida | Padrão | Uso |
|---|---|---|---|
| `API_URL` | servidor do Next, **no build** | `http://localhost:8000` | Destino do proxy. Em produção, a URL do back-end |
| `NEXT_PUBLIC_API_URL` | navegador | *(vazia)* | Opcional. Se definida, o navegador fala direto com a API, sem proxy — útil só em desenvolvimento |

| Comando | O que faz |
|---|---|
| `npm run dev` | Servidor de desenvolvimento |
| `npm test` | Roda a suíte de testes uma vez |
| `npm run test:watch` | Testes em modo observação, a cada arquivo salvo |
| `npm run lint` | ESLint |
| `npm run build` | Build de produção |

---

## Estrutura

```
frontend/
├── app/                    # uma pasta por rota (App Router)
│   ├── page.tsx            # /              catálogo e busca
│   ├── login/              # /login
│   ├── registrar/          # /registrar
│   ├── carrinho/           # /carrinho
│   ├── checkout/           # /checkout
│   ├── pedidos/            # /pedidos e /pedidos/[id] — acompanhamento
│   └── loja/pedidos/       # /loja/pedidos e /loja/pedidos/[id] — gestão (equipe)
├── componentes/            # peças reutilizadas entre telas
├── lib/
│   ├── api.ts              # ÚNICO ponto de contato com a API
│   ├── tipos.ts            # contrato de dados da API
│   ├── formato.ts          # moeda, datas, rótulos
│   └── navegacao.ts        # validação de redirecionamento
└── testes/                 # Vitest + React Testing Library
```

| Rota | Tela | História |
|---|---|---|
| `/registrar`, `/login` | Cadastro e login | ID 01, 02 |
| `/` | Catálogo com busca | ID 04 |
| `/carrinho` | Carrinho | ID 05, 06 |
| `/checkout` | Finalização | ID 07 |
| `/pedidos`, `/pedidos/[id]` | Acompanhamento do pedido | ID 08 |
| `/loja/pedidos`, `/loja/pedidos/[id]` | Gestão de pedidos pela loja | extensão do RF-15 |

---

## Decisões

**Sessão em cookie `httpOnly`, telas como Client Components.** O token
de sessão é invisível ao JavaScript — um XSS não consegue roubá-lo. Como o
navegador anexa o cookie sozinho, as telas que dependem de sessão rodam
no navegador. `lib/api.ts` envia `credentials: "include"` em toda chamada;
sem isso, front (porta 3000) e API (porta 8000) não compartilhariam o
cookie.

**Um único cliente de API.** Nenhuma tela chama `fetch` diretamente. O
wrapper converte os três formatos de erro da API em um único `ErroApi`
com `codigo` e `mensagem`, e transforma falha de rede em mensagem
compreensível.

**Valores monetários chegam como texto e não são somados aqui.** A API
envia `"17.00"`, não `17.00`, para não perder precisão. Subtotais e totais
vêm calculados do servidor; o front só formata para exibição.

**O servidor decide quais botões aparecem.** Na área da loja, cada pedido
chega com `acoes` (`proximo_status`, `pode_cancelar`,
`pode_editar_endereco`, `pode_excluir`), calculadas pelo domínio. A tela
não reimplementa a máquina de estados do pedido.

**Esconder não é proteger.** A tela da loja esconde o conteúdo de quem
não é da equipe, mas a barreira real é o servidor, que responde 403. O
mesmo vale para qualquer verificação feita aqui.

**Acessibilidade.** Erros com `role="alert"` (lidos assim que aparecem),
etapa atual do pedido com `aria-current="step"`, filtros com
`aria-pressed`, tabela semântica na lista da loja, foco visível em tudo
que recebe teclado e respeito a `prefers-reduced-motion`. Status nunca
depende só de cor: o texto está sempre presente.

---

## Testes

```bash
npm test
```

53 testes em 10 arquivos, rodando em poucos segundos e **sem precisar do
back-end**: o `fetch`, o roteador do Next e a sessão são substituídos
por dublês, e os componentes renderizam num navegador simulado (jsdom).

| Arquivo | O que verifica |
|---|---|
| `lib/api.test.ts` | Cookie enviado em toda chamada; checkout envia só o endereço; os 3 formatos de erro; servidor fora do ar |
| `lib/navegacao.test.ts` | Bloqueio de *open redirect* (CWE-601) em `?voltar=` |
| `lib/formato.test.ts` | Moeda em reais, rótulos de etapa e de ação |
| `componentes/CardCupcake.test.tsx` | Esgotado sem botão de adicionar; quantidade entre 1 e 99; foto ausente |
| `componentes/AreaDaLoja.test.tsx` | Visitante vai ao login; cliente vê área restrita; loja vê o conteúdo |
| `componentes/LinhaDoTempo.test.tsx` | Ordem das etapas; etapa atual anunciada a leitor de tela; cancelado |
| `telas/login.test.tsx` | Credencial errada mostra mensagem genérica; redireciona só para caminho interno |
| `telas/carrinho.test.tsx` | Rota protegida; total exibido é o do servidor; alteração usa a resposta da API |
| `telas/loja-pedidos.test.tsx` | Lista de todos os clientes; botões conforme `acoes`; filtro; recusa 409 |
| `telas/loja-pedido.test.tsx` | Avançar, cancelar, corrigir endereço, excluir com confirmação; endereço travado após saída |

Os testes buscam elementos pelo que o usuário enxerga — papel e nome
acessível (`getByRole("button", { name: "Adicionar" })`) — e não por
classes CSS. Um teste que encontra o botão do jeito que um leitor de tela
encontra também verifica, de quebra, que o botão é acessível.

**Um bug encontrado pelos testes.** O campo de quantidade do card
corrigia o valor a cada tecla: quem apagava o "1" para digitar "3" via o
"1" voltar e terminava com 13. O teste que digita como uma pessoa
(`userEvent`) reproduziu o problema; a correção passou a validar só ao
sair do campo ou ao clicar em Adicionar. O teste de regressão continua na
suíte.

### Limitações conhecidas

- O jsdom não aplica CSS. O layout responsivo foi verificado
  tela a tela, em 390 px de largura (tamanho de celular), com a aplicação
  rodando de verdade.
- Não há testes ponta a ponta (navegador real + API real). O próximo passo
  natural seria Playwright cobrindo o fluxo de compra completo.
