"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Alerta } from "@/componentes/Alerta";
import { useSessao } from "@/componentes/SessaoProvider";
import { carrinho as apiCarrinho, pedidos, ErroApi } from "@/lib/api";
import { formatarPreco } from "@/lib/formato";
import type { Carrinho } from "@/lib/tipos";

const FORMAS_PAGAMENTO = [
  { id: "pix", rotulo: "PIX" },
  { id: "credito", rotulo: "Cartão de crédito" },
  { id: "dinheiro", rotulo: "Dinheiro na entrega" },
];

/**
 * Checkout. Historia ID 07 / RF-12, RF-13.
 *
 * CASO DE USO REAL
 * ----------------
 * E o balcao da loja. A pessoa ja escolheu, agora diz para onde vai e
 * como paga. Tudo que ela ve aqui e confirmacao, nao escolha nova - por
 * isso o resumo e somente leitura: mudar quantidade no ultimo passo
 * reabre a decisao que ela acabou de fechar.
 *
 * SEGURANCA: O PEDIDO E MONTADO NO SERVIDOR
 * -----------------------------------------
 * Esta tela envia APENAS o endereco. Os itens e o total o servidor pega
 * do carrinho que ele mesmo guarda.
 *
 * Se a API aceitasse a lista de itens vinda daqui, bastaria abrir o
 * DevTools e enviar `[{cupcake: "Pistache", preco: "0.01"}]` para comprar
 * a loja inteira por um centavo. Nenhuma validacao no front impediria
 * isso, porque o atacante nao usa o front - usa `curl`.
 *
 * Regra: o cliente diz O QUE quer; o servidor decide QUANTO custa.
 */
export default function PaginaCheckout() {
  const [carrinho, setCarrinho] = useState<Carrinho | null>(null);
  const [endereco, setEndereco] = useState("");
  const [pagamento, setPagamento] = useState(FORMAS_PAGAMENTO[0].id);
  const [carregando, setCarregando] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const { usuario, carregando: carregandoSessao, definirQuantidadeCarrinho } =
    useSessao();
  const router = useRouter();

  useEffect(() => {
    if (!carregandoSessao && !usuario) {
      router.replace("/login?voltar=/checkout");
    }
  }, [carregandoSessao, usuario, router]);

  useEffect(() => {
    if (!usuario) return;
    apiCarrinho
      .ver()
      .then(setCarrinho)
      .catch((e: unknown) => {
        if (e instanceof ErroApi && e.status !== 401) setErro(e.message);
      })
      .finally(() => setCarregando(false));
  }, [usuario]);

  async function confirmar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      const pedido = await pedidos.finalizar(endereco);
      // O servidor esvaziou o carrinho na mesma transacao do checkout.
      // Zerar o contador aqui evita o cabecalho mostrar itens que nao
      // existem mais ate a proxima navegacao.
      definirQuantidadeCarrinho(0);
      router.replace(`/pedidos/${pedido.id}`);
    } catch (err) {
      setErro(
        err instanceof ErroApi ? err.message : "Não foi possível finalizar.",
      );
      setEnviando(false);
    }
  }

  if (carregandoSessao || carregando) {
    return <p className="px-6 py-20 text-center text-tinta-suave">Carregando…</p>;
  }

  if (!usuario) return null;

  // Carrinho vazio no checkout acontece de verdade: a pessoa deixa a aba
  // aberta, finaliza o pedido em outro dispositivo e volta nesta. O
  // back-end recusaria com RN-04, mas mostrar o formulario para depois
  // negar seria desperdicio do tempo dela.
  if (!carrinho || carrinho.itens.length === 0) {
    return (
      <div className="mx-auto max-w-lg px-6 py-20 text-center">
        <p className="font-display text-grande">Seu carrinho está vazio.</p>
        <p className="mt-2 text-tinta-suave">
          Não há o que finalizar sem itens no carrinho.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block rounded-lg bg-framboesa px-5 py-2.5 text-papel hover:bg-framboesa-escuro"
        >
          Ver o cardápio
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-12">
      <h1 className="mb-8 font-display text-titulo">Finalizar pedido</h1>

      <section className="mb-10 rounded-xl bg-papel-fundo p-6">
        <h2 className="mb-4 font-display text-media">Resumo</h2>
        <ul className="flex flex-col gap-2">
          {carrinho.itens.map((item) => (
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
          <span className="tabular-nums">{formatarPreco(carrinho.total)}</span>
        </p>
      </section>

      <form onSubmit={confirmar} className="flex flex-col gap-6">
        {erro && <Alerta>{erro}</Alerta>}

        <label className="flex flex-col gap-1.5">
          <span className="text-minuscula text-tinta-suave">
            Endereço de entrega
          </span>
          <input
            required
            minLength={5}
            maxLength={300}
            autoComplete="street-address"
            placeholder="Rua, número, complemento e bairro"
            value={endereco}
            onChange={(ev) => setEndereco(ev.target.value)}
            className="rounded-lg border border-tinta-suave/30 bg-papel px-4 py-2.5"
          />
        </label>

        <fieldset className="flex flex-col gap-2">
          <legend className="mb-1.5 text-minuscula text-tinta-suave">
            Forma de pagamento
          </legend>
          {FORMAS_PAGAMENTO.map((f) => (
            <label key={f.id} className="flex items-center gap-3">
              <input
                type="radio"
                name="pagamento"
                value={f.id}
                checked={pagamento === f.id}
                onChange={() => setPagamento(f.id)}
                className="accent-framboesa"
              />
              {f.rotulo}
            </label>
          ))}
          {/* Honestidade de escopo: a forma de pagamento e registrada na
              interface mas nao e cobrada. PIX real exige contrato com PSP
              (Provedor de Servicos de Pagamento) e CNPJ. Esconder isso do
              usuario seria pior do que admitir. */}
          <p className="mt-1 text-minuscula text-tinta-suave">
            Ambiente de demonstração: nenhuma cobrança é efetuada.
          </p>
        </fieldset>

        <button
          type="submit"
          disabled={enviando}
          className="rounded-lg bg-framboesa px-6 py-3 text-papel hover:bg-framboesa-escuro disabled:opacity-50"
        >
          {enviando ? "Confirmando…" : "Confirmar pedido"}
        </button>

        <Link
          href="/carrinho"
          className="text-center text-minuscula text-tinta-suave underline"
        >
          Voltar ao carrinho
        </Link>
      </form>
    </div>
  );
}
