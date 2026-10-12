"use client";

import { useState } from "react";
import { idCurto } from "@/lib/formato";

/**
 * Numero do pedido com botao de copiar o identificador COMPLETO.
 *
 * Caso real: o cliente liga dizendo "meu pedido 3f9a1c07 nao chegou". A
 * atendente acha pelos 8 caracteres na tela; se precisar abrir chamado
 * com o entregador ou consultar o banco, copia o UUID inteiro com um
 * clique - sem selecionar texto na mao e sem risco de cortar um digito.
 *
 * `navigator.clipboard` so existe em contexto seguro (HTTPS ou
 * localhost). Fora dele, o `catch` mostra o id completo para a pessoa
 * copiar manualmente, em vez de o botao falhar calado.
 */
export function IdPedido({
  id,
  grande = false,
}: {
  id: string;
  grande?: boolean;
}) {
  const [estado, setEstado] = useState<"parado" | "copiado" | "manual">(
    "parado",
  );

  async function copiar() {
    try {
      await navigator.clipboard.writeText(id);
      setEstado("copiado");
      setTimeout(() => setEstado("parado"), 1800);
    } catch {
      setEstado("manual");
    }
  }

  return (
    <span className="inline-flex flex-wrap items-center gap-2">
      <span
        title={id}
        className={`font-mono tabular-nums ${grande ? "text-media" : "text-minuscula"}`}
      >
        #{idCurto(id)}
      </span>
      <button
        type="button"
        onClick={copiar}
        aria-label={`Copiar identificador completo do pedido ${idCurto(id)}`}
        className="rounded-md border border-tinta-suave/30 px-2 py-0.5 text-minuscula text-tinta-suave hover:border-ameixa hover:text-ameixa"
      >
        {estado === "copiado" ? "Copiado" : "Copiar ID"}
      </button>
      {/* `aria-live` anuncia o "Copiado" para leitor de tela; sem ele, o
          retorno do clique so existiria para quem enxerga o botao. */}
      <span aria-live="polite" className="sr-only">
        {estado === "copiado" ? "Identificador copiado" : ""}
      </span>
      {estado === "manual" && (
        <code className="w-full select-all break-all rounded bg-papel-fundo px-2 py-1 text-minuscula">
          {id}
        </code>
      )}
    </span>
  );
}
