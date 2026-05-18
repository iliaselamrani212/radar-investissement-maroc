"use client";

import dynamic from "next/dynamic";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { fetchRegions, fetchProjects, formatMAD } from "@/lib/api";
import Header from "@/components/Header";
import Loading from "@/components/Loading";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MapPin } from "lucide-react";
import type { ProjectMarker, RegionCenter } from "@/components/MapComponent";

const MapComponent = dynamic(() => import("@/components/MapComponent"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[520px] items-center justify-center rounded-xl border bg-gray-50">
      <p className="text-sm text-gray-500">Chargement de la carte…</p>
    </div>
  ),
});

const SECTOR_COLORS: Record<string, string> = {
  Industrie: "#e63946",
  Énergie: "#f4a261",
  Agriculture: "#2a9d8f",
  Tourisme: "#457b9d",
  Tech: "#6a4c93",
  Immobilier: "#c77dff",
  Logistique: "#8d8d8d",
  Infrastructure: "#4361ee",
};

export default function MapPage() {
  const [sectorFilter, setSectorFilter] = useState("");
  const { data: regions, isLoading: l1 } = useQuery<RegionCenter[]>({
    queryKey: ["regions"],
    queryFn: fetchRegions,
  });

  const { data: projectsData, isLoading: l2 } = useQuery({
    queryKey: ["projects", { limit: 200 }],
    queryFn: () => fetchProjects({ limit: 200 }),
  });

  const allProjects: any[] = projectsData?.items ?? [];
  const sectors = useMemo(
    () => Array.from(new Set(allProjects.map((p) => p.secteur).filter(Boolean))).sort(),
    [allProjects]
  );

  if (l1 || l2) return <Loading />;

  const projectsWithCoords: ProjectMarker[] = allProjects
    .filter((p) => p.latitude && p.longitude)
    .map((p) => ({
      id: p.id,
      titre: p.titre,
      latitude: Number(p.latitude),
      longitude: Number(p.longitude),
      montant_mad: p.montant_mad,
      secteur: p.secteur,
      region: p.region,
      stade: p.stade,
      score_fiabilite: p.score_fiabilite,
    }));

  const regionCenters: RegionCenter[] = (regions ?? []).map((r: any) => ({
    nom: r.nom,
    latitude: Number(r.latitude),
    longitude: Number(r.longitude),
  }));

  const sectorCounts: Record<string, number> = {};
  for (const p of allProjects) {
    sectorCounts[p.secteur] = (sectorCounts[p.secteur] ?? 0) + 1;
  }
  const topSectors = Object.entries(sectorCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);

  return (
    <div className="flex flex-col h-full">
      <Header title="Carte des Projets" />
      <div className="p-8 space-y-6 overflow-y-auto">

        {/* KPI strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-5">
              <p className="text-2xl font-bold text-gray-900">{allProjects.length}</p>
              <p className="text-sm text-gray-500 mt-1">Projets total</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-5">
              <p className="text-2xl font-bold text-gray-900">{projectsWithCoords.length}</p>
              <p className="text-sm text-gray-500 mt-1">Géolocalisés</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-5">
              <p className="text-2xl font-bold text-gray-900">{regionCenters.length}</p>
              <p className="text-sm text-gray-500 mt-1">Régions</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-5">
              <p className="text-2xl font-bold text-gray-900">{topSectors.length}</p>
              <p className="text-sm text-gray-500 mt-1">Secteurs actifs</p>
            </CardContent>
          </Card>
        </div>

        {/* Map */}
        <Card>
          <CardHeader>
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <CardTitle className="flex items-center gap-2 text-lg">
                <MapPin className="h-5 w-5 text-primary" />
                Carte Interactive
              </CardTitle>
              <select
                className="h-9 rounded-md border bg-white px-3 text-sm"
                value={sectorFilter}
                onChange={(event) => setSectorFilter(event.target.value)}
              >
                <option value="">Tous les secteurs</option>
                {sectors.map((secteur) => (
                  <option key={secteur} value={secteur}>{secteur}</option>
                ))}
              </select>
            </div>
          </CardHeader>
          <CardContent className="p-0 overflow-hidden rounded-b-xl">
            {projectsWithCoords.length > 0 ? (
              <MapComponent
                projects={projectsWithCoords}
                regions={regionCenters}
                sectorFilter={sectorFilter}
              />
            ) : (
              <div className="flex h-64 items-center justify-center text-sm text-gray-500">
                Aucun projet géolocalisé disponible. Lancez le scraper ou la seed pour peupler la base.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Legend */}
        {topSectors.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Légende des secteurs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                {topSectors.map(([secteur, count]) => (
                  <div key={secteur} className="flex items-center gap-2">
                    <span
                      className="inline-block h-3 w-3 rounded-full"
                      style={{ background: SECTOR_COLORS[secteur] ?? "#2D6A4F" }}
                    />
                    <span className="text-sm text-gray-700">{secteur}</span>
                    <Badge variant="secondary" className="text-xs">{count}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Regions grid */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Régions Référencées</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {regionCenters.map((r) => (
                <div key={r.nom} className="rounded-lg border p-3 text-center hover:bg-gray-50 transition-colors">
                  <p className="font-medium text-sm">{r.nom}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {r.latitude.toFixed(2)}, {r.longitude.toFixed(2)}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Projects with coords list */}
        {projectsWithCoords.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Projets géolocalisés ({projectsWithCoords.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {projectsWithCoords.slice(0, 12).map((p) => (
                  <div key={p.id} className="rounded-lg border p-3 hover:shadow-sm transition-shadow">
                    <p className="font-medium text-sm text-gray-900 truncate">{p.titre}</p>
                    <p className="text-xs text-gray-500 mt-1">{p.secteur} · {p.region ?? "N/A"}</p>
                    <p className="text-xs font-semibold text-green-700 mt-1">{formatMAD(p.montant_mad)}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {p.latitude.toFixed(3)}, {p.longitude.toFixed(3)}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
