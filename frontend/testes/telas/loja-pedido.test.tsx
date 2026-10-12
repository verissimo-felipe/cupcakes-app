/**
 * Gestao de UM pedido (/loja/pedidos/[id]). Extensao da historia ID 08 / RF-15.
 *
 * O ponto central: quais botoes existem e decidido pelas `acoes` que o
 * servidor manda. Cada teste simula o servidor numa situacao e confere
 * que a tela obedece - sem que o front saiba nada da FSM.
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PaginaGestaoPedido from "@/app/loja/pedidos/[id]/page";
import { ErroApi } from "@/lib/api";
import { ACOES_CANCELADO, LOJA, pedidoGestao } from "../fabricas";

const ID = "3f9a1c07-0000-4000-8000-000000000001";

const nav = vi.hoisted(() => ({
  roteador: { push: vi.fn(), replace: vi.fn() },
}));
const sessao = vi.hoisted(() => ({
  usuario: null as unknown,
  carregando: false,
}));
const loja = vi.hoisted(() => ({
  detalhar: vi.fn(),
  avancar: vi.fn(),
  cancelar: vi.fn(),
  alterarEndereco: vi.fn(),
  excluir: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => nav.roteador,
  useParams: () => ({ id: "3f9a1c07-0000-4000-8000-000000000001" }),
}));
vi.mock("@/componentes/SessaoProvider", () => ({ useSessao: () => sessao }));
vi.mock("@/lib/api", async (original) => ({
  ...(await original<typeof import("@/lib/api")>()),
  loja,
}));

async function abrir() {
  render(<PaginaGestaoPedido />);
  await screen.findByRole("heading", { name: "Pedido" });
}

beforeEach(() => {
  sessao.usuario = LOJA;
});

describe("Gestao de um pedido", () => {
  it("pedido recebido: avancar, cancelar e corrigir endereco; NADA de excluir", async () => {
    loja.detalhar.mockResolvedValueOnce(pedidoGestao());
    await abrir();

    expect(loja.detalhar).toHaveBeenCalledWith(ID);
    expect(
      screen.getByRole("button", { name: "Iniciar preparo" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Cancelar pedido" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Corrigir endereço" }),
    ).toBeInTheDocument();
    // RN-13: pedido em andamento nao se exclui.
    expect(
      screen.queryByRole("button", { name: "Excluir pedido" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(
        /para excluir, o pedido precisa estar entregue ou cancelado/i,
      ),
    ).toBeInTheDocument();
  });

  it("RN-11: depois de sair para entrega, o endereco trava", async () => {
    loja.detalhar.mockResolvedValueOnce(
      pedidoGestao({
        status: "saiu_para_entrega",
        acoes: {
          proximo_status: "entregue",
          pode_cancelar: false,
          pode_editar_endereco: false,
          pode_excluir: false,
        },
      }),
    );
    await abrir();

    expect(
      screen.queryByRole("button", { name: "Corrigir endereço" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Cancelar pedido" }),
    ).not.toBeInTheDocument();
    expect(screen.getByText(/endereço travado/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Confirmar entrega" }),
    ).toBeInTheDocument();
  });

  it("corrigir endereco envia o texto novo e mostra o que o servidor gravou", async () => {
    loja.detalhar.mockResolvedValueOnce(pedidoGestao());
    loja.alterarEndereco.mockResolvedValueOnce(
      pedidoGestao({ endereco_entrega: "Rua das Flores, 132" }),
    );
    await abrir();

    await userEvent.click(
      screen.getByRole("button", { name: "Corrigir endereço" }),
    );
    const campo = screen.getByLabelText("Endereço de entrega");
    expect(campo).toHaveValue("Rua das Flores, 123"); // comeca com o atual
    await userEvent.clear(campo);
    await userEvent.type(campo, "Rua das Flores, 132");
    await userEvent.click(screen.getByRole("button", { name: "Salvar" }));

    expect(loja.alterarEndereco).toHaveBeenCalledWith(
      ID,
      "Rua das Flores, 132",
    );
    expect(await screen.findByText(/endereço atualizado/i)).toBeInTheDocument();
    expect(screen.getByText("Rua das Flores, 132")).toBeInTheDocument();
  });

  it("recusa do servidor aparece como mensagem, e o pedido na tela nao muda", async () => {
    loja.detalhar.mockResolvedValueOnce(pedidoGestao());
    loja.avancar.mockRejectedValueOnce(
      new ErroApi(
        "transicao_invalida",
        "Transicao invalida: cancelado -> proxima etapa",
        409,
      ),
    );
    await abrir();

    await userEvent.click(
      screen.getByRole("button", { name: "Iniciar preparo" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Transicao invalida",
    );
    expect(screen.getAllByText("Recebido").length).toBeGreaterThan(0);
  });

  it("RN-13: excluir pede confirmacao, chama a API e volta para a lista", async () => {
    loja.detalhar.mockResolvedValueOnce(
      pedidoGestao({ status: "cancelado", acoes: ACOES_CANCELADO }),
    );
    loja.excluir.mockResolvedValueOnce(undefined);
    await abrir();

    await userEvent.click(
      screen.getByRole("button", { name: "Excluir pedido" }),
    );

    // Primeiro clique so abre a confirmacao - nada foi apagado ainda.
    expect(loja.excluir).not.toHaveBeenCalled();
    expect(
      screen.getByText(/registro da venda continua guardado/i),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Sim, excluir" }));

    expect(loja.excluir).toHaveBeenCalledWith(ID);
    // `replace`: o "voltar" do navegador nao reabre um pedido excluido.
    expect(nav.roteador.replace).toHaveBeenCalledWith("/loja/pedidos");
  });

  it("desistir na confirmacao nao exclui nada", async () => {
    loja.detalhar.mockResolvedValueOnce(
      pedidoGestao({ status: "cancelado", acoes: ACOES_CANCELADO }),
    );
    await abrir();

    await userEvent.click(
      screen.getByRole("button", { name: "Excluir pedido" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Voltar" }));

    expect(loja.excluir).not.toHaveBeenCalled();
    expect(
      screen.getByRole("button", { name: "Excluir pedido" }),
    ).toBeInTheDocument();
  });

  it("pedido inexistente mostra 'nao encontrado' com caminho de volta", async () => {
    loja.detalhar.mockRejectedValueOnce(
      new ErroApi("pedido_nao_encontrado", "Pedido nao encontrado", 404),
    );
    render(<PaginaGestaoPedido />);

    expect(
      await screen.findByText("Pedido não encontrado."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /voltar aos pedidos/i }),
    ).toHaveAttribute("href", "/loja/pedidos");
  });
});
