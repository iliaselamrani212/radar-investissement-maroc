"use client";

import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  extractProjectWithLlm,
  fetchLlmProjects,
  fetchLlmStatus,
  fetchLlmWeeklyWatch,
  formatMAD,
  type LlmExtractionInput,
  type LlmProject,
} from "@/lib/api";
import Header from "@/components/Header";
import ScoreBadge from "@/components/ScoreBadge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  AlertCircle,
  BrainCircuit,
  CheckCircle2,
  FileText,
  Loader2,
  RefreshCw,
  Sparkles,
} from "lucide-react";

const initialForm: LlmExtractionInput = {
  title: "",
  content: "",
  source: "test",
  url: "",
};

const getErrorMessage = (error: unknown) => {
  if (error instanceof Error) return error.message;
  return "Erreur pendant l'appel IA";
};

function FieldValue({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase text-gray-400">{label}</p>
      <p className="mt-1 text-sm font-medium text-gray-900">{value || "N/A"}</p>
    </div>
  );
}

function ProjectPreview({ project }: { project: LlmProject }) {
  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase text-gray-400">Projet extrait</p>
          <h3 className="mt-1 text-lg font-semibold leading-snug text-gray-900">{project.titre}</h3>
        </div>
        <ScoreBadge score={project.score_fiabilite} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <FieldValue label="Montant" value={formatMAD(project.montant_mad)} />
        <FieldValue label="Secteur" value={project.secteur} />
        <FieldValue label="Region" value={project.region} />
        <FieldValue label="Porteur" value={project.porteur} />
        <FieldValue label="Stade" value={project.stade_avancement || project.stade} />
        <FieldValue
          label="Confiance LLM"
          value={
            project.llm?.score_confiance_extraction !== undefined &&
            project.llm?.score_confiance_extraction !== null
              ? `${Math.round(project.llm.score_confiance_extraction * 100)}%`
              : null
          }
        />
      </div>

      {Boolean(project.llm?.tags_esg?.length || project.llm?.strategies_nationales?.length) && (
        <div className="flex flex-wrap gap-2">
          {project.llm?.tags_esg?.map((tag) => (
            <Badge key={tag} variant="secondary">{tag}</Badge>
          ))}
          {project.llm?.strategies_nationales?.map((strategy) => (
            <Badge key={strategy} variant="outline">{strategy}</Badge>
          ))}
        </div>
      )}

      {project.fiche_synthetique && (
        <div className="rounded-lg border bg-gray-50 p-4">
          <p className="mb-3 text-sm font-semibold text-gray-800">Fiche synthetique</p>
          <div className="max-h-96 overflow-y-auto whitespace-pre-wrap text-sm leading-6 text-gray-700">
            {project.fiche_synthetique}
          </div>
        </div>
      )}
    </div>
  );
}

