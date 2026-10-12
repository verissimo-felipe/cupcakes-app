"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Alerta } from "@/componentes/Alerta";
import { AreaDaLoja } from "@/componentes/AreaDaLoja";
import { IdPedido } from "@/componentes/IdPedido";
import { SeloStatus } from "@/componentes/SeloStatus";
import { ErroApi, loja } from "@/lib/api";
import {
  formatarDataHora,
  formatarPreco,
  rotuloAvancar,
  rotuloStatus,
} from "@/lib/formato";
import type { PedidoGestaoResumo, StatusPedido } from "@/lib/tipos";

const FILTROS: (StatusPedido | "todos")[] = [
  "todos",
  "recebido",
  "em_preparo",
  "saiu_para_entrega",
  "entregue",
  "cancelado",
];

function mensagemDe(e: unknown): string {
  return e instanceof ErroApi ? e.message : "Algo deu errado. Tente novamente.";
}

/**
 * Gestao de pedidos da loja. Extensao da historia ID 08 / RF-15.
 *
 * CASO DE USO REAL
 * ----------------
 * E a tela que fica aberta no tablet da cozinha. Chega pedido, alguem
 * olha a fila de "Recebido", tira os cupcakes do forno e aperta
 * "Avancar" - o cliente ve "Em preparo" no celular dele na hora em que
 * abrir o app. Sem esta tela, a loja dependeria do cliente para saber
 * que existe pedido.
 */
export default function PaginaPedidosDaLoja() {
  return (
    <AreaDaLoja voltar="/loja/pedidos">
      <PainelPedidos />
    </AreaDaLoja>
  );
}

