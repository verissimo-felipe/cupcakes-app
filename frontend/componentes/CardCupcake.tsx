"use client";

import { useState } from "react";
import Image from "next/image";
import { formatarPreco } from "@/lib/formato";
import type { Cupcake } from "@/lib/tipos";

// Mesmos limites do back-end: RN-01 (minimo 1) e `le=99` no schema.
const QTD_MINIMA = 1;
const QTD_MAXIMA = 99;

/**
 * Converte o que a pessoa digitou numa quantidade valida (1 a 99).
 *
 * Roda so ao SAIR do campo ou ao clicar em Adicionar - nunca a cada
 * tecla. Corrigir a cada tecla impedia apagar o "1" para digitar outro
 * numero: o campo voltava sozinho para 1, e quem queria 3 ficava com 13.
 * O teste `CardCupcake.test.tsx` reproduz exatamente esse caso.
 */
function normalizarQuantidade(texto: string): number {
  const n = Number.parseInt(texto, 10);
  if (Number.isNaN(n)) return QTD_MINIMA;
  return Math.min(QTD_MAXIMA, Math.max(QTD_MINIMA, n));
}

/**
 * Card de produto. Historias ID 04 (catalogo) e ID 05 (adicionar).
 *
 * `next/image` em vez de <img>: o Next entrega a foto no tamanho da tela
 * de quem abre (o celular nao baixa a versao de desktop), converte para
 * formatos mais leves quando o navegador aceita e adia o carregamento do
 * que ainda esta fora da tela.
 *
 * `fill` + `sizes`: a foto ocupa a caixa 4:3 do card, e `sizes` informa a
 * largura real em cada faixa de tela - o mesmo desenho do grid (1, 2 ou
 * 3 colunas). Sem `sizes`, o navegador supoe 100% da tela e baixa uma
 * foto maior que a necessaria.
 *
 * Sem foto (url vazia ou arquivo ausente), o card mostra o sabor no
 * lugar e continua utilizavel.
 */
export function CardCupcake({
  cupcake,
  aoAdicionar,
}: {
  cupcake: Cupcake;
  aoAdicionar: (id: string, quantidade: number) => Promise<void>;
}) {
  // TEXTO, nao numero: enquanto a pessoa digita, "" e um estado legitimo
  // (ela apagou para escrever outro valor). So vira numero na hora de usar.
  const [texto, setTexto] = useState("1");
  const [enviando, setEnviando] = useState(false);
  const [semImagem, setSemImagem] = useState(false);

  async function adicionar() {
    const quantidade = normalizarQuantidade(texto);
    setTexto(String(quantidade));
    setEnviando(true);
    try {
      await aoAdicionar(cupcake.id, quantidade);
      setTexto("1");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <article className="flex flex-col overflow-hidden rounded-xl bg-papel-fundo">
      <div className="relative aspect-4/3 bg-ameixa-claro">
        {/* Url vazia tambem cai no marcador: `next/image` lanca erro com
            `src` vazio, e um cupcake sem foto cadastrada derrubaria o
            cardapio inteiro. */}
        {semImagem || !cupcake.imagem_url ? (
          <div className="flex h-full items-center justify-center font-display text-grande text-papel/40">
            {cupcake.sabor}
          </div>
        ) : (
          <Image
            src={cupcake.imagem_url}
            alt={cupcake.nome}
            fill
            sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
            onError={() => setSemImagem(true)}
            className="object-cover"
          />
        )}

        {!cupcake.disponivel && (
          <span className="absolute top-3 left-3 rounded-full bg-ameixa px-3 py-1 text-minuscula text-papel">
            Esgotado
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-2 p-5">
        <h3 className="font-display text-media leading-tight">
          {cupcake.nome}
        </h3>
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
              inputMode="numeric"
              min={QTD_MINIMA}
              max={QTD_MAXIMA}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              onBlur={() => setTexto(String(normalizarQuantidade(texto)))}
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
