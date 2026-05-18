"use client";

import { useQuery } from "@tanstack/react-query";
import {
  fetchRecentAlerts,
  fetchStats,
  formatMAD,
  type Project,
  type Stats,
} from "@/lib/api";
import Header from "@/components/Header";
import KPICard from "@/components/KPICard";
import ScoreBadge from "@/components/ScoreBadge";
import Loading from "@/components/Loading";
import { Briefcase, DollarSign, ShieldCheck, Star } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
} from "recharts";
import Link from "next/link";
import { Button } from "@/components/ui/button";

const CHART = [
  "hsl(158 58% 30%)",
  "hsl(173 48% 42%)",
  "hsl(197 50% 45%)",
  "hsl(43 74% 52%)",
  "hsl(262 45% 55%)",
  "hsl(14 70% 55%)",
];

const tooltipStyle = {
  borderRadius: 10,
  border: "1px solid hsl(214 20% 90%)",
  boxShadow: "0 4px 12px rgba(16,24,40,0.08)",
  fontSize: 13,
};

function ChartCard({
  title,
  children,
  delay = 0,
}: {
  title: string;
  children: React.ReactNode;
  delay?: number;
}) {
  return (
    <div
      className="surface animate-rise p-6"
      style={{ animationDelay: `${delay}ms` }}
    >
      <h3 className="mb-5 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h3>
      <div className="h-72">{children}</div>
    </div>
  );
}

export default function DashboardPage() {
  const { data: stats, isLoading: l1 } = useQuery<Stats>({
    queryKey: ["stats"],
    queryFn: fetchStats,
  });
  const { data: alerts, isLoading: l2 } = useQuery<{ items: Project[] }>({
    queryKey: ["alerts"],
    queryFn: fetchRecentAlerts,
  });

  if (l1 || l2) return <Loading />;

  return (
    <div className="flex h-full flex-col">
      <Header
        title="Tableau de bord"
        subtitle="Vue d'ensemble des investissements détectés au Maroc"
      />

      <div className="space-y-6 overflow-y-auto p-8">
        {/* KPIs */}
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-4">
          <KPICard
            title="Projets détectés"
            value={stats?.total_projects || 0}
            icon={Briefcase}
            accent="primary"
            description="Opportunites consolidees"
          />
          <KPICard
            title="Investissement total"
            value={formatMAD(stats?.total_amount_mad)}
            icon={DollarSign}
            accent="success"
            description="Montant cumulé estimé"
          />
          <KPICard
            title="Score moyen"
            value={`${stats?.average_score || 0}%`}
            icon={ShieldCheck}
            accent="info"
            description="Fiabilité moyenne des extractions"
          />
          <KPICard
            title="Projets très fiables"
            value={alerts?.items?.length || 0}
            icon={Star}
            accent="warning"
            description="Score supérieur à 80"
          />
        </div>

        {/* Charts row 1 */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <ChartCard title="Projets par secteur" delay={60}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats?.by_sector ?? []}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(214 20% 92%)" vertical={false} />
                <XAxis
                  dataKey="secteur"
                  fontSize={12}
                  tickLine={false}
                  axisLine={{ stroke: "hsl(214 20% 90%)" }}
                  tick={{ fill: "hsl(215 16% 47%)" }}
                />
                <YAxis
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: "hsl(215 16% 47%)" }}
                />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "hsl(210 30% 96%)" }} />
                <Bar dataKey="count" fill={CHART[0]} radius={[6, 6, 0, 0]} maxBarSize={48} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Répartition par région" delay={120}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats?.by_region ?? []}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={95}
                  paddingAngle={2}
                  dataKey="count"
                  nameKey="region"
                  label={({ name, percent }: { name?: string; percent?: number }) =>
                    `${name ?? ""} ${((percent ?? 0) * 100).toFixed(0)}%`
                  }
                  labelLine={false}
                  fontSize={11}
                >
                  {(stats?.by_region ?? []).map((_e, i) => (
                    <Cell key={i} fill={CHART[i % CHART.length]} stroke="white" strokeWidth={2} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Timeline */}
        <ChartCard title="Évolution mensuelle" delay={180}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={stats?.timeline ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(214 20% 92%)" vertical={false} />
              <XAxis
                dataKey="mois"
                fontSize={12}
                tickLine={false}
                axisLine={{ stroke: "hsl(214 20% 90%)" }}
                tick={{ fill: "hsl(215 16% 47%)" }}
              />
              <YAxis
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tick={{ fill: "hsl(215 16% 47%)" }}
              />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 13 }} />
              <Line
                type="monotone"
                dataKey="count"
                name="Projets"
                stroke={CHART[0]}
                strokeWidth={2.5}
                dot={{ r: 3, fill: CHART[0] }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Recent reliable projects */}
        <div className="surface animate-rise p-6" style={{ animationDelay: "240ms" }}>
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Projets récents fiables
          </h3>
          <div className="overflow-hidden rounded-lg border border-border">
            <table className="w-full text-left text-sm">
              <thead className="bg-secondary/60 text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium">Titre</th>
                  <th className="px-4 py-3 font-medium">Secteur</th>
                  <th className="px-4 py-3 font-medium">Région</th>
                  <th className="px-4 py-3 font-medium">Montant</th>
                  <th className="px-4 py-3 font-medium">Score</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {(alerts?.items ?? []).slice(0, 6).map((p) => (
                  <tr
                    key={p.id}
                    className="border-t border-border transition-colors hover:bg-secondary/40"
                  >
                    <td className="max-w-xs truncate px-4 py-3 font-medium text-foreground">
                      {p.titre}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{p.secteur}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {p.region || "N/A"}
                    </td>
                    <td className="px-4 py-3 tabular-nums text-muted-foreground">
                      {formatMAD(p.montant_mad)}
                    </td>
                    <td className="px-4 py-3">
                      <ScoreBadge score={p.score_fiabilite} />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link href={`/projects/${p.id}`}>
                        <Button variant="outline" size="sm">
                          Détails
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
                {!alerts?.items?.length && (
                  <tr>
                    <td
                      colSpan={6}
                      className="px-4 py-8 text-center text-sm text-muted-foreground"
                    >
                      Aucun projet fiable détecté. Lancez le scraper pour peupler la base.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
