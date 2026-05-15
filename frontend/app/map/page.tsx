"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchRegions, fetchProjects, formatMAD } from "@/lib/api";
import Header from "@/components/Header";
import Loading from "@/components/Loading";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MapPin } from "lucide-react";

export default function MapPage() {
  const { data: regions, isLoading: l1 } = useQuery({ queryKey: ["regions"], queryFn: fetchRegions });
  const { data: projectsData, isLoading: l2 } = useQuery({ 
    queryKey: ["projects", { limit: 100 }], 
    queryFn: () => fetchProjects({ limit: 100 }) 
  });

  if (l1 || l2) return <Loading />;

  const projectsWithCoords = projectsData?.items?.filter((p: any) => p.latitude && p.longitude) || [];

  return (
    <div className="flex flex-col h-full">
      <Header title="Carte des Projets" />
      <div className="p-8 space-y-6 overflow-y-auto">
        <div className="bg-white p-6 rounded-xl shadow-sm border">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">Préparation pour Leaflet</h3>
          <p className="text-gray-500 mb-6">
            L'intégration de Leaflet est en attente. Voici les projets et régions disposant de coordonnées GPS prêts à être affichés.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projectsWithCoords.map((p: any) => (
              <Card key={p.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-primary" />
                    {p.region || "Localisation"}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm font-medium text-gray-800 truncate">{p.titre}</p>
                  <p className="text-xs text-gray-500 mt-1">{formatMAD(p.montant_mad)}</p>
                  <div className="mt-2 text-xs text-gray-400">
                    Lat: {parseFloat(p.latitude).toFixed(2)} | Lng: {parseFloat(p.longitude).toFixed(2)}
                  </div>
                </CardContent>
              </Card>
            ))}
            
            {projectsWithCoords.length === 0 && (
              <p className="text-gray-500 col-span-3">Aucun projet avec des coordonnées valides trouvé.</p>
            )}
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">Régions Référencées</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {regions?.map((r: any) => (
              <div key={r.nom} className="border rounded-lg p-3 text-center">
                <p className="font-medium text-sm">{r.nom}</p>
                <p className="text-xs text-gray-400 mt-1">{parseFloat(r.latitude).toFixed(2)}, {parseFloat(r.longitude).toFixed(2)}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}