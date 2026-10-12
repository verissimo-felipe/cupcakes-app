/**
 * Defesa contra OPEN REDIRECT (CWE-601) no `?voltar=` do login.
 *
 * Cada caso abaixo e um formato que um golpista usaria num link
 * `/login?voltar=...` para levar a vitima, logo depois de digitar a
 * senha no site verdadeiro, para um site falso.
 */
import { describe, expect, it } from "vitest";
import { caminhoSeguro } from "@/lib/navegacao";

describe("caminhoSeguro", () => {
  it("aceita caminho interno", () => {
    expect(caminhoSeguro("/carrinho")).toBe("/carrinho");
    expect(caminhoSeguro("/pedidos/abc?x=1")).toBe("/pedidos/abc?x=1");
  });

  it("sem destino, volta para a pagina inicial", () => {
    expect(caminhoSeguro(null)).toBe("/");
    expect(caminhoSeguro("")).toBe("/");
  });

  it("recusa URL absoluta de outro site", () => {
    expect(caminhoSeguro("https://site-falso.com")).toBe("/");
    expect(caminhoSeguro("javascript:alert(1)")).toBe("/");
  });

  it("recusa // - o navegador trata como outro dominio", () => {
    expect(caminhoSeguro("//site-falso.com")).toBe("/");
  });

  it("recusa barra invertida - alguns navegadores a tratam como //", () => {
    expect(caminhoSeguro("/\\site-falso.com")).toBe("/");
  });

  it("usa o padrao informado quando recusa", () => {
    expect(caminhoSeguro("//x.com", "/pedidos")).toBe("/pedidos");
  });
});
