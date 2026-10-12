/**
 * Tela de login. Historia ID 02 / RF-03.
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Login from "@/app/login/page";
import { ErroApi } from "@/lib/api";

// Dublês do roteador do Next e da sessao. `vi.hoisted` cria os objetos
// antes de os `vi.mock` serem aplicados (o Vitest sobe os mocks para o
// topo do arquivo).
const nav = vi.hoisted(() => ({
  roteador: { push: vi.fn(), replace: vi.fn() },
  busca: new URLSearchParams(),
}));
const sessao = vi.hoisted(() => ({ entrar: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => nav.roteador,
  useSearchParams: () => nav.busca,
}));
vi.mock("@/componentes/SessaoProvider", () => ({
  useSessao: () => sessao,
}));

async function preencherEEnviar() {
  await userEvent.type(screen.getByLabelText("E-mail"), "ana@mail.com");
  await userEvent.type(screen.getByLabelText("Senha"), "senha-qualquer");
  await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
}

beforeEach(() => {
  nav.busca = new URLSearchParams();
});

describe("Login", () => {
  it("RN-10: credencial errada mostra a mensagem GENERICA do servidor e nao navega", async () => {
    sessao.entrar.mockRejectedValueOnce(
      new ErroApi("credenciais_invalidas", "E-mail ou senha invalidos", 401),
    );
    render(<Login />);

    await preencherEEnviar();

    // A mensagem nao diz QUAL campo errou: dizer permitiria descobrir
    // quais e-mails tem conta no sistema.
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "E-mail ou senha invalidos",
    );
    expect(nav.roteador.push).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Entrar" })).toBeEnabled();
  });

  it("depois de entrar, volta para a pagina interna que pediu o login", async () => {
    nav.busca = new URLSearchParams("voltar=/carrinho");
    sessao.entrar.mockResolvedValueOnce(undefined);
    render(<Login />);

    await preencherEEnviar();

    expect(sessao.entrar).toHaveBeenCalledWith(
      "ana@mail.com",
      "senha-qualquer",
    );
    expect(nav.roteador.push).toHaveBeenCalledWith("/carrinho");
  });

  it("CWE-601: ?voltar= apontando para outro site e ignorado", async () => {
    nav.busca = new URLSearchParams("voltar=https://site-falso.com");
    sessao.entrar.mockResolvedValueOnce(undefined);
    render(<Login />);

    await preencherEEnviar();

    expect(nav.roteador.push).toHaveBeenCalledWith("/");
  });
});
