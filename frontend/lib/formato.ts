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
