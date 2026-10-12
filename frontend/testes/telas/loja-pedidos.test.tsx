/**
 * Lista de pedidos da loja (/loja/pedidos). Extensao da historia ID 08 / RF-15.
 *
 * A tela desenha DUAS versoes da lista - cartoes no celular e tabela na
 * tela larga - e o CSS esconde uma delas. O jsdom nao aplica CSS, entao
 * as duas existem aqui; os testes olham dentro da TABELA com `within`.
 */
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PaginaPedidosDaLoja from "@/app/loja/pedidos/page";
import { ErroApi } from "@/lib/api";
import { ACOES_CANCELADO, LOJA, pedidoGestao } from "../fabricas";

const nav = vi.hoisted(() => ({
  roteador: { push: vi.fn(), replace: vi.fn() },
}));
const sessao = vi.hoisted(() => ({
  usuario: null as unknown,
  carregando: false,
}));
const loja = vi.hoisted(() => ({ listar: vi.fn(), avancar: vi.fn() }));

vi.mock("next/navigation", () => ({ useRouter: () => nav.roteador }));
vi.mock("@/componentes/SessaoProvider", () => ({ useSessao: () => sessao }));
vi.mock("@/lib/api", async (original) => ({
  ...(await original<typeof import("@/lib/api")>()),
  loja,
}));

const RECEBIDO = pedidoGestao({ id: "aaaaaaaa-0000-4000-8000-000000000001" });
const CANCELADO = pedidoGestao({
  id: "bbbbbbbb-0000-4000-8000-000000000002",
  status: "cancelado",
  cliente: { nome: "Bruno", email: "bruno@mail.com" },
  acoes: ACOES_CANCELADO,
});

/** Abre a tela e devolve consultas restritas a tabela. */
async function abrir() {
  render(<PaginaPedidosDaLoja />);
  return within(await screen.findByRole("table"));
}

beforeEach(() => {
  sessao.usuario = LOJA;
  loja.listar.mockResolvedValue([RECEBIDO, CANCELADO]);
});

describe("Pedidos da loja", () => {
  it("lista pedidos de TODOS os clientes, com numero curto e dono", async () => {
    const t = await abrir();

    expect(t.getByText("#aaaaaaaa")).toBeInTheDocument();
    expect(t.getByText("Ana Cliente")).toBeInTheDocument();
    expect(t.getByText("bruno@mail.com")).toBeInTheDocument();
  });

  it("botao de avancar so aparece onde o SERVIDOR disse que ha proxima etapa", async () => {
    const t = await abrir();

    // Um botao so: o pedido cancelado veio com `proximo_status: null`.
    expect(t.getAllByRole("button", { name: "Iniciar preparo" })).toHaveLength(
      1,
    );
    expect(t.getAllByRole("link", { name: "Gerenciar" })).toHaveLength(2);
  });

  it("filtro por etapa mostra a contagem e esconde as outras etapas", async () => {
    await abrir();

    const filtros = within(
      screen.getByRole("group", { name: /filtrar por etapa/i }),
    );
    await userEvent.click(
      filtros.getByRole("button", { name: /cancelado\s*1/i }),
    );

    const t = within(screen.getByRole("table"));
    expect(t.queryByText("Ana Cliente")).not.toBeInTheDocument();
    expect(t.getByText("Bruno")).toBeInTheDocument();
    expect(filtros.getByRole("button", { name: /cancelado/i })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("avancar troca a linha pela resposta do servidor", async () => {
    loja.avancar.mockResolvedValueOnce(
      pedidoGestao({
        id: RECEBIDO.id,
        status: "em_preparo",
        acoes: { ...RECEBIDO.acoes, proximo_status: "saiu_para_entrega" },
      }),
    );
    const t = await abrir();

    await userEvent.click(t.getByRole("button", { name: "Iniciar preparo" }));

    expect(loja.avancar).toHaveBeenCalledWith(RECEBIDO.id);
    expect(
      await t.findByRole("button", { name: "Enviar para entrega" }),
    ).toBeInTheDocument();
    expect(t.getByText("Em preparo")).toBeInTheDocument();
  });

  it("recusa do servidor (409) mostra o motivo e mantem a linha como estava", async () => {
    loja.avancar.mockRejectedValueOnce(
      new ErroApi(
        "transicao_invalida",
        "Transicao invalida: cancelado -> proxima etapa",
        409,
      ),
    );
    const t = await abrir();

    await userEvent.click(t.getByRole("button", { name: "Iniciar preparo" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Transicao invalida",
    );
    expect(
      t.getByRole("button", { name: "Iniciar preparo" }),
    ).toBeInTheDocument();
  });
});
