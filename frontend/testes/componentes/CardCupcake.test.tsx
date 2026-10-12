/**
 * Card de produto. Historias ID 04 (catalogo) e ID 05 (adicionar).
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { CardCupcake } from "@/componentes/CardCupcake";
import type { Cupcake } from "@/lib/tipos";

const BAUNILHA: Cupcake = {
  id: "c-baunilha",
  nome: "Baunilha Clássico",
  descricao: "Massa de baunilha com cobertura de buttercream",
  sabor: "baunilha",
  preco: "8.50",
  imagem_url: "/images/cupcakes/baunilha.jpg",
  disponivel: true,
};

const PISTACHE: Cupcake = {
  ...BAUNILHA,
  id: "c-pistache",
  nome: "Pistache",
  disponivel: false,
};

describe("CardCupcake", () => {
  it("RN-02: cupcake esgotado NAO tem botao de adicionar", () => {
    render(<CardCupcake cupcake={PISTACHE} aoAdicionar={vi.fn()} />);

    // Ausencia, nao botao desabilitado: botao cinza convida ao clique.
    expect(
      screen.queryByRole("button", { name: /adicionar/i }),
    ).not.toBeInTheDocument();
    expect(screen.getByText("Esgotado")).toBeInTheDocument();
    expect(screen.getByText(/voltamos a produzir/i)).toBeInTheDocument();
  });

  it("cupcake disponivel mostra preco e adiciona 1 unidade por padrao", async () => {
    const aoAdicionar = vi.fn().mockResolvedValue(undefined);
    render(<CardCupcake cupcake={BAUNILHA} aoAdicionar={aoAdicionar} />);

    expect(screen.getByText(/R\$\s8,50/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Adicionar" }));

    expect(aoAdicionar).toHaveBeenCalledWith("c-baunilha", 1);
  });

  it("regressao: apagar o 1 e digitar 3 adiciona 3, nao 13", async () => {
    // Bug real encontrado por este teste: a versao anterior corrigia o
    // campo a cada tecla. Apagar o "1" fazia o campo voltar sozinho para
    // 1, e o "3" digitado em seguida virava 13.
    const aoAdicionar = vi.fn().mockResolvedValue(undefined);
    render(<CardCupcake cupcake={BAUNILHA} aoAdicionar={aoAdicionar} />);

    const campo = screen.getByLabelText(/quantidade de baunilha/i);
    await userEvent.clear(campo);
    await userEvent.type(campo, "3");
    await userEvent.click(screen.getByRole("button", { name: "Adicionar" }));

    expect(aoAdicionar).toHaveBeenCalledWith("c-baunilha", 3);
  });

  it("RN-01 espelhada na tela: quantidade 0 vira 1 antes de enviar", async () => {
    const aoAdicionar = vi.fn().mockResolvedValue(undefined);
    render(<CardCupcake cupcake={BAUNILHA} aoAdicionar={aoAdicionar} />);

    const campo = screen.getByLabelText(/quantidade de baunilha/i);
    await userEvent.clear(campo);
    await userEvent.type(campo, "0");
    await userEvent.click(screen.getByRole("button", { name: "Adicionar" }));

    expect(aoAdicionar).toHaveBeenCalledWith("c-baunilha", 1);
  });

  it("acima de 99 e limitado ao maximo aceito pela API ao sair do campo", async () => {
    render(<CardCupcake cupcake={BAUNILHA} aoAdicionar={vi.fn()} />);

    const campo = screen.getByLabelText(/quantidade de baunilha/i);
    await userEvent.clear(campo);
    await userEvent.type(campo, "150");
    await userEvent.tab(); // sair do campo

    // Sem o limite, a API recusaria com 422 e a pessoa veria um erro
    // tecnico em vez de um numero corrigido.
    expect(campo).toHaveValue(99);
  });

  it("sem foto cadastrada, mostra o sabor no lugar da imagem", () => {
    render(
      <CardCupcake
        cupcake={{ ...BAUNILHA, imagem_url: "" }}
        aoAdicionar={vi.fn()}
      />,
    );

    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.getByText("baunilha")).toBeInTheDocument();
  });

  it("com foto, a imagem tem texto alternativo com o nome do produto", () => {
    render(<CardCupcake cupcake={BAUNILHA} aoAdicionar={vi.fn()} />);

    expect(
      screen.getByRole("img", { name: "Baunilha Clássico" }),
    ).toBeInTheDocument();
  });
});
