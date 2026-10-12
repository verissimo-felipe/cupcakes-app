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
  /**
   * Serve para a INTERFACE decidir o que desenhar, nao para autorizar.
   * A autorizacao real esta no servidor (`deps.usuario_admin`): trocar
   * este campo no DevTools libera o botao, mas a requisicao leva 403.
   */
  admin: boolean;
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

// ------------------------------------------------------------------
// Visao da LOJA - rotas /admin/pedidos
// ------------------------------------------------------------------

export interface ClienteResumo {
  nome: string;
  email: string;
}

/**
 * O que a loja pode fazer com o pedido AGORA, calculado pelo dominio no
 * back-end. A tela so le estes campos para decidir quais botoes mostrar -
 * ela nao conhece a FSM (Finite State Machine) do pedido.
 */
export interface AcoesPedido {
  /** `null` quando o pedido ja terminou (entregue ou cancelado). */
  proximo_status: StatusPedido | null;
  pode_cancelar: boolean;
  pode_editar_endereco: boolean;
  pode_excluir: boolean;
}

export interface PedidoGestaoResumo {
  id: string;
  /** ISO 8601 com fuso, ex.: "2026-10-12T17:45:00+00:00". */
  criado_em: string | null;
  cliente: ClienteResumo;
  total: string;
  status: StatusPedido;
  quantidade_itens: number;
  acoes: AcoesPedido;
}

export interface PedidoGestao extends PedidoGestaoResumo {
  itens: ItemCarrinho[];
  endereco_entrega: string;
}
