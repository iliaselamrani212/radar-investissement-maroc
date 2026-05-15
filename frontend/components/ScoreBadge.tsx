import { scoreColor } from "@/lib/api";

export default function ScoreBadge({ score }: { score: number | null | undefined }) {
  if (score === null || score === undefined) return <span className="text-xs text-gray-400">N/A</span>;
  
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${scoreColor(score)}`}>
      {score.toFixed(1)}%
    </span>
  );
}