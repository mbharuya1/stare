import type { Metadata } from "next";
import { Playfair_Display, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const display = Playfair_Display({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-display",
  display: "swap",
});

const body = Inter({
  subsets: ["latin"],
  axes: ["opsz"],
  variable: "--font-body",
  display: "swap",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Stare. AI Law Assistant.",
  description:
    "Stare is an AI Law Assistant built by lawyers and engineers. Ask a legal question and get an answer grounded in real case law, with every claim verified against the source.",
  metadataBase: new URL("https://stare.app"),
  openGraph: {
    title: "Stare. AI Law Assistant.",
    description:
      "Built by lawyers and engineers. Grounded citations, honest refusal, real precedent.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${body.variable} ${mono.variable}`}
    >
      <body className="min-h-screen bg-cream-100 font-sans text-navy-800 antialiased">
        {/* Top accent stripe, editorial rather than flag-like. */}
        <div
          aria-hidden="true"
          className="h-1 w-full bg-accent-stripe"
        />
        {children}
      </body>
    </html>
  );
}
