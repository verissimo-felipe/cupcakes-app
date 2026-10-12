/**
 * Linha do tempo do pedido. Historia ID 08 / RF-14.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LinhaDoTempo } from "@/componentes/LinhaDoTempo";

describe("LinhaDoTempo", () => {
  it("mostra as 4 etapas na ordem da FSM e marca a atual para leitor de tela", () => {
    render(<LinhaDoTempo status="em_preparo" />);

    const etapas = screen.getAllByRole("listitem").map((li) => li.textContent);
    expect(etapas[0]).toContain("Recebido");
    expect(etapas[1]).toContain("Em preparo");
    expect(etapas[2]).toContain("Saiu para entrega");
    expect(etapas[3]).toContain("Entregue");

    // `aria-current="step"`: quem nao enxerga a cor ainda sabe onde o
    // pedido esta.
    const atual = screen.getByText("Etapa atual");
    expect(atual).toHaveAttribute("aria-current", "step");
    expect(atual.closest("li")).toHaveTextContent("Em preparo");
  });

  it("cancelado e desvio, nao etapa: mostra aviso proprio em vez da linha", () => {
    render(<LinhaDoTempo status="cancelado" />);

    expect(screen.getByText("Pedido cancelado")).toBeInTheDocument();
    expect(screen.queryByRole("list")).not.toBeInTheDocument();
  });
});
