import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

/**
 * Configuracao dos testes do front-end.
 *
 * - `jsdom`: um navegador simulado em Node. Os componentes renderizam
 *   de verdade (DOM, eventos, foco), sem abrir Chrome - por isso a suite
 *   inteira roda em poucos segundos.
 * - `alias`: o mesmo `@/` do tsconfig. Sem ele, `import "@/lib/api"`
 *   funcionaria no Next e quebraria aqui.
 * - `setupFiles`: roda antes de cada arquivo de teste (matchers do
 *   jest-dom e limpeza do DOM entre testes).
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      {
        find: /^@\//,
        replacement: fileURLToPath(new URL("./", import.meta.url)),
      },
    ],
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./testes/setup.ts"],
    include: ["testes/**/*.test.{ts,tsx}"],
  },
});
