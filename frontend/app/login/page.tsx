"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Alerta } from "@/componentes/Alerta";
import { useSessao } from "@/componentes/SessaoProvider";
import { ErroApi } from "@/lib/api";
import { caminhoSeguro } from "@/lib/navegacao";

/** Historia ID 02 / RF-03. */
function Formulario() {
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const { entrar } = useSessao();
  const router = useRouter();
  const params = useSearchParams();
  // Nunca redirecionar para fora do site - ver lib/navegacao.ts.
  const voltar = caminhoSeguro(params.get("voltar"));

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await entrar(email, senha);
      router.push(voltar);
    } catch (err) {
      // A API devolve a MESMA mensagem para e-mail inexistente e senha
      // errada (RN-10). Nao tente ser prestativo aqui: distinguir os dois
      // permitiria descobrir quais e-mails tem conta no sistema.
      setErro(err instanceof ErroApi ? err.message : "Nao foi possivel entrar.");
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={enviar} className="flex flex-col gap-4">
      {erro && <Alerta>{erro}</Alerta>}

      <label className="flex flex-col gap-1.5">
        <span className="text-minuscula text-tinta-suave">E-mail</span>
        <input
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded-lg border border-tinta-suave/30 bg-papel px-4 py-2.5"
        />
      </label>

      <label className="flex flex-col gap-1.5">
        <span className="text-minuscula text-tinta-suave">Senha</span>
        <input
          type="password"
          required
          autoComplete="current-password"
          value={senha}
          onChange={(e) => setSenha(e.target.value)}
          className="rounded-lg border border-tinta-suave/30 bg-papel px-4 py-2.5"
        />
      </label>

      <button
        type="submit"
        disabled={enviando}
        className="mt-2 rounded-lg bg-framboesa px-4 py-3 text-papel transition-colors hover:bg-framboesa-escuro disabled:opacity-50"
      >
        {enviando ? "Entrando…" : "Entrar"}
      </button>

      <p className="text-center text-minuscula text-tinta-suave">
        Ainda não tem conta?{" "}
        <Link href="/registrar" className="text-framboesa underline">
          Criar conta
        </Link>
      </p>
    </form>
  );
}

export default function Login() {
  return (
    <div className="mx-auto max-w-sm px-6 py-20">
      <h1 className="mb-8 font-display text-titulo">Entrar</h1>
      {/* useSearchParams exige Suspense no App Router: o componente e
          suspenso ate os parametros serem conhecidos, e sem a fronteira
          o build falha com erro de prerender. */}
      <Suspense fallback={<p className="text-tinta-suave">Carregando…</p>}>
        <Formulario />
      </Suspense>
    </div>
  );
}
