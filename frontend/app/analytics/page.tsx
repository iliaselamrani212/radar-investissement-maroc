"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchStats, type Stats } from "@/lib/api";
import Header from "@/components/Header";
import Loading from "@/components/Loading";
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
} from "recharts";

const COLORS = ["#2D6A4F", "#40916C", "#52B788", "#74C69D", "#95D5B2", "#B7E4C7"];

export default function AnalyticsPage() {
  const { data: stats, isLoading } = useQuery<Stats>({
    queryKey: ["stats"],
    queryFn: fetchStats,
  });

  if (isLoading) return <Loading />;

  return (
    <div className="flex flex-col h-full">
      <Header title="Analytique" />

      <div className="p-8 space-y-8 overflow-y-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">
              Montant par Secteur (MAD)
            </h3>

            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats?.by_sector ?? []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="secteur" fontSize={12} />
                  <YAxis />
                  <Tooltip
                    formatter={(value) =>
                      `${new Intl.NumberFormat("fr-MA").format(Number(value))} MAD`
                    }
                  />
                  <Bar dataKey="total" fill="#2D6A4F" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">
              Top Régions par Montant
            </h3>

            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats?.by_region?.slice(0, 5) ?? []} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="region" type="category" fontSize={12} width={100} />
                  <Tooltip
                    formatter={(value) =>
                      `${new Intl.NumberFormat("fr-MA").format(Number(value))} MAD`
                    }
                  />
                  <Bar dataKey="total" fill="#40916C" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">
              Distribution par Stade
            </h3>

            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats?.by_stade ?? []}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="count"
                    nameKey="stade"
                    label
                  >
                    {(stats?.by_stade ?? []).map((_entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">
              Top Projets par Investissement
            </h3>

            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={(stats?.by_sector ?? []).slice(0, 6).map((s) => ({
                    secteur: s.secteur,
                    projets: s.count,
                    montant: Math.round((s.total ?? 0) / 1e6),
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="secteur" fontSize={11} />
                  <YAxis yAxisId="left" orientation="left" stroke="#2D6A4F" label={{ value: "Projets", angle: -90, position: "insideLeft", fontSize: 11 }} />
                  <YAxis yAxisId="right" orientation="right" stroke="#40916C" label={{ value: "M MAD", angle: 90, position: "insideRight", fontSize: 11 }} />
                  <Tooltip
                    formatter={(value, name) =>
                      name === "montant"
                        ? [`${Number(value).toLocaleString("fr-MA")} M MAD`, "Investissement"]
                        : [value, "Projets"]
                    }
                  />
                  <Bar yAxisId="left" dataKey="projets" fill="#74C69D" radius={[4, 4, 0, 0]} name="projets" />
                  <Bar yAxisId="right" dataKey="montant" fill="#2D6A4F" radius={[4, 4, 0, 0]} name="montant" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
