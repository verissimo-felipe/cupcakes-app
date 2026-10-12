"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { auth, carrinho as apiCarrinho, ErroApi } from "@/lib/api";
import type { Usuario } from "@/lib/tipos";

/**
 * Estado de sessao compartilhado.
 *
 * POR QUE CLIENT COMPONENT
 * ------------------------
 * O JWT vive em cookie httpOnly. Server Components rodam no Node, nao no
 * navegador, e nao recebem esse cookie automaticamente ao chamar a API -
 * seria preciso extrair de `cookies()` e repassar no header a cada
 * requisicao.
 *
 * Em Client Component o navegador anexa o cookie sozinho. Menos codigo e
 * menos chance de esquecer o repasse em alguma rota.
 *
 * Custo aceito: o catalogo nao e renderizado no servidor. Para uma loja
 * com dezenas de produtos e sem exigencia de SEO no enunciado, e troca
 * barata.
 *
 * O contador do carrinho vive aqui junto porque o cabecalho precisa dele
 * em toda tela, e subir o estado evita que cada pagina refaca a chamada.
 */

interface Sessao {
  usuario: Usuario | null;
  carregando: boolean;
  quantidadeCarrinho: number;
  entrar: (email: string, senha: string) => Promise<void>;
  registrar: (nome: string, email: string, senha: string) => Promise<void>;
  sair: () => Promise<void>;
  atualizarCarrinho: () => Promise<void>;
  definirQuantidadeCarrinho: (n: number) => void;
}

const ContextoSessao = createContext<Sessao | null>(null);

export function SessaoProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [quantidadeCarrinho, setQuantidadeCarrinho] = useState(0);

  const atualizarCarrinho = useCallback(async () => {
    try {
      const c = await apiCarrinho.ver();
      setQuantidadeCarrinho(c.quantidade_itens);
    } catch {
      // Carrinho e informacao secundaria: se falhar, o cabecalho apenas
      // nao mostra contador. Nao vale derrubar a pagina por isso.
      setQuantidadeCarrinho(0);
    }
  }, []);

  // Descobre se ha sessao ativa no carregamento. O front NAO consegue ler
  // o cookie httpOnly para saber sozinho - precisa perguntar ao servidor.
  useEffect(() => {
    let ativo = true;

    auth
      .eu()
      .then((u) => {
        if (!ativo) return;
        setUsuario(u);
        return atualizarCarrinho();
      })
      .catch((e: unknown) => {
        // 401 aqui e o caso NORMAL de visitante sem login, nao um erro.
        if (!(e instanceof ErroApi) || e.status !== 401) {
          console.error("Falha ao verificar sessao:", e);
        }
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });

    return () => {
      ativo = false;
    };
  }, [atualizarCarrinho]);

  const entrar = useCallback(
    async (email: string, senha: string) => {
      setUsuario(await auth.entrar(email, senha));
      await atualizarCarrinho();
    },
    [atualizarCarrinho],
  );

  const registrar = useCallback(
    async (nome: string, email: string, senha: string) => {
      setUsuario(await auth.registrar(nome, email, senha));
      await atualizarCarrinho();
    },
    [atualizarCarrinho],
  );

  const sair = useCallback(async () => {
    await auth.sair();
    setUsuario(null);
    setQuantidadeCarrinho(0);
  }, []);

  return (
    <ContextoSessao.Provider
      value={{
        usuario,
        carregando,
        quantidadeCarrinho,
        entrar,
        registrar,
        sair,
        atualizarCarrinho,
        definirQuantidadeCarrinho: setQuantidadeCarrinho,
      }}
    >
      {children}
    </ContextoSessao.Provider>
  );
}

export function useSessao(): Sessao {
  const ctx = useContext(ContextoSessao);
  if (!ctx) {
    throw new Error("useSessao precisa estar dentro de <SessaoProvider>");
  }
  return ctx;
}