export default function AiPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<LlmExtractionInput>(initialForm);
  const [extractedProject, setExtractedProject] = useState<LlmProject | null>(null);

  const statusQuery = useQuery({
    queryKey: ["llm-status"],
    queryFn: fetchLlmStatus,
    retry: false,
  });

  const projectsQuery = useQuery({
    queryKey: ["llm-projects", { limit: 8 }],
    queryFn: () => fetchLlmProjects({ limit: 8 }),
    retry: false,
  });

  const weeklyQuery = useQuery({
    queryKey: ["llm-weekly-watch"],
    queryFn: fetchLlmWeeklyWatch,
    enabled: false,
    retry: false,
  });

  const extractMutation = useMutation({
    mutationFn: extractProjectWithLlm,
    onSuccess: (data) => {
      if (data.project) {
        setExtractedProject(data.project);
        queryClient.invalidateQueries({ queryKey: ["llm-projects"] });
      }
    },
  });

  const updateForm = (key: keyof LlmExtractionInput, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const submitExtraction = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setExtractedProject(null);
    extractMutation.mutate({
      ...form,
      title: form.title.trim(),
      content: form.content.trim(),
      source: form.source.trim() || "test",
      url: form.url?.trim() || undefined,
    });
  };

  const status = statusQuery.data;
  const statusMessage = statusQuery.isError
    ? "API backend indisponible"
    : status?.message || "Verification en cours";
  const canExtract = form.title.trim().length > 0 && form.content.trim().length >= 100;

  return (
    <div className="flex h-full flex-col">
      <Header title="IA locale" />

      <div className="space-y-6 overflow-y-auto p-8">
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <BrainCircuit className="h-5 w-5 text-primary" />
                Ollama
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-2 text-sm">
                <span className={`h-2.5 w-2.5 rounded-full ${status?.available ? "bg-green-500" : "bg-red-500"}`} />
                <span className="font-medium text-gray-900">
                  {status?.available ? "Disponible" : "Indisponible"}
                </span>
              </div>
              <p className="text-sm text-gray-500">{statusMessage}</p>
              <div className="text-xs text-gray-500">
                <p>Modele: {status?.model || "qwen2.5:7b"}</p>
                <p>URL: {status?.base_url || "http://localhost:11434"}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <FileText className="h-5 w-5 text-primary" />
                Base IA
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900">{projectsQuery.data?.total ?? 0}</div>
              <p className="mt-1 text-sm text-gray-500">projets structures par le pipeline</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Sparkles className="h-5 w-5 text-primary" />
                Veille
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Button
                variant="outline"
                className="w-full"
                disabled={weeklyQuery.isFetching}
                onClick={() => void weeklyQuery.refetch()}
              >
                {weeklyQuery.isFetching ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="mr-2 h-4 w-4" />
                )}
                Generer le rapport
              </Button>
              {weeklyQuery.isError && (
                <p className="mt-3 text-sm text-red-600">Rapport indisponible</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(420px,0.85fr)_1.15fr]">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Extraction LLM</CardTitle>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={submitExtraction}>
                <Input
                  value={form.title}
                  onChange={(event) => updateForm("title", event.target.value)}
                  placeholder="Titre du document"
                />
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  <Input
                    value={form.source}
                    onChange={(event) => updateForm("source", event.target.value)}
                    placeholder="Source"
                  />
                  <Input
                    value={form.url}
                    onChange={(event) => updateForm("url", event.target.value)}
                    placeholder="URL source"
                  />
                </div>
                <textarea
                  value={form.content}
                  onChange={(event) => updateForm("content", event.target.value)}
                  placeholder="Contenu officiel a analyser"
                  className="min-h-[260px] w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
                <Button className="w-full" type="submit" disabled={!canExtract || extractMutation.isPending}>
                  {extractMutation.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="mr-2 h-4 w-4" />
                  )}
                  Extraire avec le LLM
                </Button>
              </form>

              {extractMutation.data?.status === "rejected" && (
                <div className="mt-4 flex gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>{extractMutation.data.reason}</span>
                </div>
              )}

              {extractMutation.isError && (
                <div className="mt-4 flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>{getErrorMessage(extractMutation.error)}</span>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                {extractedProject ? (
                  <CheckCircle2 className="h-5 w-5 text-green-600" />
                ) : (
                  <BrainCircuit className="h-5 w-5 text-primary" />
                )}
                Resultat
              </CardTitle>
            </CardHeader>
            <CardContent>
              {extractedProject ? (
                <ProjectPreview project={extractedProject} />
              ) : (
                <div className="flex min-h-[360px] items-center justify-center rounded-lg border border-dashed text-sm text-gray-500">
                  En attente d'une extraction
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {weeklyQuery.data && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Rapport de veille</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-4 flex flex-wrap gap-3 text-sm text-gray-600">
                <Badge variant="secondary">{weeklyQuery.data.nb_projets_analyses} projets analyses</Badge>
                {weeklyQuery.data.chiffres_cles?.investissement_total_mds !== undefined && (
                  <Badge variant="outline">
                    {weeklyQuery.data.chiffres_cles.investissement_total_mds} Mds MAD
                  </Badge>
                )}
              </div>
              <div className="max-h-[520px] overflow-y-auto whitespace-pre-wrap rounded-lg border bg-gray-50 p-4 text-sm leading-6 text-gray-700">
                {weeklyQuery.data.rapport_markdown}
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Projets IA enregistres</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-hidden rounded-lg border">
              <table className="w-full text-left text-sm">
                <thead className="border-b bg-gray-50 text-gray-500">
                  <tr>
                    <th className="p-3 font-medium">Titre</th>
                    <th className="p-3 font-medium">Secteur</th>
                    <th className="p-3 font-medium">Region</th>
                    <th className="p-3 font-medium">Montant</th>
                    <th className="p-3 font-medium">Score</th>
                  </tr>
                </thead>
                <tbody>
                  {(projectsQuery.data?.items ?? []).map((project) => (
                    <tr key={project.id} className="border-b last:border-0">
                      <td className="max-w-md p-3 font-medium text-gray-900">{project.titre}</td>
                      <td className="p-3 text-gray-600">{project.secteur}</td>
                      <td className="p-3 text-gray-600">{project.region || "N/A"}</td>
                      <td className="p-3 text-gray-600">{formatMAD(project.montant_mad)}</td>
                      <td className="p-3"><ScoreBadge score={project.score_fiabilite} /></td>
                    </tr>
                  ))}
                  {!projectsQuery.data?.items?.length && (
                    <tr>
                      <td className="p-5 text-center text-gray-500" colSpan={5}>
                        Aucun projet IA enregistre
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
