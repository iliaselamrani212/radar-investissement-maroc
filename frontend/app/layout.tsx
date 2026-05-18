import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "InvestiGator 43",
  description: "Dashboard d'analyse et priorisation des projets d'investissement",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body>
        <Providers>
          <div className="flex h-screen bg-background">
            <Sidebar />
            <main className="flex-1 overflow-y-auto">
              <div className="animate-fade-in">{children}</div>
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
