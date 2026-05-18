export default function ScoreBadge({
  score,
}: {
  score: number | null | undefined;
}) {
  if (score === null || score === undefined)
    return <span className="text-xs text-muted-foreground">N/A</span>;

  const tone =
    score >= 80
      ? { dot: "bg-success", text: "text-success", bg: "bg-success/10" }
      : score >= 60
      ? { dot: "bg-info", text: "text-info", bg: "bg-info/10" }
      : score >= 40
      ? { dot: "bg-warning", text: "text-warning", bg: "bg-warning/10" }
      : { dot: "bg-slate-400", text: "text-slate-500", bg: "bg-slate-100" };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold tabular-nums ${tone.bg} ${tone.text}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${tone.dot}`} />
      {score.toFixed(0)}%
    </span>
  );
}
