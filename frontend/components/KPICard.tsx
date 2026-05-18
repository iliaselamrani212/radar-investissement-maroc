import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  description?: string;
  trend?: { value: string; up?: boolean };
  accent?: "primary" | "info" | "warning" | "success";
}

const ACCENTS: Record<string, string> = {
  primary: "bg-primary/10 text-primary",
  info: "bg-info/10 text-info",
  warning: "bg-warning/10 text-warning",
  success: "bg-success/10 text-success",
};

export default function KPICard({
  title,
  value,
  icon: Icon,
  description,
  trend,
  accent = "primary",
}: KPICardProps) {
  return (
    <div className="surface surface-hover animate-rise p-5">
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        <div
          className={`flex h-9 w-9 items-center justify-center rounded-lg ${ACCENTS[accent]}`}
        >
          <Icon className="h-[18px] w-[18px]" />
        </div>
      </div>

      <div className="mt-3 flex items-end gap-2">
        <span className="text-[28px] font-semibold leading-none tracking-tight tabular-nums text-foreground">
          {value}
        </span>
        {trend && (
          <span
            className={`stat-chip mb-0.5 ${
              trend.up
                ? "bg-success/10 text-success"
                : "bg-destructive/10 text-destructive"
            }`}
          >
            {trend.up ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            {trend.value}
          </span>
        )}
      </div>

      {description && (
        <p className="mt-2 text-xs text-muted-foreground">{description}</p>
      )}
    </div>
  );
}
