"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Alerta } from "@/componentes/Alerta";
import { useSessao } from "@/componentes/SessaoProvider";
import { pedidos as api, ErroApi } from "@/lib/api";
import { formatarPreco, rotuloStatus } from "@/lib/formato";
import type { PedidoResumo } from "@/lib/tipos";

/**
 * Meus pedidos. Historia ID 08.
 *
 * CASO DE USO REAL
 * ----------------
 * "Pedi ontem, chegou?" e "quanto gastei no mes passado?" sao as duas
 * perguntas que trazem a pessoa de volta a esta tela. Sem ela, as duas
 * viram ligacao para a loja - e atendimento humano custa caro por
 * consulta que um `SELECT` resolve.
 *
 * POR QUE A LISTA NAO TRAZ OS ITENS
 * ---------------------------------
 * A API devolve um RESUMO: numero, total, status e contagem. Os itens so
 * vem na tela de detalhe.
 *
 * Nao e economia de bytes por avareza: com 50 pedidos de 8 itens, trazer
 * tudo significa 400 linhas que ninguem le - e o ORM faria a consulta
 * delas no banco. A pessoa que abre esta tela quer achar UM pedido, nao
 * reler todos.
 */
export default function PaginaPedidos() {
  const [lista, setLista] = useState<PedidoResumo[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const { usuario, carregando: carregandoSessao } = useSessao();
  const router = useRouter();

  useEffect(() => {
    if (!carregandoSessao && !usuario) {
      router.replace("/login?voltar=/pedidos");
    }
  }, [carregandoSessao, usuario, router]);

  useEffect(() => {
    if (!usuario) return;
    api
      .listar()
      .then(setLista)
      .catch((e: unknown) => {
        if (e instanceof ErroApi && e.status !== 401) setErro(e.message);
      })
      .finally(() => setCarregando(false));
  }, [usuario]);

  if (carregandoSessao || carregando) {
    return <p className="px-6 py-20 text-center text-tinta-suave">Carregando…</p>;
  }

  if (!usuario) return null;

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="mb-8 font-display text-titulo">Meus pedidos</h1>

      {erro && (
        <div className="mb-6">
          <Alerta>{erro}</Alerta>
        </div>
      )}

      {lista.length === 0 ? (
        <div className="rounded-xl bg-papel-fundo px-6 py-16 text-center">
          <p className="font-display text-grande">Você ainda não pediu nada.</p>
          <Link
            href="/"
            className="mt-6 inline-block rounded-lg bg-framboesa px-5 py-2.5 text-papel hover:bg-framboesa-escuro"
          >
            Ver o cardápio
          </Link>
        </div>
      ) : (
        <ul className="flex flex-col gap-3">
          {lista.map((p) => (
            <li key={p.id}>
              <Link
                href={`/pedidos/${p.id}`}
                className="flex flex-wrap items-center justify-between gap-4 rounded-xl bg-papel-fundo px-5 py-4 transition-colors hover:bg-papel-fundo/70"
              >
                <div>
                  {/* Os 8 primeiros caracteres do UUID bastam para a
                      pessoa reconhecer e citar o pedido ao telefone.
                      O identificador completo vai na URL. */}
                  <p className="font-display text-media">
                    Pedido #{p.id.slice(0, 8)}
                  </p>
                  <p className="text-minuscula text-tinta-suave">
                    {p.quantidade_itens}{" "}
                    {p.quantidade_itens === 1 ? "item" : "itens"}
                  </p>
                </div>

                <div className="text-right">
                  <p className="font-display text-media tabular-nums">
                    {formatarPreco(p.total)}
                  </p>
                  <p className="text-minuscula text-framboesa">
                    {rotuloStatus(p.status)}
                  </p>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
