/**
 * Valida o destino de `?voltar=` antes de redirecionar.
 *
 * OPEN REDIRECT (CWE-601)
 * -----------------------
 * Sem esta checagem, um link como
 *   /login?voltar=https://doceforma-pagamento.com
 * levaria a pessoa, DEPOIS de digitar a senha no site verdadeiro, para
 * um site falso - que pede "confirme o cartao". O dominio legitimo na
 * barra de endereco durante o login e o que torna o golpe convincente.
 *
 * Regra: so caminhos internos. Comeca com UMA barra, nunca com duas -
 * `//site.com` e uma URL de outro dominio para o navegador, mesmo sem
 * `https:`. Barra invertida tambem e recusada: alguns navegadores
 * tratam `/\site.com` como `//site.com`.
 */
export function caminhoSeguro(destino: string | null, padrao = "/"): string {
  if (!destino) return padrao;
  if (!destino.startsWith("/")) return padrao;
  if (destino.startsWith("//") || destino.includes("\\")) return padrao;
  return destino;
}
