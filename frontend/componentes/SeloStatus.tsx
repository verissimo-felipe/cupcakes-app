import { rotuloStatus } from "@/lib/formato";
import type { StatusPedido } from "@/lib/tipos";

/**
 * Etiqueta de status.
 *
 * Framboesa fica de fora de proposito: ela e a cor de ACAO do sistema
 * (ver globals.css). Se o status tambem fosse framboesa, o olho nao
 * saberia mais o que e botao e o que e informacao.
 *
 * A cor nunca carrega o significado sozinha - o texto esta sempre la.
 * Cerca de 8% dos homens tem algum grau de daltonismo; para eles, um
 * selo so colorido seria um selo vazio.
 */
const ESTILO: Record<StatusPedido, string> = {
  recebido: "bg-papel-fundo text-ameixa ring-1 ring-inset ring-ameixa/25",
  em_preparo: "bg-buttercream text-ameixa",
  saiu_para_entrega: "bg-ameixa text-papel",
  entregue:
    "bg-emerald-50 text-emerald-800 ring-1 ring-inset ring-emerald-700/20",
  cancelado: "bg-papel-fundo text-tinta-suave",
};

export function SeloStatus({ status }: { status: StatusPedido }) {
  return (
    <span
      className={`inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 text-minuscula ${ESTILO[status]}`}
    >
      {rotuloStatus(status)}
    </span>
  );
}
