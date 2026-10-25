import type { Metadata } from "next";
import type { ReactNode } from "react";
import "@fontsource-variable/manrope";
import "./base.css";

export const metadata: Metadata = {
  title: "StoreScout",
  description: "Retail expansion decisions with traceable assumptions.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
