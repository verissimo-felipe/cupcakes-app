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

        <nav className="flex items-center gap-5 text-minuscula text-papel">
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
