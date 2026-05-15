"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { fetchProjects, fetchSectors, fetchRegions, formatMAD, exportCsv } from "@/lib/api";
import Header from "@/components/Header";
import ScoreBadge from "@/components/ScoreBadge";
import Loading from "@/components/Loading";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Link from "next/link";
import { Download, ChevronLeft, ChevronRight } from "lucide-react";

export default function ProjectsPage() {
  const [filters, setFilters] = useState({
    search: "",
    secteur: "",
    region: "",
    stade: "",
    score_min: "",
    montant_min: "",
    montant_max: "",
    sort_by: "score_fiabilite",
    limit: 20,
    offset: 0,
  });

  const { data: sectors } = useQuery({ queryKey: ["sectors"], queryFn: fetchSectors });
  const { data: regions } = useQuery({ queryKey: ["regions"], queryFn: fetchRegions });
  
  const { data, isLoading } = useQuery({
    queryKey: ["projects", filters],
    queryFn: () => fetchProjects(filters),
  });

  const updateFilter = (key: string, value: string | number) => {
    setFilters(prev => ({ ...prev, [key]: value, offset: 0 }));
  };

  if (isLoading) return <Loading />;

  return (
    <div className="flex flex-col h-full">
      <Header title="Projets d'Investissement" onSearch={(val) => updateFilter("search", val)} />
      <div className="p-8 space-y-6 overflow-y-auto">
        {/* Filtres */}
        <div className="bg-white p-4 rounded-xl shadow-sm border grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          <select className="border rounded-md p-2 text-sm" value={filters.secteur} onChange={e => updateFilter("secteur", e.target.value)}>
            <option value="">Tous les secteurs</option>
            {sectors?.map((s: string) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select className="border rounded-md p-2 text-sm" value={filters.region} onChange={e => updateFilter("region", e.target.value)}>
            <option value="">Toutes les régions</option>
            {regions?.map((r: any) => <option key={r.nom} value={r.nom}>{r.nom}</option>)}
          </select>
          <select className="border rounded-md p-2 text-sm" value={filters.stade} onChange={e => updateFilter("stade", e.target.value)}>
            <option value="">Tous les stades</option>
            <option value="annoncé">Annoncé</option>
            <option value="en cours">En cours</option>
            <option value="réalisé">Réalisé</option>
          </select>
          <Input placeholder="Score min" type="number" value={filters.score_min} onChange={e => updateFilter("score_min", e.target.value)} />
          <Input placeholder="Montant min" type="number" value={filters.montant_min} onChange={e => updateFilter("montant_min", e.target.value)} />
          <Input placeholder="Montant max" type="number" value={filters.montant_max} onChange={e => updateFilter("montant_max", e.target.value)} />
          <Button className="bg-primary hover:bg-primary/90" onClick={() => exportCsv(filters)}>
            <Download className="mr-2 h-4 w-4" /> Export CSV
          </Button>
        </div>

        {/* Tableau */}
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-50 border-b">
              <tr className="text-gray-500 text-sm">
                <th className="p-4 font-medium">Titre</th>
                <th className="p-4 font-medium">Secteur</th>
                <th className="p-4 font-medium">Région</th>
                <th className="p-4 font-medium">Montant</th>
                <th className="p-4 font-medium cursor-pointer" onClick={() => updateFilter("sort_by", "score_fiabilite")}>Score ↕</th>
                <th className="p-4 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data?.items?.map((p: any) => (
                <tr key={p.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="p-4 font-medium text-gray-900 max-w-xs truncate">{p.titre}</td>
                  <td className="p-4 text-gray-600">{p.secteur}</td>
                  <td className="p-4 text-gray-600">{p.region || "N/A"}</td>
                  <td className="p-4 text-gray-600">{formatMAD(p.montant_mad)}</td>
                  <td className="p-4"><ScoreBadge score={p.score_fiabilite} /></td>
                  <td className="p-4">
                    <Link href={`/projects/${p.id}`}>
                      <Button variant="outline" size="sm">Voir détails</Button>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex justify-between items-center">
          <p className="text-sm text-gray-500">{data?.total} projets trouvés</p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={filters.offset === 0} onClick={() => setFilters(prev => ({...prev, offset: prev.offset - prev.limit}))}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" disabled={data?.total <= filters.offset + filters.limit} onClick={() => setFilters(prev => ({...prev, offset: prev.offset + prev.limit}))}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}