/**
 * Tipos do contrato da API.
 *
 * Escritos a mao por ora. Quando o back estiver estavel, substituir por
 * geracao automatica:
 *   npm run gen:api
 * que roda `openapi-typescript` contra /openapi.json. Manter a mao e
 * aceitar que front e back divirjam em silencio.
 */

export type StatusPedido =
  | "recebido"
  | "em_preparo"
  | "saiu_para_entrega"
  | "entregue"
  | "cancelado";

export interface Usuario {
  id: string;
  nome: string;
  email: string;
}

export interface Cupcake {
  id: string;
  nome: string;
  descricao: string;
  sabor: string;
  /** String, nao number. Ver lib/formato.ts. */
  preco: string;
  imagem_url: string;
  disponivel: boolean;
}

export interface ItemCarrinho {
  cupcake_id: string;
  nome: string;
  preco_unitario: string;
  quantidade: number;
  /** Ja calculado pelo servidor. Nunca recalcular aqui. */
  subtotal: string;
}

export interface Carrinho {
  itens: ItemCarrinho[];
  total: string;
  quantidade_itens: number;
}

export interface Pedido {
  id: string;
  itens: ItemCarrinho[];
  endereco_entrega: string;
  total: string;
  status: StatusPedido;
}

export interface PedidoResumo {
  id: string;
  total: string;
  status: StatusPedido;
  quantidade_itens: number;
}
