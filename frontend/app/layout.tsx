import type { Metadata } from "next";
import { Fraunces, Karla } from "next/font/google";
import { SessaoProvider } from "@/componentes/SessaoProvider";
import { Cabecalho } from "@/componentes/Cabecalho";
import "./globals.css";

/**
 * Fraunces no display: serifa com eixo `wonk`, que inclina levemente as
 * formas. Irregularidade proposital, coerente com confeitaria artesanal -
 * e distante da serifa alta e neutra que qualquer pagina usaria.
 *
 * Karla no corpo: grotesca com letterforms um pouco peculiares, legivel
 * em texto pequeno sem o ar corporativo das grotescas padrao.
 */
const fraunces = Fraunces({
  variable: "--fonte-display",
  subsets: ["latin"],
  axes: ["SOFT", "WONK"],
});

const karla = Karla({
  variable: "--fonte-corpo",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Doce Forma — cupcakes feitos no dia",
  description:
    "Cupcakes artesanais com entrega. Escolha os sabores, monte seu pedido e acompanhe a entrega.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="pt-BR"
      className={`${fraunces.variable} ${karla.variable} h-full`}
    >
      <body className="flex min-h-full flex-col">
        <SessaoProvider>
          <Cabecalho />
          <main className="flex-1">{children}</main>
          <footer className="mt-24 border-t border-papel-fundo px-6 py-8 text-center text-minuscula text-tinta-suave">
            Doce Forma — projeto acadêmico, Projeto Integrador Transdisciplinar II
          </footer>
        </SessaoProvider>
      </body>
    </html>
  );
}
