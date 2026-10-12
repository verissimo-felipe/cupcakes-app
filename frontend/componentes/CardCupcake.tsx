"use client";

import { useState } from "react";
import { formatarPreco } from "@/lib/formato";
import type { Cupcake } from "@/lib/tipos";

/**
 * Card de produto.
 *
 * Usa <img> e nao next/image de proposito: as fotos ainda nao existem em
 * public/images/cupcakes/. O next/image quebraria o build com arquivo
 * local ausente; com <img> a tela continua funcional e cai no marcador
 * abaixo. Quando as 7 fotos entrarem, vale migrar para next/image e
 * ganhar otimizacao.
 */
export function CardCupcake({
  cupcake,
  aoAdicionar,
}: {
  cupcake: Cupcake;
  aoAdicionar: (id: string, quantidade: number) => Promise<void>;
}) {
  const [quantidade, setQuantidade] = useState(1);
  const [enviando, setEnviando] = useState(false);
  const [semImagem, setSemImagem] = useState(false);

  async function adicionar() {
    setEnviando(true);
    try {
      await aoAdicionar(cupcake.id, quantidade);
      setQuantidade(1);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <article className="flex flex-col overflow-hidden rounded-xl bg-papel-fundo">
      <div className="relative aspect-4/3 bg-ameixa-claro">
        {semImagem ? (
          <div className="flex h-full items-center justify-center font-display text-grande text-papel/40">
            {cupcake.sabor}
          </div>
        ) : (
          <img
            src={cupcake.imagem_url}
            alt={cupcake.nome}
            onError={() => setSemImagem(true)}
            className="h-full w-full object-cover"
          />
        )}

        {!cupcake.disponivel && (
          <span className="absolute top-3 left-3 rounded-full bg-ameixa px-3 py-1 text-minuscula text-papel">
            Esgotado
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-2 p-5">
        <h3 className="font-display text-media leading-tight">{cupcake.nome}</h3>
        <p className="flex-1 text-minuscula leading-relaxed text-tinta-suave">
          {cupcake.descricao}
        </p>

        <p className="font-display text-grande text-framboesa">
          {formatarPreco(cupcake.preco)}
        </p>

        {cupcake.disponivel ? (
          <div className="mt-2 flex items-center gap-2">
            <label className="sr-only" htmlFor={`qtd-${cupcake.id}`}>
              Quantidade de {cupcake.nome}
            </label>
            <input
              id={`qtd-${cupcake.id}`}
              type="number"
              min={1}
              max={99}
              value={quantidade}
              onChange={(e) =>
                setQuantidade(Math.max(1, Number(e.target.value) || 1))
              }
              className="w-16 rounded-lg border border-tinta-suave/30 bg-papel px-2 py-2 text-center"
            />
            <button
              onClick={adicionar}
              disabled={enviando}
              className="flex-1 rounded-lg bg-framboesa px-4 py-2 text-papel transition-colors hover:bg-framboesa-escuro disabled:opacity-50"
            >
              {enviando ? "Adicionando…" : "Adicionar"}
            </button>
          </div>
        ) : (
          /* Sem botao quando esgotado. Desabilitar o botao seria pior:
             convida ao clique e depois recusa. A ausencia comunica melhor. */
          <p className="mt-2 rounded-lg bg-papel px-4 py-2 text-center text-minuscula text-tinta-suave">
            Voltamos a produzir em breve
          </p>
        )}
      </div>
    </article>
  );
}
