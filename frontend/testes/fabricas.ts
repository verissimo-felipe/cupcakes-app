/**
 * Dados de exemplo usados pelos testes.
 *
 * Fabricas em vez de objetos copiados em cada arquivo: quando o contrato
 * da API ganhar um campo, muda-se aqui, num lugar so.
 *
 * As `acoes` sao escritas a mao de proposito. O front nao calcula acoes
 * - ele so obedece o que o servidor manda. Os testes simulam o servidor
 * mandando cada combinacao e verificam que a tela obedece.
 */
import type { AcoesPedido, PedidoGestao, Usuario } from "@/lib/tipos";

export const CLIENTE: Usuario = {
  id: "u-cliente",
  nome: "Ana Cliente",
  email: "ana@mail.com",
  admin: false,
};

export const LOJA: Usuario = {
  id: "u-loja",
  nome: "Doce Forma",
  email: "loja@doceforma.com",
  admin: true,
};

export const ACOES_RECEBIDO: AcoesPedido = {
  proximo_status: "em_preparo",
  pode_cancelar: true,
  pode_editar_endereco: true,
  pode_excluir: false,
};

export const ACOES_CANCELADO: AcoesPedido = {
  proximo_status: null,
  pode_cancelar: false,
  pode_excluir: true,
  pode_editar_endereco: false,
};

export function pedidoGestao(extra: Partial<PedidoGestao> = {}): PedidoGestao {
  return {
    id: "3f9a1c07-0000-4000-8000-000000000001",
    criado_em: "2026-10-12T17:45:00+00:00",
    cliente: { nome: "Ana Cliente", email: "ana@mail.com" },
    total: "17.00",
    status: "recebido",
    quantidade_itens: 2,
    acoes: ACOES_RECEBIDO,
    itens: [
      {
        cupcake_id: "c-baunilha",
        nome: "Baunilha Clássico",
        preco_unitario: "8.50",
        quantidade: 2,
        subtotal: "17.00",
      },
    ],
    endereco_entrega: "Rua das Flores, 123",
    ...extra,
  };
}
