"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSessao } from "./SessaoProvider";

export function Cabecalho() {
  const { usuario, carregando, quantidadeCarrinho, sair } = useSessao();
  const router = useRouter();

  async function aoSair() {
    await sair();
    router.push("/");
  }

  return (
    <header>
      <div className="flex items-center justify-between gap-4 bg-ameixa px-6 py-4">
        <Link
          href="/"
          className="font-display text-media text-papel"
          style={{ fontVariationSettings: "'SOFT' 60, 'WONK' 1" }}
        >
          Doce Forma
        </Link>

        <nav className="flex flex-wrap items-center justify-end gap-x-5 gap-y-2 text-minuscula text-papel">
          <Link href="/carrinho" className="hover:text-buttercream">
            Carrinho
            {quantidadeCarrinho > 0 && (
              <span className="ml-1.5 rounded-full bg-framboesa px-2 py-0.5 text-papel">
                {quantidadeCarrinho}
              </span>
            )}
          </Link>

          {/* `carregando` evita o pisca-pisca: sem ele, "Entrar" aparece
              por um instante antes de a sessao ser verificada, e quem ja
              esta logado ve o botao errado. */}
          {carregando ? (
            <span className="text-tinta-suave">···</span>
          ) : usuario ? (
            <>
              {/* Quem esta logado precisa ficar visivel: o endereco de
                  entrega e o historico vem da conta, entao confirmar um
                  pedido na conta errada e um erro caro e silencioso.
                  O e-mail completo vai no `title` para conferencia sem
                  ocupar a barra. */}
              <span
                title={usuario.email}
                className="hidden text-tinta-suave sm:inline"
              >
                {usuario.nome.split(" ")[0]}
                {usuario.admin && (
                  <span className="ml-1.5 rounded-full bg-buttercream px-2 py-0.5 text-ameixa">
                    loja
                  </span>
                )}
              </span>
              {/* Link da gestao so para a equipe. Esconder e conforto de
                  interface; quem digitar /loja/pedidos sem ser admin ve o
                  aviso de area restrita, e a API responde 403. */}
              {usuario.admin && (
                <Link href="/loja/pedidos" className="text-buttercream hover:underline">
                  Gestão
                </Link>
              )}
              <Link href="/pedidos" className="hover:text-buttercream">
                Meus pedidos
              </Link>
              <button onClick={aoSair} className="hover:text-buttercream">
                Sair
              </button>
            </>
          ) : (
            <Link href="/login" className="hover:text-buttercream">
              Entrar
            </Link>
          )}
        </nav>
      </div>
      <div className="pregas" aria-hidden="true" />
    </header>
  );
}
