"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Alerta } from "@/componentes/Alerta";
import { useSessao } from "@/componentes/SessaoProvider";
import { carrinho as api, ErroApi } from "@/lib/api";
import { formatarPreco } from "@/lib/formato";
import type { Carrinho } from "@/lib/tipos";

/**
 * Carrinho. Historias ID 05 (adicionar) e ID 06 (remover) / RF-08, RF-09.
 *
 * CASO DE USO REAL
 * ----------------
 * O cliente escolhe 2 cupcakes de baunilha, lembra que a sogra nao come
 * chocolate e remove o de chocolate, aumenta a baunilha para 4 porque
 * sao quatro pessoas, e so entao finaliza. Nada disso e uma decisao
 * unica - e um rascunho que a pessoa edita ate ficar satisfeita.
 *
 * O carrinho existe porque comprar nao e um ato, e um processo. Sem ele,
 * a pessoa teria de fechar um pedido por item.
 */
export default function PaginaCarrinho() {
  const [carrinho, setCarrinho] = useState<Carrinho | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState<string | null>(null);

  const {
    usuario,
    carregando: carregandoSessao,
    definirQuantidadeCarrinho,
  } = useSessao();
  const router = useRouter();

  // O redirecionamento espera `carregandoSessao` virar false. Sem isso, a
  // pagina manda para o login no primeiro render - antes de o GET
  // /auth/eu responder - e quem JA esta logado e expulso do proprio
  // carrinho. E o bug mais comum de guarda de rota em client component.
  useEffect(() => {
    if (!carregandoSessao && !usuario) {
      router.replace("/login?voltar=/carrinho");
    }
  }, [carregandoSessao, usuario, router]);

  // A busca vive DENTRO do efeito, e o estado so muda nos callbacks da
  // Promise. Chamar uma funcao que faz `setState` sincrono no corpo do
  // efeito dispara render em cascata - e a regra
  // `react-hooks/set-state-in-effect` do ESLint recusa o padrao.
  useEffect(() => {
    if (!usuario) return;
    api
      .ver()
      .then((c) => {
        setCarrinho(c);
        definirQuantidadeCarrinho(c.quantidade_itens);
      })
      .catch((e: unknown) => {
        if (e instanceof ErroApi && e.status !== 401) setErro(e.message);
      })
      .finally(() => setCarregando(false));
  }, [usuario, definirQuantidadeCarrinho]);

  /**
   * Toda mutacao devolve o carrinho inteiro do servidor, e substituimos o
   * estado por ele.
   *
   * A alternativa seria ajustar o numero localmente e confiar que o
   * servidor fez o mesmo - mais rapido na tela, e errado na primeira
   * divergencia. Se o item esgotou entre a leitura e o clique, o total
   * local mentiria ate a proxima recarga. Uma fonte de verdade so.
   */
  async function mutar(id: string, acao: () => Promise<Carrinho>) {
    setOcupado(id);
    setErro(null);
    try {
      const c = await acao();
      setCarrinho(c);
      definirQuantidadeCarrinho(c.quantidade_itens);
    } catch (e) {
      if (e instanceof ErroApi) setErro(e.message);
    } finally {
      setOcupado(null);
    }
  }

  if (carregandoSessao || carregando) {
    return (
      <p className="px-6 py-20 text-center text-tinta-suave">Carregando…</p>
    );
  }

  if (!usuario) return null;

  const vazio = !carrinho || carrinho.itens.length === 0;

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="mb-8 font-display text-titulo">Seu carrinho</h1>

      {erro && (
        <div className="mb-6">
          <Alerta>{erro}</Alerta>
        </div>
      )}

      {vazio ? (
        /* Tela vazia e convite, nao beco sem saida: diz o que fazer e
           leva ate la com um clique. */
        <div className="rounded-xl bg-papel-fundo px-6 py-16 text-center">
          <p className="font-display text-grande">Nada por aqui ainda.</p>
          <p className="mt-2 text-tinta-suave">
            Escolha os sabores no cardápio e eles aparecem aqui.
          </p>
          <Link
            href="/"
            className="mt-6 inline-block rounded-lg bg-framboesa px-5 py-2.5 text-papel hover:bg-framboesa-escuro"
          >
            Ver o cardápio
          </Link>
        </div>
      ) : (
        <>
          <ul className="flex flex-col divide-y divide-papel-fundo">
            {carrinho.itens.map((item) => {
              const travado = ocupado === item.cupcake_id;
              return (
                <li
                  key={item.cupcake_id}
                  className="flex flex-wrap items-center gap-4 py-5"
                >
                  <div className="min-w-48 flex-1">
                    <p className="font-display text-media">{item.nome}</p>
                    <p className="text-minuscula text-tinta-suave">
                      {formatarPreco(item.preco_unitario)} cada
                    </p>
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      aria-label={`Diminuir ${item.nome}`}
                      disabled={travado || item.quantidade <= 1}
                      onClick={() =>
                        mutar(item.cupcake_id, () =>
                          api.alterarQuantidade(
                            item.cupcake_id,
                            item.quantidade - 1,
                          ),
                        )
                      }
                      className="size-9 rounded-lg border border-tinta-suave/30 disabled:opacity-30"
                    >
                      −
                    </button>
                    <span className="w-10 text-center tabular-nums">
                      {item.quantidade}
                    </span>
                    <button
                      aria-label={`Aumentar ${item.nome}`}
                      disabled={travado || item.quantidade >= 99}
                      onClick={() =>
                        mutar(item.cupcake_id, () =>
                          api.alterarQuantidade(
                            item.cupcake_id,
                            item.quantidade + 1,
                          ),
                        )
                      }
                      className="size-9 rounded-lg border border-tinta-suave/30 disabled:opacity-30"
                    >
                      +
                    </button>
                  </div>

                  {/* Subtotal e "Remover" andam juntos. No celular eles
                      descem para uma linha propria, de ponta a ponta -
                      sem isso o valor ficava solto, recuado no meio. */}
                  <div className="flex items-center gap-4 max-sm:w-full max-sm:justify-between">
                    <p className="font-display text-media tabular-nums sm:w-24 sm:text-right">
                      {formatarPreco(item.subtotal)}
                    </p>

                    {/* Remover tem botao proprio, separado do "−". Chegar a
                        zero diminuindo seria ambiguo: o back-end trata
                        quantidade 0 como entrada invalida (RN-01), nao como
                        remocao. A separacao tambem evita exclusao
                        acidental de quem so queria ajustar. */}
                    <button
                      aria-label={`Remover ${item.nome}`}
                      disabled={travado}
                      onClick={() =>
                        mutar(item.cupcake_id, () =>
                          api.remover(item.cupcake_id),
                        )
                      }
                      className="text-minuscula text-tinta-suave underline hover:text-framboesa disabled:opacity-40"
                    >
                      Remover
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>

          <div className="mt-8 flex flex-wrap items-center justify-between gap-4 border-t border-ameixa pt-6">
            <div>
              <p className="text-minuscula text-tinta-suave">
                {carrinho.quantidade_itens}{" "}
                {carrinho.quantidade_itens === 1 ? "item" : "itens"}
              </p>
              {/* O total vem PRONTO do servidor. O front nunca soma
                  preco: os valores chegam como string decimal exata, e
                  somar em JavaScript introduziria erro de ponto
                  flutuante binario (0.1 + 0.2 = 0.30000000000000004). */}
              <p className="font-display text-titulo tabular-nums">
                {formatarPreco(carrinho.total)}
              </p>
            </div>

            <Link
              href="/checkout"
              className="rounded-lg bg-framboesa px-6 py-3 text-papel hover:bg-framboesa-escuro"
            >
              Finalizar pedido
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
