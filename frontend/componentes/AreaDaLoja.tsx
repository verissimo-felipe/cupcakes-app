"use client";

import { useEffect, type ReactNode } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSessao } from "./SessaoProvider";

/**
 * Porteiro das telas da loja.
 *
 * Tres situacoes, tres respostas:
 *   - sessao ainda carregando -> espera (senao expulsa quem esta logado)
 *   - visitante sem login     -> vai para o login e volta para ca depois
 *   - cliente comum           -> aviso de area restrita
 *
 * O conteudo (`children`) so MONTA para admin. Isso importa: as telas da
 * loja buscam dados assim que montam, e para quem nao e admin essa busca
 * nem chega a acontecer.
 *
 * LEMBRETE DE SEGURANCA: este componente e experiencia do usuario, nao
 * barreira. Quem forcar `admin: true` no DevTools passa daqui - e leva
 * 403 do servidor na primeira requisicao, porque a protecao real esta no
 * router `/admin/pedidos` do back-end.
 */
export function AreaDaLoja({
  voltar,
  children,
}: {
  voltar: string;
  children: ReactNode;
}) {
  const { usuario, carregando } = useSessao();
  const router = useRouter();

  useEffect(() => {
    if (!carregando && !usuario) {
      router.replace(`/login?voltar=${encodeURIComponent(voltar)}`);
    }
  }, [carregando, usuario, router, voltar]);

  if (carregando) {
    return (
      <p className="px-6 py-20 text-center text-tinta-suave">Carregando…</p>
    );
  }

  if (!usuario) return null;

  if (!usuario.admin) {
    return (
      <div className="mx-auto max-w-lg px-6 py-20 text-center">
        <p className="font-display text-grande">
          Área restrita à equipe da loja.
        </p>
        <p className="mt-2 text-tinta-suave">
          Sua conta é de cliente. Seus pedidos ficam em “Meus pedidos”.
        </p>
        <Link
          href="/pedidos"
          className="mt-6 inline-block rounded-lg bg-framboesa px-5 py-2.5 text-papel hover:bg-framboesa-escuro"
        >
          Ver meus pedidos
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}
