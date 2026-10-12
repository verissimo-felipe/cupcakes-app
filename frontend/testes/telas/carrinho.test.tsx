/**
 * Tela do carrinho. Historias ID 05 e ID 06.
 */
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PaginaCarrinho from "@/app/carrinho/page";
import type { Carrinho } from "@/lib/tipos";
import { CLIENTE } from "../fabricas";

const nav = vi.hoisted(() => ({
  roteador: { push: vi.fn(), replace: vi.fn() },
}));
const sessao = vi.hoisted(() => ({
  usuario: null as unknown,
  carregando: false,
  definirQuantidadeCarrinho: vi.fn(),
}));
const api = vi.hoisted(() => ({
  ver: vi.fn(),
  alterarQuantidade: vi.fn(),
  remover: vi.fn(),
}));

vi.mock("next/navigation", () => ({ useRouter: () => nav.roteador }));
vi.mock("@/componentes/SessaoProvider", () => ({ useSessao: () => sessao }));
vi.mock("@/lib/api", async (original) => ({
  ...(await original<typeof import("@/lib/api")>()),
  carrinho: api,
}));

// Total PROPOSITALMENTE diferente da soma dos subtotais (17,00): se a
// tela somasse por conta propria, mostraria 17,00. O servidor e a unica
// fonte do valor - e assim que uma taxa ou desconto futuro aparece na
// tela sem mexer no front.
const DO_SERVIDOR: Carrinho = {
  itens: [
    {
      cupcake_id: "c-baunilha",
      nome: "Baunilha Clássico",
      preco_unitario: "8.50",
      quantidade: 2,
      subtotal: "17.00",
    },
  ],
  total: "18.00",
  quantidade_itens: 2,
};

beforeEach(() => {
  sessao.usuario = CLIENTE;
  sessao.carregando = false;
});

describe("Carrinho", () => {
  it("rota protegida: sem sessao, manda para o login e volta depois", () => {
    sessao.usuario = null;
    render(<PaginaCarrinho />);

    expect(nav.roteador.replace).toHaveBeenCalledWith(
      "/login?voltar=/carrinho",
    );
    expect(api.ver).not.toHaveBeenCalled();
  });

  it("nao redireciona enquanto a sessao ainda esta sendo verificada", () => {
    sessao.usuario = null;
    sessao.carregando = true;
    render(<PaginaCarrinho />);

    // Redirecionar aqui expulsaria do carrinho quem JA esta logado,
    // antes de o GET /auth/eu responder.
    expect(nav.roteador.replace).not.toHaveBeenCalled();
  });

  it("mostra o total calculado pelo SERVIDOR, sem recalcular", async () => {
    api.ver.mockResolvedValueOnce(DO_SERVIDOR);
    render(<PaginaCarrinho />);

    expect(await screen.findByText(/R\$\s18,00/)).toBeInTheDocument();
    expect(screen.getByText(/R\$\s17,00/)).toBeInTheDocument(); // subtotal da linha
    expect(sessao.definirQuantidadeCarrinho).toHaveBeenCalledWith(2);
  });

  it("aumentar a quantidade substitui o carrinho pela resposta da API", async () => {
    api.ver.mockResolvedValueOnce(DO_SERVIDOR);
    api.alterarQuantidade.mockResolvedValueOnce({
      ...DO_SERVIDOR,
      itens: [{ ...DO_SERVIDOR.itens[0], quantidade: 3, subtotal: "25.50" }],
      total: "25.50",
      quantidade_itens: 3,
    });
    render(<PaginaCarrinho />);

    await userEvent.click(
      await screen.findByRole("button", { name: /aumentar baunilha/i }),
    );

    expect(api.alterarQuantidade).toHaveBeenCalledWith("c-baunilha", 3);
    const linha = screen.getByRole("listitem");
    expect(await within(linha).findByText("3")).toBeInTheDocument();
    expect(screen.getAllByText(/R\$\s25,50/)).toHaveLength(2); // subtotal + total
  });

  it("carrinho vazio convida a voltar ao cardapio", async () => {
    api.ver.mockResolvedValueOnce({
      itens: [],
      total: "0.00",
      quantidade_itens: 0,
    });
    render(<PaginaCarrinho />);

    expect(
      await screen.findByRole("link", { name: /ver o cardápio/i }),
    ).toHaveAttribute("href", "/");
  });
});
