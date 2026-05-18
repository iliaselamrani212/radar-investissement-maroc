"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FolderKanban,
  ClipboardList,
  BarChart3,
  Map,
  Radar,
  BrainCircuit,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Tableau de bord", icon: LayoutDashboard },
  { href: "/projects", label: "Projets", icon: FolderKanban },
  { href: "/tracking", label: "Suivi", icon: ClipboardList },
  { href: "/ai", label: "IA locale", icon: BrainCircuit },
  { href: "/analytics", label: "Analytique", icon: BarChart3 },
  { href: "/map", label: "Carte", icon: Map },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-64 shrink-0 flex-col bg-sidebar text-slate-300">
      {/* Brand */}
      <div className="flex items-center gap-3 px-6 py-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sidebar-accent/15 ring-1 ring-sidebar-accent/30">
          <Radar className="h-5 w-5 text-sidebar-accent" />
        </div>
        <div>
          <h1 className="text-[15px] font-semibold leading-tight text-white">
            InvestiGator 43
          </h1>
          <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
            Projets Maroc
          </p>
        </div>
      </div>

      <div className="mx-6 mb-4 h-px bg-white/10" />

      <p className="px-6 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
        Navigation
      </p>

      <nav className="flex-1 space-y-1 px-3">
        {links.map((link) => {
          const isActive =
            link.href === "/"
              ? pathname === "/"
              : pathname.startsWith(link.href);

          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-white/[0.07] text-white"
                  : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-100"
              )}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-sidebar-accent" />
              )}
              <link.icon
                className={cn(
                  "h-[18px] w-[18px] transition-colors",
                  isActive
                    ? "text-sidebar-accent"
                    : "text-slate-500 group-hover:text-slate-300"
                )}
              />
              {link.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer status */}
      <div className="m-3 rounded-lg bg-white/[0.04] px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
          </span>
          <span className="text-xs font-medium text-slate-300">
            Système actif
          </span>
        </div>
        <p className="mt-1 text-[11px] text-slate-500">
          IA locale · Ollama Qwen 2.5
        </p>
      </div>
    </aside>
  );
}
