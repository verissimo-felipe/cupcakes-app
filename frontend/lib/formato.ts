import type { StatusPedido } from "./tipos";

/**
 * Formatacao de valores monetarios.
 *
 * POR QUE OS PRECOS CHEGAM COMO STRING
 * ------------------------------------
 * O back-end usa `Decimal` e o Pydantic o serializa como string, para nao
 * perder precisao. O JSON entrega `"17.00"`, nao `17.00`.
 *
 * Isso e proposital e nao deve ser "corrigido": ponto flutuante binario
 * nao representa 0,10 exatamente, e somar itens em `number` acumularia
 * centavos de erro ate a nota nao fechar.
 *
 * Consequencia pratica: NUNCA faca aritmetica com esses valores aqui.
 * Subtotais e totais ja vem somados do servidor. Esta funcao so converte
 * para exibicao, no ultimo momento possivel.
 */
export function formatarPreco(valor: string): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(Number(valor));
}

const ROTULOS_STATUS: Record<StatusPedido, string> = {
  recebido: "Recebido",
  em_preparo: "Em preparo",
  saiu_para_entrega: "Saiu para entrega",
  entregue: "Entregue",
  cancelado: "Cancelado",
};

export function rotuloStatus(status: StatusPedido): string {
  return ROTULOS_STATUS[status];
}

/** Ordem da FSM do back-end, para desenhar a linha do tempo. */
export const SEQUENCIA_STATUS: StatusPedido[] = [
  "recebido",
  "em_preparo",
  "saiu_para_entrega",
  "entregue",
];

/**
 * Data e hora no fuso de QUEM ESTA OLHANDO.
 *
 * O servidor guarda e devolve em UTC (Coordinated Universal Time), com o
 * fuso explicito na string. O `Date` do navegador converte para o fuso
 * local sozinho - a cozinha em Brasilia ve 14:45, nao 17:45.
 */
export function formatarDataHora(iso: string | null): string {
  if (!iso) return "—";
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(iso));
}

/**
 * Os 8 primeiros caracteres do UUID (Universally Unique Identifier).
 *
 * Bastam para uma pessoa reconhecer e citar o pedido ao telefone: 16^8
 * sao ~4 bilhoes de combinacoes. O identificador COMPLETO continua sendo
 * o que vai na URL e na API.
 */
export function idCurto(id: string): string {
  return id.slice(0, 8);
}

/**
 * Rotulo do botao que LEVA a cada etapa - verbo de quem esta na cozinha,
 * nao o nome do estado. "Iniciar preparo" diz o que o clique faz;
 * "Avancar para em preparo" obriga a pessoa a traduzir.
 */
const ROTULOS_ACAO: Partial<Record<StatusPedido, string>> = {
  em_preparo: "Iniciar preparo",
  saiu_para_entrega: "Enviar para entrega",
  entregue: "Confirmar entrega",
};

export function rotuloAvancar(destino: StatusPedido): string {
  return ROTULOS_ACAO[destino] ?? `Avançar para ${rotuloStatus(destino).toLowerCase()}`;
}
