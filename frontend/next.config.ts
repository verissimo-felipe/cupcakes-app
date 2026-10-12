import type { NextConfig } from "next";

/**
 * Endereco da API visto PELO SERVIDOR do Next (nunca pelo navegador).
 * Em producao: a URL do back-end no Render. Localmente: a porta 8000.
 */
const API_URL = process.env.API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  /**
   * PROXY DA API NA MESMA ORIGEM.
   *
   * O navegador chama `/api/v1/...` no proprio dominio do front, e o Next
   * repassa para a API. Por que nao chamar a API direto?
   *
   * A sessao e um cookie `httpOnly` com `SameSite=Lax`. Com front em
   * `*.vercel.app` e API em `*.onrender.com`, os dois sao SITES
   * diferentes (ambos os dominios estao na Public Suffix List), e o
   * navegador nao envia esse cookie entre eles: o login "funciona" e a
   * tela seguinte responde 401.
   *
   * Com o proxy, para o navegador so existe um site. O cookie fica no
   * dominio do front, e nao e preciso afrouxar para `SameSite=None` -
   * que reabriria a porta para CSRF e ainda e bloqueado por navegadores
   * que recusam cookie de terceiros.
   *
   * ATENCAO: `rewrites` e calculado no BUILD. Mudou `API_URL` no painel
   * da hospedagem? Faca um novo deploy.
   */
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${API_URL}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
