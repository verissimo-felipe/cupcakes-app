import { describe, expect, it } from "vitest";
import {
  formatarDataHora,
  formatarPreco,
  idCurto,
  rotuloAvancar,
  rotuloStatus,
} from "@/lib/formato";

// `\s` casa o espaco nao separavel (U+00A0) que o Intl coloca entre
// "R$" e o numero. Comparar com " " comum falharia sem motivo visivel.
describe("formatarPreco", () => {
  it("converte a string decimal da API para reais", () => {
    expect(formatarPreco("17.00")).toMatch(/^R\$\s17,00$/);
  });

  it("usa separador de milhar e duas casas", () => {
    expect(formatarPreco("1234.5")).toMatch(/^R\$\s1\.234,50$/);
  });
});

describe("rotulos", () => {
  it("botao de avancar usa o verbo da acao, nao o nome do estado", () => {
    expect(rotuloAvancar("em_preparo")).toBe("Iniciar preparo");
    expect(rotuloAvancar("saiu_para_entrega")).toBe("Enviar para entrega");
    expect(rotuloAvancar("entregue")).toBe("Confirmar entrega");
  });

  it("status tem rotulo legivel", () => {
    expect(rotuloStatus("saiu_para_entrega")).toBe("Saiu para entrega");
  });
});

describe("identificacao e datas", () => {
  it("numero curto do pedido tem 8 caracteres", () => {
    expect(idCurto("3f9a1c07-0000-4000-8000-000000000001")).toBe("3f9a1c07");
  });

  it("data ausente vira travessao, nao 'Invalid Date'", () => {
    expect(formatarDataHora(null)).toBe("—");
  });
});
