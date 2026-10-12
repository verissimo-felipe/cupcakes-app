/**
 * Cliente de API (`lib/api.ts`) - o unico ponto do front que fala com o
 * servidor.
 *
 * O `fetch` e substituido por um dublê: nenhum teste aqui depende do
 * back-end estar no ar. O que se verifica e o CONTRATO do wrapper:
 *   - todo pedido leva o cookie de sessao (`credentials: "include"`);
 *   - os tres formatos de erro da API viram um unico `ErroApi`;
 *   - falha de rede vira mensagem compreensivel, nao "TypeError".
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { auth, ErroApi, loja, pedidos } from "@/lib/api";

const fetchFalso = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", fetchFalso);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function responder(status: number, corpo?: unknown) {
  fetchFalso.mockResolvedValueOnce(
    new Response(corpo === undefined ? null : JSON.stringify(corpo), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

async function capturarErro(promessa: Promise<unknown>): Promise<ErroApi> {
  try {
    await promessa;
  } catch (e) {
    expect(e).toBeInstanceOf(ErroApi);
    return e as ErroApi;
  }
  throw new Error("era esperado um ErroApi");
}

describe("envio", () => {
  it("todo pedido leva o cookie de sessao (credentials: include)", async () => {
    responder(200, {
      id: "u1",
      nome: "Ana",
      email: "ana@mail.com",
      admin: false,
    });

    await auth.entrar("ana@mail.com", "senha-longa-o-bastante");

    const [url, opcoes] = fetchFalso.mock.calls[0];
    expect(url).toMatch(/\/api\/v1\/auth\/login$/);
    expect(opcoes.method).toBe("POST");
    // Sem isto o navegador nao envia o cookie httpOnly para a porta 8000,
    // e toda rota autenticada responde 401.
    expect(opcoes.credentials).toBe("include");
    expect(JSON.parse(opcoes.body)).toEqual({
      email: "ana@mail.com",
      senha: "senha-longa-o-bastante",
    });
  });

  it("checkout envia SO o endereco - nunca itens ou precos", async () => {
    responder(201, { id: "p1" });

    await pedidos.finalizar("Rua das Flores, 123");

    const corpo = JSON.parse(fetchFalso.mock.calls[0][1].body);
    expect(corpo).toEqual({ endereco_entrega: "Rua das Flores, 123" });
  });

  it("204 sem corpo resolve sem erro (exclusao de pedido)", async () => {
    responder(204);
    await expect(loja.excluir("p1")).resolves.toBeUndefined();
  });
});

describe("traducao de erros", () => {
  it("formato do tratador de dominio: { codigo, mensagem }", async () => {
    responder(409, {
      codigo: "cupcake_indisponivel",
      mensagem: "Cupcake indisponivel: Pistache",
    });

    const erro = await capturarErro(pedidos.listar());

    expect(erro.codigo).toBe("cupcake_indisponivel");
    expect(erro.message).toBe("Cupcake indisponivel: Pistache");
    expect(erro.status).toBe(409);
  });

  it("formato do HTTPException: { detail: { codigo, mensagem } }", async () => {
    responder(403, {
      detail: { codigo: "acesso_negado", mensagem: "Operacao restrita" },
    });

    const erro = await capturarErro(loja.listar());

    expect(erro.codigo).toBe("acesso_negado");
    expect(erro.status).toBe(403);
  });

  it("formato de validacao do Pydantic: lista de campos invalidos", async () => {
    responder(422, {
      detail: [
        {
          loc: ["body", "endereco_entrega"],
          msg: "String too short",
          type: "string_too_short",
        },
      ],
    });

    const erro = await capturarErro(pedidos.finalizar("x"));

    expect(erro.codigo).toBe("dados_invalidos");
    // Aponta o campo - sem traducao, a tela mostraria "[object Object]".
    expect(erro.message).toContain("endereco_entrega");
  });

  it("resposta que nao e JSON vira erro generico, nao excecao de parse", async () => {
    fetchFalso.mockResolvedValueOnce(
      new Response("<html>502 Bad Gateway</html>", { status: 502 }),
    );

    const erro = await capturarErro(pedidos.listar());

    expect(erro.codigo).toBe("erro_desconhecido");
    expect(erro.status).toBe(502);
  });

  it("servidor fora do ar vira mensagem compreensivel", async () => {
    fetchFalso.mockRejectedValueOnce(new TypeError("Failed to fetch"));

    const erro = await capturarErro(auth.eu());

    expect(erro.codigo).toBe("sem_conexao");
    expect(erro.status).toBe(0);
    expect(erro.message).toMatch(/servidor/i);
  });
});
