import type {
  Carrinho,
  Cupcake,
  Pedido,
  PedidoGestao,
  PedidoGestaoResumo,
  PedidoResumo,
  StatusPedido,
  Usuario,
} from "./tipos";

const BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const API = `${BASE}/api/v1`;

/**
 * Erro vindo da API, carregando o codigo do back-end.
 *
 * O back-end tem um tratador central que devolve SEMPRE o mesmo formato:
 *   { "codigo": "cupcake_indisponivel", "mensagem": "..." }
 *
 * Guardamos `codigo` separado porque a interface deve decidir o que fazer
 * pelo codigo, nunca casando o texto da mensagem - texto muda, codigo e
 * contrato.
 */
export class ErroApi extends Error {
  constructor(
    readonly codigo: string,
    mensagem: string,
    readonly status: number,
  ) {
    super(mensagem);
    this.name = "ErroApi";
  }
}

type Payload = Record<string, unknown>;

/**
 * Wrapper unico de rede. Nenhum componente chama `fetch` direto.
 *
 * `credentials: "include"` E A LINHA MAIS IMPORTANTE DESTE ARQUIVO.
 *
 * A sessao usa JWT em cookie httpOnly - o JavaScript nao consegue ler nem
 * gravar esse cookie, e isso e a defesa contra roubo de sessao por XSS.
 * Mas o `fetch` NAO envia cookies para outra origem por padrao, e o front
 * (porta 3000) e o back (porta 8000) sao origens diferentes.
 *
 * Sem esta opcao toda rota autenticada devolve 401, e o sintoma parece
 * bug de login em vez de configuracao de rede. Centralizar aqui garante
 * que ninguem esqueca.
 */
async function requisitar<T>(
  caminho: string,
  opcoes: { metodo?: string; corpo?: Payload } = {},
): Promise<T> {
  const { metodo = "GET", corpo } = opcoes;

  let resposta: Response;
  try {
    resposta = await fetch(`${API}${caminho}`, {
      method: metodo,
      credentials: "include",
      headers: corpo ? { "Content-Type": "application/json" } : undefined,
      body: corpo ? JSON.stringify(corpo) : undefined,
      cache: "no-store",
    });
  } catch {
    // Falha de rede: servidor fora do ar, CORS recusado, DNS. O `fetch`
    // so rejeita nesses casos - status 4xx e 5xx resolvem normalmente.
    throw new ErroApi(
      "sem_conexao",
      "Nao foi possivel falar com o servidor. Verifique se ele esta no ar.",
      0,
    );
  }

  if (resposta.status === 204) {
    return undefined as T;
  }

  const dados = await resposta.json().catch(() => null);

  if (!resposta.ok) {
    throw traduzirErro(dados, resposta.status);
  }

  return dados as T;
}

/**
 * Normaliza os TRES formatos de erro que a API pode devolver.
 *
 * 1. Tratador de dominio:  { codigo, mensagem }
 * 2. HTTPException:        { detail: { codigo, mensagem } }
 * 3. Validacao do Pydantic:{ detail: [ { loc, msg, type }, ... ] }
 *
 * O terceiro aparece quando o payload nem chega ao nosso codigo - campo
 * faltando, tipo errado, e-mail malformado. Sem esta traducao, a tela
 * mostraria "[object Object]".
 */
function traduzirErro(dados: unknown, status: number): ErroApi {
  const generico = new ErroApi(
    "erro_desconhecido",
    "Algo deu errado. Tente novamente.",
    status,
  );

  if (!dados || typeof dados !== "object") return generico;

  const corpo = dados as Record<string, unknown>;

  if (typeof corpo.codigo === "string" && typeof corpo.mensagem === "string") {
    return new ErroApi(corpo.codigo, corpo.mensagem, status);
  }

  const detail = corpo.detail;

  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    const d = detail as Record<string, unknown>;
    if (typeof d.codigo === "string" && typeof d.mensagem === "string") {
      return new ErroApi(d.codigo, d.mensagem, status);
    }
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const primeiro = detail[0] as Record<string, unknown>;
    const campo = Array.isArray(primeiro.loc)
      ? String(primeiro.loc[primeiro.loc.length - 1])
      : "";
    const msg = typeof primeiro.msg === "string" ? primeiro.msg : "";
    return new ErroApi(
      "dados_invalidos",
      campo ? `Confira o campo "${campo}": ${msg}` : msg || generico.message,
      status,
    );
  }

  return generico;
}

