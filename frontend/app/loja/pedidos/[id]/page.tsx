"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Alerta } from "@/componentes/Alerta";
import { AreaDaLoja } from "@/componentes/AreaDaLoja";
import { IdPedido } from "@/componentes/IdPedido";
import { LinhaDoTempo } from "@/componentes/LinhaDoTempo";
import { SeloStatus } from "@/componentes/SeloStatus";
import { ErroApi, loja } from "@/lib/api";
import {
  formatarDataHora,
  formatarPreco,
  rotuloAvancar,
  rotuloStatus,
} from "@/lib/formato";
import type { PedidoGestao } from "@/lib/tipos";

function mensagemDe(e: unknown): string {
  return e instanceof ErroApi ? e.message : "Algo deu errado. Tente novamente.";
}

/**
 * Gestao de UM pedido. Extensao da historia ID 08 / RF-15.
 *
 * CASOS DE USO REAIS
 * ------------------
 * Avancar etapa  -> a cozinha terminou; o entregador saiu; chegou.
 * Corrigir endereco -> o cliente liga: "digitei o numero errado, e 132,
 *                   nao 123". Funciona ate o pedido sair da loja.
 * Cancelar       -> acabou o ingrediente, ou o cliente desistiu antes do
 *                   preparo. Fica registrado como cancelado.
 * Excluir        -> limpar da lista um pedido de teste ou duplicado,
 *                   DEPOIS de cancelado. A venda continua no banco.
 *
 * Que botao aparece e decidido pelo servidor (`pedido.acoes`), nao por
 * uma copia da FSM aqui. A tela so desenha o que o dominio permite.
 */
export default function PaginaGestaoPedido() {
  const { id } = useParams<{ id: string }>();
  return (
    <AreaDaLoja voltar={`/loja/pedidos/${id}`}>
      <GestaoPedido id={id} />
    </AreaDaLoja>
  );
}

type Confirmacao = "cancelar" | "excluir" | null;

