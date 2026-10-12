"use client";

/**
 * Mensagem de erro ou sucesso.
 *
 * O texto vem pronto do back-end (campo `mensagem` do tratador central).
 * Nao reescrevemos aqui: a mensagem do servidor e a fonte unica, e
 * duplicar o texto no front criaria duas versoes que divergem.
 *
 * `role="alert"` faz o leitor de tela anunciar assim que o elemento
 * aparece - sem isso, quem navega por teclado preenche o formulario de
 * novo sem saber que houve erro.
 */
export function Alerta({
  tipo = "erro",
  children,
}: {
  tipo?: "erro" | "sucesso";
  children: React.ReactNode;
}) {
  const estilo =
    tipo === "erro"
      ? "border-framboesa/30 bg-framboesa/10 text-framboesa"
      : "border-emerald-600/30 bg-emerald-50 text-emerald-800";

  return (
    <p
      role="alert"
      className={`rounded-lg border px-4 py-3 text-sm ${estilo}`}
    >
      {children}
    </p>
  );
}
