"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Alerta } from "@/componentes/Alerta";
import { useSessao } from "@/componentes/SessaoProvider";
import { ErroApi } from "@/lib/api";

const MINIMO_SENHA = 8;

/** Historia ID 01 / RF-01. */
export default function Registrar() {
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const { registrar } = useSessao();
  const router = useRouter();

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await registrar(nome, email, senha);
      router.push("/");
    } catch (err) {
      setErro(
        err instanceof ErroApi ? err.message : "Nao foi possivel criar a conta.",
      );
      setEnviando(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm px-6 py-20">
      <h1 className="mb-8 font-display text-titulo">Criar conta</h1>

      <form onSubmit={enviar} className="flex flex-col gap-4">
        {erro && <Alerta>{erro}</Alerta>}

        <label className="flex flex-col gap-1.5">
          <span className="text-minuscula text-tinta-suave">Nome</span>
          <input
            required
            minLength={2}
            autoComplete="name"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            className="rounded-lg border border-tinta-suave/30 bg-papel px-4 py-2.5"
          />
        </label>

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
            minLength={MINIMO_SENHA}
            autoComplete="new-password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            className="rounded-lg border border-tinta-suave/30 bg-papel px-4 py-2.5"
          />
          {/* Diz a regra ANTES do erro. Nao exigimos caractere especial:
              conforme NIST SP 800-63B, regras de composicao produzem
              senhas piores porque o usuario responde com padroes obvios. */}
          <span className="text-minuscula text-tinta-suave">
            Pelo menos {MINIMO_SENHA} caracteres. Não precisa de símbolo.
          </span>
        </label>

        <button
          type="submit"
          disabled={enviando}
          className="mt-2 rounded-lg bg-framboesa px-4 py-3 text-papel transition-colors hover:bg-framboesa-escuro disabled:opacity-50"
        >
          {enviando ? "Criando…" : "Criar conta"}
        </button>

        <p className="text-center text-minuscula text-tinta-suave">
          Já tem conta?{" "}
          <Link href="/login" className="text-framboesa underline">
            Entrar
          </Link>
        </p>
      </form>
    </div>
  );
}
