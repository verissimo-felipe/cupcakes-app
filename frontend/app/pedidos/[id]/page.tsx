"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Alerta } from "@/componentes/Alerta";
import { LinhaDoTempo } from "@/componentes/LinhaDoTempo";
import { useSessao } from "@/componentes/SessaoProvider";
import { pedidos as api, ErroApi } from "@/lib/api";
import { formatarPreco, rotuloStatus } from "@/lib/formato";
import type { Pedido } from "@/lib/tipos";

/**
 * Detalhe e rastreamento. Historia ID 08 / RF-14, RF-15.
 *
 * CASO DE USO REAL
 * ----------------
 * O cliente abre para saber onde o pedido esta - e a tela de "seu pedido
 * saiu para entrega" que todo aplicativo de delivery tem.
 *
 * Quem muda a etapa e a loja, em outra tela (`/loja/pedidos/[id]`). Esse
 * clique e o que faz esta tela mudar - nao existe automacao magica,
 * existe alguem na cozinha apertando um botao.
 *
 * `useParams` em vez de receber `params` por propriedade: no Next.js 16
 * o `params` de Server Component virou Promise e precisa de `await`.
 * Como esta pagina e Client Component (o cookie httpOnly exige), o hook
 * entrega o valor de forma sincrona e o problema nem aparece.
 */
export default function PaginaPedido() {
  const { id } = useParams<{ id: string }>();
  const [pedido, setPedido] = useState<Pedido | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const { usuario, carregando: carregandoSessao } = useSessao();
  const router = useRouter();

  useEffect(() => {
    if (!carregandoSessao && !usuario) {
      router.replace(`/login?voltar=/pedidos/${id}`);
    }
  }, [carregandoSessao, usuario, router, id]);

  useEffect(() => {
    if (!usuario || !id) return;
    api
      .detalhar(id)
      .then(setPedido)
      .catch((e: unknown) => {
        if (e instanceof ErroApi && e.status !== 401) setErro(e.message);
      })
      .finally(() => setCarregando(false));
  }, [usuario, id]);

  if (carregandoSessao || carregando) {
    return <p className="px-6 py-20 text-center text-tinta-suave">Carregando…</p>;
  }

  if (!usuario) return null;

  // 404 aqui cobre DOIS casos de proposito: pedido inexistente e pedido
  // de outro cliente. O back-end nao distingue - responder 403 para o
  // segundo confirmaria que aquele identificador existe, e bastaria
  // varrer identificadores para mapear os pedidos da loja (IDOR).
  if (erro && !pedido) {
    return (
      <div className="mx-auto max-w-lg px-6 py-20 text-center">
        <p className="font-display text-grande">Pedido não encontrado.</p>
        <p className="mt-2 text-tinta-suave">{erro}</p>
        <Link
          href="/pedidos"
          className="mt-6 inline-block rounded-lg bg-framboesa px-5 py-2.5 text-papel hover:bg-framboesa-escuro"
        >
          Ver meus pedidos
        </Link>
      </div>
    );
  }

  if (!pedido) return null;

  return (
    <div className="mx-auto max-w-2xl px-6 py-12">
      <Link
        href="/pedidos"
        className="text-minuscula text-tinta-suave underline"
      >
        Meus pedidos
      </Link>

      <h1 className="mt-3 mb-1 font-display text-titulo">
        Pedido #{pedido.id.slice(0, 8)}
      </h1>
      <p className="mb-10 text-framboesa">{rotuloStatus(pedido.status)}</p>

      {erro && (
        <div className="mb-6">
          <Alerta>{erro}</Alerta>
        </div>
      )}

      <section className="mb-10">
        <h2 className="mb-5 font-display text-media">Acompanhamento</h2>
        <LinhaDoTempo status={pedido.status} />
      </section>

      <section className="mb-10 rounded-xl bg-papel-fundo p-6">
        <h2 className="mb-4 font-display text-media">Itens</h2>
        <ul className="flex flex-col gap-2">
          {pedido.itens.map((item) => (
            <li
              key={item.cupcake_id}
              className="flex justify-between gap-4 text-minuscula"
            >
              <span>
                {item.quantidade}× {item.nome}
              </span>
              <span className="tabular-nums">{formatarPreco(item.subtotal)}</span>
            </li>
          ))}
        </ul>
        <p className="mt-4 flex justify-between border-t border-tinta-suave/20 pt-4 font-display text-media">
          <span>Total</span>
          <span className="tabular-nums">{formatarPreco(pedido.total)}</span>
        </p>
      </section>

      <section className="mb-10">
        <h2 className="mb-2 font-display text-media">Entrega</h2>
        <p className="text-tinta-suave">{pedido.endereco_entrega}</p>
      </section>

      {/* Atalho para a equipe. So aparece no PROPRIO pedido do admin,
          porque esta rota e a do cliente: ela devolve 404 para pedido de
          outra pessoa ate para a loja. A gestao de verdade vive em
          /loja/pedidos, que usa as rotas /admin do servidor. */}
      {usuario.admin && (
        <Link
          href={`/loja/pedidos/${pedido.id}`}
          className="inline-block rounded-lg border border-ameixa/30 px-4 py-2 text-minuscula hover:border-ameixa"
        >
          Gerenciar na área da loja
        </Link>
      )}
    </div>
  );
}
