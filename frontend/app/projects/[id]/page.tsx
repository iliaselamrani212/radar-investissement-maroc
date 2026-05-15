"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  fetchProject,
  fetchProjectSources,
  formatMAD,
  type Project,
} from "@/lib/api";
import Header from "@/components/Header";
import Loading from "@/components/Loading";
import ScoreBadge from "@/components/ScoreBadge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ArrowLeft,
  Building2,
  CalendarDays,
  Database,
  ExternalLink,
  MapPin,
} from "lucide-react";

function DetailItem({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase text-gray-400">{label}</p>
      <p className="mt-1 text-sm font-medium text-gray-900">{value || "N/A"}</p>
    </div>
  );
}

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;

  const projectQuery = useQuery<Project>({
    queryKey: ["project", projectId],
    queryFn: () => fetchProject(projectId),
  });

  const sourcesQuery = useQuery({
    queryKey: ["project-sources", projectId],
    queryFn: () => fetchProjectSources(projectId),
    enabled: Boolean(projectId),
  });

  if (projectQuery.isLoading) return <Loading />;

  if (projectQuery.isError || !projectQuery.data) {
    return (
      <div className="flex h-full flex-col">
        <Header title="Projet introuvable" />
        <div className="p-8">
          <Card>
            <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
              <Database className="h-10 w-10 text-gray-400" />
              <p className="text-sm text-gray-500">Impossible de charger ce projet.</p>
              <Button asChild variant="outline">
                <Link href="/projects">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Retour aux projets
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const project = projectQuery.data;
  const sources = sourcesQuery.data?.sources || project.sources || [];
  const scoreDetails = project.score_details || {};

  return (
    <div className="flex h-full flex-col">
      <Header title="Detail projet" />

      <div className="space-y-6 overflow-y-auto p-8">
        <div className="flex items-center justify-between gap-4">
          <Button asChild variant="outline">
            <Link href="/projects">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Retour
            </Link>
          </Button>
          <ScoreBadge score={project.score_fiabilite} />
        </div>

        <Card>
          <CardHeader>
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <CardTitle className="text-xl leading-tight">{project.titre}</CardTitle>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Badge>{project.secteur}</Badge>
                  {project.stade && <Badge variant="secondary">{project.stade}</Badge>}
                  {project.region && <Badge variant="outline">{project.region}</Badge>}
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="max-w-4xl text-sm leading-6 text-gray-600">
              {project.resume_ai || "Aucun resume disponible pour ce projet."}
            </p>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.15fr_0.85fr]">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Informations cles</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-5 md:grid-cols-2">
              <DetailItem label="Montant" value={formatMAD(project.montant_mad)} />
              <DetailItem label="Porteur" value={project.porteur} />
              <DetailItem label="Secteur" value={project.secteur} />
              <DetailItem label="Region" value={project.region} />
              <DetailItem label="Date annonce" value={project.date_annonce} />
              <DetailItem label="Sources confirmees" value={project.nb_sources_confirmees} />
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Building2 className="h-4 w-4 text-primary" />
                <span>{project.porteur || "Porteur non renseigne"}</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <MapPin className="h-4 w-4 text-primary" />
                <span>{project.latitude && project.longitude ? `${project.latitude}, ${project.longitude}` : "Coordonnees non renseignees"}</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <CalendarDays className="h-4 w-4 text-primary" />
                <span>{project.created_at || "Date inconnue"}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Score</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {Object.entries(scoreDetails).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between gap-3 rounded-lg border px-3 py-2">
                  <span className="text-sm text-gray-600">{key.replaceAll("_", " ")}</span>
                  <span className="text-sm font-semibold text-gray-900">{String(value)}</span>
                </div>
              ))}
              {Object.keys(scoreDetails).length === 0 && (
                <p className="text-sm text-gray-500">Aucun detail de score disponible.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Array.isArray(sources) && sources.length > 0 ? (
                sources.map((source: any, index: number) => (
                  <div key={`${source.url || source.name || index}`} className="flex items-center justify-between gap-4 rounded-lg border p-3">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{source.name || source.source || `Source ${index + 1}`}</p>
                      {source.niveau && <p className="text-xs text-gray-500">Niveau {source.niveau}</p>}
                    </div>
                    {source.url && (
                      <Button asChild size="sm" variant="outline">
                        <a href={source.url} target="_blank" rel="noreferrer">
                          <ExternalLink className="mr-2 h-4 w-4" />
                          Ouvrir
                        </a>
                      </Button>
                    )}
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500">Aucune source detaillee disponible.</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
