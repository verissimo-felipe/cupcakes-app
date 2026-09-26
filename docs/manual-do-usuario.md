# Manual de Uso — Loja de Cupcakes

Guia de utilização do sistema para o usuário final.

> **Nota de preenchimento:** os marcadores `[CAPTURA: ...]` indicam onde
> inserir as imagens de tela após a implementação da interface. Remova
> esta nota antes da entrega.

---

## 1. Sobre o sistema

A Loja de Cupcakes é uma aplicação web que permite ao cliente navegar pelo
catálogo de produtos, montar um pedido, finalizar a compra e acompanhar a
entrega.

O sistema funciona em navegador, sem instalação. Recomendado: Chrome,
Firefox ou Edge em versão atual.

---

## 2. Primeiro acesso — criar conta

Para comprar é necessário ter conta. A criação leva menos de um minuto.

1. Na tela inicial, clique em **Criar conta**
2. Preencha nome, e-mail e senha
3. Confirme a senha
4. Clique em **Cadastrar**

`[CAPTURA: tela de cadastro preenchida]`

### Regras de senha

| Regra | Valor |
|---|---|
| Comprimento mínimo | 8 caracteres |
| Caractere especial | não exigido |
| Diferenciação de maiúsculas | sim |

O sistema não exige símbolos na senha. Essa escolha segue a recomendação
atual de segurança, que prioriza senhas mais longas em vez de regras de
composição — que costumam levar o usuário a criar variações previsíveis.

### Mensagens possíveis

| Mensagem | O que significa | O que fazer |
|---|---|---|
| E-mail já cadastrado | Já existe conta com esse endereço | Use **Entrar** ou recupere a senha |
| Senha muito curta | Menos de 8 caracteres | Escolha uma senha mais longa |
| As senhas não conferem | Confirmação divergente | Digite novamente nos dois campos |

---

## 3. Entrar no sistema

1. Clique em **Entrar**
2. Informe e-mail e senha
3. Clique em **Acessar**

`[CAPTURA: tela de login]`

A sessão permanece ativa por 30 minutos de inatividade. Após esse período
o sistema solicita novo login — medida de segurança para proteger a conta
em computadores compartilhados.

Se as credenciais estiverem incorretas, o sistema exibe **E-mail ou senha
inválidos**, sem indicar qual dos dois está errado. Isso é intencional:
informar qual campo falhou permitiria a um terceiro descobrir quais
e-mails possuem conta no sistema.

---

## 4. Navegar pelo catálogo

A página principal exibe os cupcakes disponíveis, cada um com foto, nome,
descrição, sabor e preço.

`[CAPTURA: catálogo com os cards de produto]`

| Recurso | Como usar |
|---|---|
| Ver detalhes | Clique sobre o card do cupcake |
| Buscar | Campo de busca no topo; digite nome ou sabor |
| Produto esgotado | Aparece marcado, sem botão de adicionar |

---

## 5. Adicionar ao carrinho

1. Localize o cupcake desejado
2. Ajuste a quantidade, se quiser mais de uma unidade
3. Clique em **Adicionar ao carrinho**

`[CAPTURA: card com o seletor de quantidade]`

O contador do carrinho, no topo da tela, é atualizado imediatamente.

**Comportamento ao repetir um produto:** se você adicionar o mesmo cupcake
duas vezes, o sistema **soma as quantidades** na linha existente em vez de
criar uma segunda linha. Adicionar 2 e depois 3 resulta em uma única linha
com 5 unidades.

### Mensagens possíveis

| Mensagem | Motivo |
|---|---|
| Quantidade deve ser no mínimo 1 | Tentativa de adicionar zero ou valor negativo |
| Cupcake indisponível | Produto sem estoque no momento |

---

## 6. Gerenciar o carrinho

Clique no ícone do carrinho para abrir o resumo.

`[CAPTURA: carrinho com dois ou mais itens]`

| Ação | Como fazer |
|---|---|
| Alterar quantidade | Use os botões **+** e **−** na linha do item |
| Remover item | Clique no ícone de lixeira |
| Continuar comprando | Botão **Voltar ao catálogo** |
| Finalizar | Botão **Finalizar pedido** |

O subtotal de cada linha e o total geral são recalculados a cada
alteração.

Para remover um produto, use a lixeira — reduzir a quantidade até zero não
é aceito, porque o sistema trata "quantidade zero" como entrada inválida,
não como remoção. A separação evita exclusão acidental.

---

## 7. Finalizar o pedido

1. No carrinho, clique em **Finalizar pedido**
2. Informe o endereço de entrega
3. Escolha a forma de pagamento
4. Revise o resumo do pedido
5. Confirme

`[CAPTURA: tela de checkout com resumo]`

Após a confirmação o sistema exibe o número do pedido. **Anote-o** — é ele
que identifica a compra no acompanhamento.

> **Ambiente de demonstração:** o pagamento opera em modo de teste. Nenhuma
> cobrança real é efetuada e nenhum dado de cartão verdadeiro deve ser
> informado.

### Mensagens possíveis

| Mensagem | Motivo |
|---|---|
| Carrinho vazio | Não há itens para finalizar |
| Endereço obrigatório | Campo de entrega não preenchido |

---

## 8. Acompanhar o pedido

Acesse **Meus pedidos** no menu da conta.

`[CAPTURA: tela de acompanhamento]`

O pedido percorre os seguintes estados:

| Estado | Significado |
|---|---|
| Recebido | Pedido registrado, aguardando produção |
| Em preparo | Cupcakes sendo produzidos |
| Saiu para entrega | A caminho do endereço informado |
| Entregue | Concluído |
| Cancelado | Cancelado antes da saída para entrega |

A progressão é sequencial: um pedido não pula de **Recebido** direto para
**Entregue**. O cancelamento é possível enquanto o pedido não tiver saído
para entrega; depois disso, apenas a conclusão.

---

## 9. Funcionalidades previstas para versões futuras

Esta versão entrega o fluxo completo de compra. As funcionalidades abaixo
constam do planejamento e não estão disponíveis:

| Funcionalidade |
|---|
| Redefinição de senha por e-mail |
| Avaliação de produtos |
| Histórico completo de pedidos |
| Cupons de desconto |
| Notificações push |
| Edição de perfil |
| Busca avançada com filtros |
| Chat de suporte |

---

## 10. Problemas comuns

| Situação | Solução |
|---|---|
| Página não carrega | Verifique a conexão e atualize com `Ctrl+F5` |
| Sessão expirou | Faça login novamente |
| Carrinho aparece vazio após login | O carrinho é vinculado à conta; confirme que entrou com o mesmo e-mail |
| Botão de adicionar desabilitado | Produto esgotado |