function PainelPedidos() {
  const [lista, setLista] = useState<PedidoGestaoResumo[] | null>(null);
  const [filtro, setFiltro] = useState<StatusPedido | "todos">("todos");
  const [erro, setErro] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState<string | null>(null);
  const [atualizando, setAtualizando] = useState(false);

  // So monta para admin (ver AreaDaLoja), entao pode buscar direto.
  // O `setState` acontece no callback da Promise, nao no corpo do efeito.
  useEffect(() => {
    let ativo = true;
    loja
      .listar()
      .then((dados) => ativo && setLista(dados))
      .catch((e: unknown) => ativo && setErro(mensagemDe(e)));
    return () => {
      ativo = false;
    };
  }, []);

  /**
   * Busca a lista INTEIRA e filtra aqui, em vez de usar `?status=` do
   * servidor. Motivo: os botoes de filtro mostram a contagem de cada
   * etapa ("Recebido 3"), e isso exige conhecer todos os pedidos.
   *
   * Vale enquanto a lista cabe numa resposta. Com milhares de pedidos, o
   * caminho e paginar no servidor, usar o filtro `?status=` que a API ja
   * tem, e pedir as contagens numa rota propria com `GROUP BY status`.
   */
  const contagem = useMemo(() => {
    const c = new Map<string, number>();
    for (const p of lista ?? []) c.set(p.status, (c.get(p.status) ?? 0) + 1);
    c.set("todos", lista?.length ?? 0);
    return c;
  }, [lista]);

  const visiveis = useMemo(
    () =>
      (lista ?? []).filter((p) => filtro === "todos" || p.status === filtro),
    [lista, filtro],
  );

  async function atualizar() {
    setAtualizando(true);
    setErro(null);
    try {
      setLista(await loja.listar());
    } catch (e) {
      setErro(mensagemDe(e));
    } finally {
      setAtualizando(false);
    }
  }

  /**
   * Avanca uma etapa direto da lista - o "acelerar" da cozinha.
   *
   * A resposta do servidor SUBSTITUI a linha. Nao calculamos o novo
   * status aqui: se outra pessoa da loja tiver cancelado o pedido um
   * segundo antes, o servidor devolve 409 e a tela mostra o motivo, em
   * vez de exibir um avanco que nao aconteceu.
   */
  async function avancar(id: string) {
    setOcupado(id);
    setErro(null);
    try {
      const atualizado = await loja.avancar(id);
      setLista((atual) =>
        (atual ?? []).map((p) => (p.id === id ? atualizado : p)),
      );
    } catch (e) {
      setErro(mensagemDe(e));
    } finally {
      setOcupado(null);
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-minuscula uppercase tracking-widest text-tinta-suave">
            Área da loja
          </p>
          <h1 className="font-display text-titulo">Pedidos</h1>
        </div>
        <button
          type="button"
          onClick={atualizar}
          disabled={atualizando}
          className="rounded-lg border border-ameixa/30 px-4 py-2 text-minuscula hover:border-ameixa disabled:opacity-50"
        >
          {atualizando ? "Atualizando…" : "Atualizar lista"}
        </button>
      </div>

      {/* Filtros como grupo de botoes com `aria-pressed`: o leitor de tela
          anuncia "Recebido, 3, botao, pressionado" - o estado nao fica
          so na cor do botao. */}
      <div
        role="group"
        aria-label="Filtrar por etapa"
        className="mb-6 flex flex-wrap gap-2"
      >
        {FILTROS.map((f) => {
          const ativo = filtro === f;
          return (
            <button
              key={f}
              type="button"
              aria-pressed={ativo}
              onClick={() => setFiltro(f)}
              className={`rounded-full px-3.5 py-1.5 text-minuscula transition-colors ${
                ativo
                  ? "bg-ameixa text-papel"
                  : "bg-papel-fundo text-tinta hover:bg-ameixa/10"
              }`}
            >
              {f === "todos" ? "Todos" : rotuloStatus(f)}
              <span
                className={`ml-1.5 tabular-nums ${ativo ? "text-buttercream" : "text-tinta-suave"}`}
              >
                {contagem.get(f) ?? 0}
              </span>
            </button>
          );
        })}
      </div>

      {erro && (
        <div className="mb-6">
          <Alerta>{erro}</Alerta>
        </div>
      )}

      {lista === null && !erro ? (
        <p className="py-16 text-center text-tinta-suave">
          Carregando pedidos…
        </p>
      ) : visiveis.length === 0 ? (
        <div className="rounded-xl bg-papel-fundo px-6 py-16 text-center">
          <p className="font-display text-grande">
            {filtro === "todos"
              ? "Nenhum pedido por enquanto."
              : `Nenhum pedido em “${rotuloStatus(filtro)}”.`}
          </p>
        </div>
      ) : (
        <>
          {/* CELULAR: cartoes empilhados. Numa tabela de 5 colunas em tela
            de 390px, o botao de avancar ficaria fora da tela, atras de
            uma rolagem lateral - justo o botao mais usado na cozinha. */}
          <ul className="flex flex-col gap-3 md:hidden">
            {visiveis.map((p) => (
              <li key={p.id} className="rounded-xl bg-papel-fundo p-4">
                <div className="flex items-start justify-between gap-3">
                  <IdPedido id={p.id} />
                  <SeloStatus status={p.status} />
                </div>
                <p className="mt-1 text-minuscula text-tinta-suave">
                  {formatarDataHora(p.criado_em)}
                </p>
                <div className="mt-3 flex items-end justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate">{p.cliente.nome}</p>
                    <p className="truncate text-minuscula text-tinta-suave">
                      {p.cliente.email}
                    </p>
                  </div>
                  <p className="shrink-0 text-right font-display tabular-nums">
                    {formatarPreco(p.total)}
                    <span className="block font-sans text-minuscula text-tinta-suave">
                      {p.quantidade_itens}{" "}
                      {p.quantidade_itens === 1 ? "item" : "itens"}
                    </span>
                  </p>
                </div>
                <div className="mt-4">
                  <AcoesLinha
                    pedido={p}
                    ocupado={ocupado === p.id}
                    aoAvancar={() => avancar(p.id)}
                  />
                </div>
              </li>
            ))}
          </ul>

          {/* TELA LARGA: tabela de verdade, nao divs alinhadas - o leitor de
            tela associa cada celula ao cabecalho ("Cliente: Ana").

            `relative` no contêiner NAO e enfeite: sem ele, elementos
            `position: absolute` la dentro (o texto `sr-only` do botao de
            copiar) escapam do `overflow-x-auto` e alargam a pagina
            inteira - o bloco que os contem passaria a ser o <html>. */}
          <div className="relative hidden overflow-x-auto rounded-xl border border-papel-fundo md:block">
            <table className="w-full min-w-[46rem] text-left text-minuscula">
              <caption className="sr-only">
                Pedidos da loja, do mais recente para o mais antigo
              </caption>
              <thead className="bg-papel-fundo text-tinta-suave">
                <tr>
                  <th scope="col" className="px-4 py-3 font-normal">
                    Pedido
                  </th>
                  <th scope="col" className="px-4 py-3 font-normal">
                    Cliente
                  </th>
                  <th scope="col" className="px-4 py-3 text-right font-normal">
                    Total
                  </th>
                  <th scope="col" className="px-4 py-3 font-normal">
                    Etapa
                  </th>
                  <th scope="col" className="px-4 py-3 font-normal">
                    <span className="sr-only">Ações</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {visiveis.map((p) => (
                  <tr
                    key={p.id}
                    className="border-t border-papel-fundo align-top"
                  >
                    <td className="px-4 py-4">
                      <IdPedido id={p.id} />
                      <p className="mt-1 text-tinta-suave">
                        {formatarDataHora(p.criado_em)}
                      </p>
                    </td>
                    <td className="px-4 py-4">
                      <p>{p.cliente.nome}</p>
                      <p className="text-tinta-suave">{p.cliente.email}</p>
                    </td>
                    <td className="px-4 py-4 text-right">
                      <p className="font-display text-base tabular-nums">
                        {formatarPreco(p.total)}
                      </p>
                      <p className="text-tinta-suave">
                        {p.quantidade_itens}{" "}
                        {p.quantidade_itens === 1 ? "item" : "itens"}
                      </p>
                    </td>
                    <td className="px-4 py-4">
                      <SeloStatus status={p.status} />
                    </td>
                    <td className="px-4 py-4">
                      <AcoesLinha
                        pedido={p}
                        ocupado={ocupado === p.id}
                        aoAvancar={() => avancar(p.id)}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

/** Botao de avancar + link de gerenciar. Usado no cartao e na tabela. */
function AcoesLinha({
  pedido,
  ocupado,
  aoAvancar,
}: {
  pedido: PedidoGestaoResumo;
  ocupado: boolean;
  aoAvancar: () => void;
}) {
  const proximo = pedido.acoes.proximo_status;
  return (
    <div className="flex flex-wrap justify-end gap-2">
      {proximo && (
        <button
          type="button"
          disabled={ocupado}
          onClick={aoAvancar}
          className="whitespace-nowrap rounded-lg bg-ameixa px-3 py-1.5 text-minuscula text-papel hover:bg-ameixa-claro disabled:opacity-50"
        >
          {ocupado ? "Salvando…" : rotuloAvancar(proximo)}
        </button>
      )}
      <Link
        href={`/loja/pedidos/${pedido.id}`}
        className="whitespace-nowrap rounded-lg border border-tinta-suave/30 px-3 py-1.5 text-minuscula hover:border-ameixa"
      >
        Gerenciar
      </Link>
    </div>
  );
}
