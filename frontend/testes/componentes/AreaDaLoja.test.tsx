/**
 * Porteiro das telas da loja.
 *
 * Lembrete que vale para todos os testes daqui: isto e EXPERIENCIA do
 * usuario. A barreira de seguranca e o 403 do servidor, coberto em
 * `backend/tests/test_api.py::test_gestao_recusa_cliente_comum_em_todas_as_rotas`.
 */
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AreaDaLoja } from "@/componentes/AreaDaLoja";
import { CLIENTE, LOJA } from "../fabricas";

const nav = vi.hoisted(() => ({
  roteador: { push: vi.fn(), replace: vi.fn() },
}));
const sessao = vi.hoisted(() => ({
  usuario: null as unknown,
  carregando: false,
}));

vi.mock("next/navigation", () => ({ useRouter: () => nav.roteador }));
vi.mock("@/componentes/SessaoProvider", () => ({ useSessao: () => sessao }));

function renderizar() {
  render(
    <AreaDaLoja voltar="/loja/pedidos">
      <p>conteudo da loja</p>
    </AreaDaLoja>,
  );
}

beforeEach(() => {
  sessao.usuario = null;
  sessao.carregando = false;
});

describe("AreaDaLoja", () => {
  it("enquanto verifica a sessao, espera - nao expulsa nem mostra o conteudo", () => {
    sessao.carregando = true;
    renderizar();

    expect(screen.getByText("Carregando…")).toBeInTheDocument();
    expect(nav.roteador.replace).not.toHaveBeenCalled();
    expect(screen.queryByText("conteudo da loja")).not.toBeInTheDocument();
  });

  it("visitante sem login vai para o login e volta para a loja depois", () => {
    renderizar();

    expect(nav.roteador.replace).toHaveBeenCalledWith(
      "/login?voltar=%2Floja%2Fpedidos",
    );
    expect(screen.queryByText("conteudo da loja")).not.toBeInTheDocument();
  });

  it("cliente comum ve aviso de area restrita, e o conteudo nem monta", () => {
    sessao.usuario = CLIENTE;
    renderizar();

    expect(screen.getByText(/área restrita/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /meus pedidos/i })).toHaveAttribute(
      "href",
      "/pedidos",
    );
    // Nao montar significa nao buscar: a tela da loja nem chega a chamar
    // a API para quem nao e admin.
    expect(screen.queryByText("conteudo da loja")).not.toBeInTheDocument();
  });

  it("conta da loja ve o conteudo", () => {
    sessao.usuario = LOJA;
    renderizar();

    expect(screen.getByText("conteudo da loja")).toBeInTheDocument();
  });
});
