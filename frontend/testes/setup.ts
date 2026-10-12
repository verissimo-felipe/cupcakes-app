import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

// Sem `globals: true` no Vitest, o Testing Library nao registra a limpeza
// sozinho. Cada teste comeca com o DOM vazio e sem mocks de rodadas
// anteriores - um teste nunca depende da ordem em que os outros rodaram.
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