function GestaoPedido({ id }: { id: string }) {
  const router = useRouter();
  const [pedido, setPedido] = useState<PedidoGestao | null>(null);
  const [erroCarga, setErroCarga] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const [editando, setEditando] = useState(false);
  const [endereco, setEndereco] = useState("");
  const [confirmando, setConfirmando] = useState<Confirmacao>(null);

  useEffect(() => {
    let ativo = true;
    loja
      .detalhar(id)
      .then((p) => ativo && setPedido(p))
      .catch((e: unknown) => ativo && setErroCarga(mensagemDe(e)));
    return () => {
      ativo = false;
    };
  }, [id]);

  /**
   * Executa uma acao e substitui o pedido pelo que o servidor devolveu.
   *
   * Nenhuma acao altera o estado local "na fe". Se o servidor recusar -
   * 409 porque o pedido ja saiu para entrega, por exemplo - a tela
   * continua mostrando a verdade e exibe o motivo vindo da API.
   */
  async function executar(acao: () => Promise<PedidoGestao>, sucesso: string) {
    setOcupado(true);
    setErro(null);
    setAviso(null);
    try {
      setPedido(await acao());
      setAviso(sucesso);
      setEditando(false);
      setConfirmando(null);
    } catch (e) {
      setErro(mensagemDe(e));
    } finally {
      setOcupado(false);
    }
  }

  async function excluir() {
    setOcupado(true);
    setErro(null);
    try {
      await loja.excluir(id);
      // `replace`, nao `push`: o botao "voltar" do navegador nao deve
      // reabrir um pedido que deixou de existir para a aplicacao.
      router.replace("/loja/pedidos");
    } catch (e) {
      setErro(mensagemDe(e));
      setConfirmando(null);
      setOcupado(false);
    }
  }

  if (erroCarga) {
    return (
      <div className="mx-auto max-w-lg px-6 py-20 text-center">
        <p className="font-display text-grande">Pedido não encontrado.</p>
        <p className="mt-2 text-tinta-suave">{erroCarga}</p>
        <Link
          href="/loja/pedidos"
          className="mt-6 inline-block rounded-lg bg-framboesa px-5 py-2.5 text-papel hover:bg-framboesa-escuro"
        >
          Voltar aos pedidos
        </Link>
      </div>
    );
  }

  if (!pedido) {
    return (
      <p className="px-6 py-20 text-center text-tinta-suave">Carregando…</p>
    );
  }

  const { acoes } = pedido;
  const proximo = acoes.proximo_status;

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <Link
        href="/loja/pedidos"
        className="text-minuscula text-tinta-suave underline"
      >
        Pedidos da loja
      </Link>

      <div className="mt-3 mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-titulo">Pedido</h1>
          <IdPedido id={pedido.id} grande />
          <p className="mt-1 text-minuscula text-tinta-suave">
            Feito em {formatarDataHora(pedido.criado_em)}
          </p>
        </div>
        <SeloStatus status={pedido.status} />
      </div>

      {/* Avisos com `role` proprio (dentro de Alerta): mudanca de etapa e
          anunciada ao leitor de tela sem a pessoa procurar. */}
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

      {/* --- Acoes principais ------------------------------------------ */}
      {(proximo || acoes.pode_cancelar || acoes.pode_excluir) && (
        <section
          aria-labelledby="titulo-acoes"
          className="mb-10 rounded-xl border border-ameixa/20 p-6"
        >
          <h2 id="titulo-acoes" className="font-display text-media">
            O que fazer agora
          </h2>

          <div className="mt-4 flex flex-wrap gap-2">
            {proximo && (
              <button
                type="button"
                disabled={ocupado}
                onClick={() =>
                  executar(
                    () => loja.avancar(pedido.id),
                    `Pedido avançou para “${rotuloStatus(proximo)}”.`,
                  )
                }
                className="rounded-lg bg-ameixa px-4 py-2 text-papel hover:bg-ameixa-claro disabled:opacity-50"
              >
                {rotuloAvancar(proximo)}
              </button>
            )}

            {acoes.pode_cancelar && confirmando !== "cancelar" && (
              <button
                type="button"
                disabled={ocupado}
                onClick={() => setConfirmando("cancelar")}
                className="rounded-lg border border-tinta-suave/30 px-4 py-2 text-tinta-suave hover:border-framboesa hover:text-framboesa disabled:opacity-50"
              >
                Cancelar pedido
              </button>
            )}

            {acoes.pode_excluir && confirmando !== "excluir" && (
              <button
                type="button"
                disabled={ocupado}
                onClick={() => setConfirmando("excluir")}
                className="rounded-lg border border-framboesa/40 px-4 py-2 text-framboesa hover:bg-framboesa/10 disabled:opacity-50"
              >
                Excluir pedido
              </button>
            )}
          </div>

          {/* Confirmacao em linha, nao `window.confirm`: o dialogo nativo
              nao segue o visual, nao explica a consequencia e, em alguns
              navegadores, pode ser silenciado pela propria pessoa
              ("impedir esta pagina de criar dialogos"). */}
          {confirmando === "cancelar" && (
            <Confirmar
              texto="O cliente verá o pedido como cancelado. Isso não pode ser desfeito."
              acao="Sim, cancelar"
              ocupado={ocupado}
              aoConfirmar={() =>
                executar(() => loja.cancelar(pedido.id), "Pedido cancelado.")
              }
              aoVoltar={() => setConfirmando(null)}
            />
          )}
          {confirmando === "excluir" && (
            <Confirmar
              texto="O pedido sai de todas as listas, da loja e do cliente. O registro da venda continua guardado no banco para auditoria."
              acao="Sim, excluir"
              ocupado={ocupado}
              aoConfirmar={excluir}
              aoVoltar={() => setConfirmando(null)}
            />
          )}

          {!acoes.pode_excluir && (
            <p className="mt-4 text-minuscula text-tinta-suave">
              Para excluir, o pedido precisa estar entregue ou cancelado.
            </p>
          )}
        </section>
      )}

      {/* --- Acompanhamento -------------------------------------------- */}
      <section className="mb-10">
        <h2 className="mb-5 font-display text-media">Acompanhamento</h2>
        <LinhaDoTempo status={pedido.status} />
      </section>

      {/* --- Cliente e entrega ----------------------------------------- */}
      <section className="mb-10 grid gap-6 sm:grid-cols-2">
        <div>
          <h2 className="mb-2 font-display text-media">Cliente</h2>
          <p>{pedido.cliente.nome}</p>
          <p className="text-minuscula text-tinta-suave">
            {pedido.cliente.email}
          </p>
        </div>

        <div>
          <div className="mb-2 flex items-baseline justify-between gap-3">
            <h2 className="font-display text-media">Entrega</h2>
            {acoes.pode_editar_endereco && !editando && (
              <button
                type="button"
                onClick={() => {
                  setEndereco(pedido.endereco_entrega);
                  setEditando(true);
                  setAviso(null);
                }}
                className="text-minuscula text-tinta-suave underline hover:text-ameixa"
              >
                Corrigir endereço
              </button>
            )}
          </div>

          {editando ? (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                executar(
                  () => loja.alterarEndereco(pedido.id, endereco),
                  "Endereço atualizado. O cliente já vê o novo endereço.",
                );
              }}
            >
              <label htmlFor="endereco" className="sr-only">
                Endereço de entrega
              </label>
              <textarea
                id="endereco"
                value={endereco}
                onChange={(e) => setEndereco(e.target.value)}
                rows={3}
                minLength={5}
                maxLength={300}
                required
                className="w-full rounded-lg border border-tinta-suave/30 bg-papel px-3 py-2"
              />
              <div className="mt-2 flex gap-2">
                <button
                  type="submit"
                  disabled={ocupado}
                  className="rounded-lg bg-ameixa px-4 py-1.5 text-minuscula text-papel hover:bg-ameixa-claro disabled:opacity-50"
                >
                  Salvar
                </button>
                <button
                  type="button"
                  onClick={() => setEditando(false)}
                  className="rounded-lg px-4 py-1.5 text-minuscula text-tinta-suave hover:text-ameixa"
                >
                  Desistir
                </button>
              </div>
            </form>
          ) : (
            <>
              <p className="whitespace-pre-line text-tinta-suave">
                {pedido.endereco_entrega}
              </p>
              {!acoes.pode_editar_endereco && (
                <p className="mt-1 text-minuscula text-tinta-suave">
                  Endereço travado: o pedido já saiu da loja.
                </p>
              )}
            </>
          )}
        </div>
      </section>

      {/* --- Itens ----------------------------------------------------- */}
      <section className="rounded-xl bg-papel-fundo p-6">
        <h2 className="mb-4 font-display text-media">Itens</h2>
        <ul className="flex flex-col gap-2">
          {pedido.itens.map((item) => (
            <li
              key={item.cupcake_id}
              className="flex justify-between gap-4 text-minuscula"
            >
              <span>
                {item.quantidade}× {item.nome}
                <span className="ml-2 text-tinta-suave">
                  ({formatarPreco(item.preco_unitario)} cada)
                </span>
              </span>
              <span className="tabular-nums">
                {formatarPreco(item.subtotal)}
              </span>
            </li>
          ))}
        </ul>
        <p className="mt-4 flex justify-between border-t border-tinta-suave/20 pt-4 font-display text-media">
          <span>Total</span>
          <span className="tabular-nums">{formatarPreco(pedido.total)}</span>
        </p>
        <p className="mt-2 text-minuscula text-tinta-suave">
          Itens e valores não são editáveis: são o que o cliente pagou.
        </p>
      </section>
    </div>
  );
}

function Confirmar({
  texto,
  acao,
  ocupado,
  aoConfirmar,
  aoVoltar,
}: {
  texto: string;
  acao: string;
  ocupado: boolean;
  aoConfirmar: () => void;
  aoVoltar: () => void;
}) {
  return (
    // `aria-live` faz o leitor de tela ler a consequencia assim que a
    // caixa aparece - quem nao ve a tela tambem sabe o que vai acontecer.
    <div
      role="group"
      aria-label="Confirmar ação"
      aria-live="polite"
      className="mt-4 rounded-lg bg-framboesa/5 p-4"
    >
      <p className="text-minuscula">{texto}</p>
      <div className="mt-3 flex gap-2">
        <button
          type="button"
          disabled={ocupado}
          onClick={aoConfirmar}
          className="rounded-lg bg-framboesa px-4 py-1.5 text-minuscula text-papel hover:bg-framboesa-escuro disabled:opacity-50"
        >
          {ocupado ? "Aguarde…" : acao}
        </button>
        <button
          type="button"
          onClick={aoVoltar}
          className="rounded-lg px-4 py-1.5 text-minuscula text-tinta-suave hover:text-ameixa"
        >
          Voltar
        </button>
      </div>
    </div>
  );
}