// ------------------------------------------------------------------
// Autenticacao - historias ID 01, 02
// ------------------------------------------------------------------

export const auth = {
  registrar: (nome: string, email: string, senha: string) =>
    requisitar<Usuario>("/auth/registrar", {
      metodo: "POST",
      corpo: { nome, email, senha },
    }),

  entrar: (email: string, senha: string) =>
    requisitar<Usuario>("/auth/login", {
      metodo: "POST",
      corpo: { email, senha },
    }),

  sair: () => requisitar<void>("/auth/logout", { metodo: "POST" }),

  eu: () => requisitar<Usuario>("/auth/eu"),
};

// ------------------------------------------------------------------
// Catalogo - historia ID 04
// ------------------------------------------------------------------

export const catalogo = {
  listar: (busca?: string) => {
    const query = busca?.trim()
      ? `?busca=${encodeURIComponent(busca.trim())}`
      : "";
    return requisitar<Cupcake[]>(`/cupcakes${query}`);
  },

  detalhar: (id: string) => requisitar<Cupcake>(`/cupcakes/${id}`),
};

// ------------------------------------------------------------------
// Carrinho - historias ID 05, 06
// ------------------------------------------------------------------

export const carrinho = {
  ver: () => requisitar<Carrinho>("/carrinho"),

  adicionar: (cupcake_id: string, quantidade = 1) =>
    requisitar<Carrinho>("/carrinho/itens", {
      metodo: "POST",
      corpo: { cupcake_id, quantidade },
    }),

  alterarQuantidade: (cupcake_id: string, quantidade: number) =>
    requisitar<Carrinho>(`/carrinho/itens/${cupcake_id}`, {
      metodo: "PATCH",
      corpo: { quantidade },
    }),

  remover: (cupcake_id: string) =>
    requisitar<Carrinho>(`/carrinho/itens/${cupcake_id}`, {
      metodo: "DELETE",
    }),
};

// ------------------------------------------------------------------
// Pedidos - historias ID 07, 08
// ------------------------------------------------------------------

export const pedidos = {
  finalizar: (endereco_entrega: string) =>
    requisitar<Pedido>("/pedidos", {
      metodo: "POST",
      corpo: { endereco_entrega },
    }),

  listar: () => requisitar<PedidoResumo[]>("/pedidos"),

  detalhar: (id: string) => requisitar<Pedido>(`/pedidos/${id}`),
};

// ------------------------------------------------------------------
// Gestao da loja - extensao da historia ID 08 / RF-15
//
// Todas exigem conta listada em ADMIN_EMAILS no back-end. Cliente comum
// recebe 403 (`acesso_negado`) em QUALQUER uma delas: a protecao esta no
// router inteiro do servidor, nao rota a rota.
// ------------------------------------------------------------------

export const loja = {
  /** Sem filtro: a tela filtra localmente para mostrar a contagem por etapa. */
  listar: (status?: StatusPedido) =>
    requisitar<PedidoGestaoResumo[]>(
      `/admin/pedidos${status ? `?status=${status}` : ""}`,
    ),

  detalhar: (id: string) => requisitar<PedidoGestao>(`/admin/pedidos/${id}`),

  /** Uma etapa adiante. O servidor decide qual - a tela nao escolhe destino. */
  avancar: (id: string) =>
    requisitar<PedidoGestao>(`/admin/pedidos/${id}/avancar`, { metodo: "POST" }),

  cancelar: (id: string) =>
    requisitar<PedidoGestao>(`/admin/pedidos/${id}/cancelar`, { metodo: "POST" }),

  alterarEndereco: (id: string, endereco_entrega: string) =>
    requisitar<PedidoGestao>(`/admin/pedidos/${id}`, {
      metodo: "PATCH",
      corpo: { endereco_entrega },
    }),

  /** Exclusao LOGICA: some das listas, continua no banco. 204 sem corpo. */
  excluir: (id: string) =>
    requisitar<void>(`/admin/pedidos/${id}`, { metodo: "DELETE" }),
};
