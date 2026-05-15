"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, FolderKanban, BarChart3, Map, Radar } from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/projects", label: "Projets", icon: FolderKanban },
  { href: "/analytics", label: "Analytique", icon: BarChart3 },
  { href: "/map", label: "Carte", icon: Map },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-primary text-primary-foreground flex flex-col">
      <div className="p-6 flex items-center gap-2 border-b border-green-800">
        <Radar className="h-8 w-8" />
        <h1 className="text-xl font-bold">Radar Maroc</h1>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={cn(
              "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
              pathname === link.href
                ? "bg-white/20 font-semibold"
                : "hover:bg-white/10"
            )}
          >
            <link.icon className="h-5 w-5" />
            {link.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}