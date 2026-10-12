"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CardCupcake } from "@/componentes/CardCupcake";
import { Alerta } from "@/componentes/Alerta";
import { useSessao } from "@/componentes/SessaoProvider";
import { carrinho as apiCarrinho, catalogo, ErroApi } from "@/lib/api";
import type { Cupcake } from "@/lib/tipos";

/** Catalogo e busca. Historias ID 04 e ID 05. */
export default function Catalogo() {
  const [cupcakes, setCupcakes] = useState<Cupcake[]>([]);
  const [busca, setBusca] = useState("");
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);

  const { usuario, definirQuantidadeCarrinho } = useSessao();
  const router = useRouter();

  const buscar = useCallback(async (termo: string) => {
    setCarregando(true);
    setErro(null);
    try {
      setCupcakes(await catalogo.listar(termo));
    } catch (e) {
      setErro(e instanceof ErroApi ? e.message : "Nao foi possivel carregar o cardapio.");
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    // Debounce: sem ele, cada tecla dispara uma requisicao. RNF-04 pede
    // resposta em ate 1s, e rajada de chamadas trabalha contra isso.
    const t = setTimeout(() => buscar(busca), busca ? 300 : 0);
    return () => clearTimeout(t);
  }, [busca, buscar]);

  async function adicionar(cupcakeId: string, quantidade: number) {
    // Rota protegida: manda para o login antes de tentar e levar 401.
    if (!usuario) {
      router.push("/login?voltar=/");
      return;
    }

    setErro(null);
    setAviso(null);
    try {
      const c = await apiCarrinho.adicionar(cupcakeId, quantidade);
      definirQuantidadeCarrinho(c.quantidade_itens);
      setAviso("Adicionado ao carrinho.");
    } catch (e) {
      // `cupcake_indisponivel` (409) chega aqui quando o produto esgota
      // entre o carregamento da pagina e o clique. Recarregamos a lista
      // para a tela refletir o estoque real.
      if (e instanceof ErroApi) {
        setErro(e.message);
        if (e.codigo === "cupcake_indisponivel") buscar(busca);
      }
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-6">
      <section className="py-16">
        <h1
          className="max-w-2xl font-display text-heroi leading-[1.05]"
          style={{ fontVariationSettings: "'SOFT' 80, 'WONK' 1" }}
        >
          Cupcakes assados no dia, entregues ainda macios.
        </h1>
        <p className="mt-5 max-w-lg leading-relaxed text-tinta-suave">
          Massa feita pela manhã, cobertura montada na hora do pedido.
          Escolha os sabores e acompanhe a entrega em tempo real.
        </p>
      </section>

      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <h2 className="font-display text-titulo">Cardápio</h2>
        <input
          type="search"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder="Buscar por nome ou sabor"
          aria-label="Buscar cupcakes"
          className="w-full max-w-xs rounded-lg border border-tinta-suave/30 bg-papel px-4 py-2"
        />
      </div>

      {erro && (
        <div className="mb-6">
          <Alerta>{erro}</Alerta>
        </div>
      )}
      {aviso && !erro && (
        <div className="mb-6">
          <Alerta tipo="sucesso">{aviso}</Alerta>
        </div>
      )}

      {carregando ? (
        <p className="py-12 text-center text-tinta-suave">Carregando o cardápio…</p>
      ) : cupcakes.length === 0 ? (
        /* Tela vazia e convite para agir, nao beco sem saida. */
        <div className="py-16 text-center">
          <p className="font-display text-grande">Nenhum cupcake com esse nome.</p>
          <button
            onClick={() => setBusca("")}
            className="mt-3 text-framboesa underline"
          >
            Ver o cardápio inteiro
          </button>
        </div>
      ) : (
        <div className="grid gap-6 pb-12 sm:grid-cols-2 lg:grid-cols-3">
          {cupcakes.map((c) => (
            <CardCupcake key={c.id} cupcake={c} aoAdicionar={adicionar} />
          ))}
        </div>
      )}
    </div>
  );
}
