"use client";

import { Bell, Search } from "lucide-react";
import { Input } from "@/components/ui/input";

interface HeaderProps {
  title: string;
  subtitle?: string;
  onSearch?: (value: string) => void;
}

export default function Header({ title, subtitle, onSearch }: HeaderProps) {
  return (
    <header className="sticky top-0 z-20 flex items-center justify-between border-b border-border bg-white/85 px-8 py-4 backdrop-blur-md">
      <div>
        <h2 className="text-xl font-semibold tracking-tight text-foreground">
          {title}
        </h2>
        {subtitle && (
          <p className="mt-0.5 text-sm text-muted-foreground">{subtitle}</p>
        )}
      </div>

      <div className="flex items-center gap-3">
        {onSearch && (
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Rechercher un projet…"
              className="h-9 w-72 rounded-lg bg-secondary/60 pl-9 text-sm"
              onChange={(e) => onSearch(e.target.value)}
            />
          </div>
        )}
        <button
          aria-label="Notifications"
          className="relative rounded-lg border border-border bg-white p-2 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
        >
          <Bell className="h-[18px] w-[18px]" />
          <span className="absolute -right-0.5 -top-0.5 flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-destructive opacity-60" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-destructive ring-2 ring-white" />
          </span>
        </button>
      </div>
    </header>
  );
}
