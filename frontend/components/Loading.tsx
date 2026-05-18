import { Radar } from "lucide-react";

export default function Loading() {
  return (
    <div className="flex h-full w-full flex-1 flex-col items-center justify-center gap-4 py-24">
      <div className="relative flex h-14 w-14 items-center justify-center">
        <span className="absolute inset-0 animate-ping rounded-full bg-primary/15" />
        <span className="absolute inset-0 animate-spin rounded-full border-2 border-primary/20 border-t-primary" />
        <Radar className="h-5 w-5 text-primary" />
      </div>
      <p className="text-sm font-medium text-muted-foreground">
        Chargement des données…
      </p>
    </div>
  );
}
