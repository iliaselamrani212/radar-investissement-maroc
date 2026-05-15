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

const COLORS = ["#2D6A4F", "#40916C", "#52B788", "#74C69D", "#95D5B2", "#B7E4C7", "#D8F3DC"];

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
    <div className="flex flex-col h-full">
      <Header title="Tableau de Bord" />
      <div className="p-8 space-y-8 overflow-y-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KPICard title="Projets Détectés" value={stats?.total_projects || 0} icon={Briefcase} />
          <KPICard title="Investissement Total" value={formatMAD(stats?.total_amount_mad)} icon={DollarSign} />
          <KPICard title="Score Moyen" value={`${stats?.average_score || 0}%`} icon={ShieldCheck} />
          <KPICard
            title="Projets Très Fiables (>80)"
            value={alerts?.items?.length || 0}
            icon={Star}
            description="Récemment détectés"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">Projets par Secteur</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats?.by_sector ?? []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="secteur" fontSize={12} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#2D6A4F" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">Répartition par Région</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats?.by_region ?? []}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="count"
                    nameKey="region"
                    label={({ name, percent }: { name?: string; percent?: number }) =>
                      `${name ?? ""} ${((percent ?? 0) * 100).toFixed(0)}%`
                    }
                  >
                    {(stats?.by_region ?? []).map((_entry: Stats["by_region"][number], index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">Évolution Mensuelle</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stats?.timeline ?? []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="mois" fontSize={12} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="count" name="Projets" stroke="#2D6A4F" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">Projets Récents Fiables</h3>
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b text-gray-500">
                <th className="pb-3 font-medium">Titre</th>
                <th className="pb-3 font-medium">Secteur</th>
                <th className="pb-3 font-medium">Région</th>
                <th className="pb-3 font-medium">Montant</th>
                <th className="pb-3 font-medium">Score</th>
                <th className="pb-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {(alerts?.items ?? []).slice(0, 5).map((p) => (
                <tr key={p.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="py-3 font-medium text-gray-900">{p.titre}</td>
                  <td className="py-3 text-gray-600">{p.secteur}</td>
                  <td className="py-3 text-gray-600">{p.region || "N/A"}</td>
                  <td className="py-3 text-gray-600">{formatMAD(p.montant_mad)}</td>
                  <td className="py-3"><ScoreBadge score={p.score_fiabilite} /></td>
                  <td className="py-3">
                    <Link href={`/projects/${p.id}`}>
                      <Button variant="outline" size="sm">Détails</Button>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
