"use client";

import { SEQUENCIA_STATUS, rotuloStatus } from "@/lib/formato";
import type { StatusPedido } from "@/lib/tipos";

/**
 * Linha do tempo do pedido. Historia ID 08 / RF-14.
 *
 * Desenha a FSM (Finite State Machine) do back-end como progressao
 * visual. A ordem NAO e inventada aqui: vem de `SEQUENCIA_STATUS`, que
 * espelha a tabela `TRANSICOES_PERMITIDAS` do dominio.
 *
 * Caso real: e o mesmo recurso de "Pedido confirmado -> Em preparo ->
 * Saiu para entrega" que aplicativos de delivery mostram. A pessoa que
 * acabou de pagar quer saber em que etapa esta sem precisar ligar para a
 * loja - e cada ligacao economizada e custo de atendimento que nao
 * acontece.
 *
 * `cancelado` nao pertence a sequencia: e um desvio, nao uma etapa. Por
 * isso ganha tratamento proprio em vez de virar um sexto circulo que
 * nunca acende.
 */
export function LinhaDoTempo({ status }: { status: StatusPedido }) {
  if (status === "cancelado") {
    return (
      <div className="rounded-lg border border-tinta-suave/30 bg-papel-fundo px-4 py-3">
        <p className="font-display text-media">Pedido cancelado</p>
        <p className="mt-1 text-minuscula text-tinta-suave">
          Este pedido não será entregue.
        </p>
      </div>
    );
  }

  const atual = SEQUENCIA_STATUS.indexOf(status);

  return (
    <ol className="flex flex-col gap-0">
      {SEQUENCIA_STATUS.map((etapa, i) => {
        const concluida = i < atual;
        const corrente = i === atual;
        const ultima = i === SEQUENCIA_STATUS.length - 1;

        return (
          <li key={etapa} className="flex gap-4">
            <div className="flex flex-col items-center">
              <span
                aria-hidden="true"
                className={`mt-1 size-3.5 shrink-0 rounded-full border-2 ${
                  corrente
                    ? "border-framboesa bg-framboesa"
                    : concluida
                      ? "border-framboesa bg-papel"
                      : "border-tinta-suave/30 bg-papel"
                }`}
              />
              {!ultima && (
                <span
                  aria-hidden="true"
                  className={`w-0.5 flex-1 ${
                    concluida ? "bg-framboesa" : "bg-tinta-suave/20"
                  }`}
                />
              )}
            </div>

            <div className={ultima ? "pb-0" : "pb-6"}>
              <p
                className={
                  corrente
                    ? "font-display text-media text-framboesa"
                    : concluida
                      ? "text-tinta"
                      : "text-tinta-suave"
                }
              >
                {rotuloStatus(etapa)}
              </p>
              {/* `aria-current` diz ao leitor de tela qual etapa e a de
                  agora. Sem isso, quem nao enxerga a cor ouve quatro
                  rotulos iguais e nao sabe onde o pedido esta. */}
              {corrente && (
                <p aria-current="step" className="text-minuscula text-tinta-suave">
                  Etapa atual
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
