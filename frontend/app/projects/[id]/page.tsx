"use client";

import React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  fetchProject,
  fetchLlmSimilarProjects,
  formatMAD,
  type Project,
} from "@/lib/api";
import Header from "@/components/Header";
import Loading from "@/components/Loading";
import ScoreBadge from "@/components/ScoreBadge";
import ProjectRagChat from "@/components/ProjectRagChat";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ArrowLeft,
  Building2,
  CalendarDays,
  Database,
  FileText,
  MapPin,
} from "lucide-react";

const EMOJI_RE =
  /[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{FE00}-\u{FE0F}\u{1F1E6}-\u{1F1FF}\u{2190}-\u{21FF}\u{2300}-\u{23FF}]/gu;

function stripEmoji(text: string) {
  return text
    .replace(EMOJI_RE, "")
    .replace(/SDG\s+Capital/gi, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function renderInline(text: string) {
  const parts = stripEmoji(text).split(/\*\*(.+?)\*\*/g);
  return parts.map((part, j) =>
    j % 2 === 1
      ? <strong key={j} className="font-semibold text-slate-900">{part}</strong>
      : part
  );
}

function normalizeFicheText(text: string) {
  return stripEmoji(text)
    .replace(/\r\n/g, "\n")
    .replace(/\s+(#{1,3}\s+)/g, "\n\n$1")
    .replace(/(##\s+R\S*sum\S*\s+ex\S*cutif)\s+/gi, "$1\n")
    .replace(/(##\s+Points\s+cl\S*s)\s+/gi, "$1\n")
    .replace(/(##\s+Analyse\s+contextuelle)\s+/gi, "$1\n")
    .replace(/(##\s+Sources\s*&\s*fiabilit\S*)\s+/gi, "$1\n")
    .replace(/\n?##\s+Sources\s*&\s*fiabilit\S*[\s\S]*$/i, "")
    .replace(/([^\n])\s+([-*•]\s+)/g, "$1\n$2")
    .replace(/•\s+/g, "- ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function renderFiche(text: string) {
  const lines = normalizeFicheText(text).split("\n");
  const elements: React.ReactNode[] = [];
  let listBuffer: string[] = [];
  const firstContentIndex = lines.findIndex((line) => Boolean(stripEmoji(line.trim())));

  const flushList = (key: string) => {
    if (listBuffer.length === 0) return;
    elements.push(
      <ul key={key} className="my-4 grid gap-2 rounded-lg border border-slate-200 bg-slate-50/80 p-4">
        {listBuffer.map((item, k) => (
          <li key={k} className="flex gap-3 text-sm leading-6 text-slate-700">
            <span className="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-600" />
            <span>{renderInline(item)}</span>
          </li>
        ))}
      </ul>
    );
    listBuffer = [];
  };

  lines.forEach((line, i) => {
    const trimmed = stripEmoji(line.trim());

    if (!trimmed) {
      flushList(`list-${i}`);
      elements.push(<div key={i} className="h-1" />);
      return;
    }

    // H1 : # Titre — titre principal du document
    if (/^# /.test(trimmed)) {
      flushList(`list-${i}`);
      elements.push(
        <h2 key={i} className="mb-5 text-2xl font-semibold leading-tight tracking-tight text-slate-950">
          {renderInline(trimmed.replace(/^#\s*/, ""))}
        </h2>
      );
      return;
    }

    // H2 : ## Section
    if (/^## /.test(trimmed)) {
      flushList(`list-${i}`);
      elements.push(
        <h3
          key={i}
          className="mt-8 flex items-center gap-2 border-b border-slate-200 pb-2 text-[13px] font-semibold uppercase tracking-wide text-slate-700"
        >
          <span className="h-2 w-2 rounded-full bg-emerald-600" />
          {renderInline(trimmed.replace(/^##\s*/, ""))}
        </h3>
      );
      return;
    }

    // H3 : ### Sous-section
    if (/^### /.test(trimmed)) {
      flushList(`list-${i}`);
      elements.push(
        <h4 key={i} className="mt-5 text-sm font-semibold text-slate-900">
          {renderInline(trimmed.replace(/^###\s*/, ""))}
        </h4>
      );
      return;
    }

    // Liste : - / * / • item
    if (/^[-*•]\s/.test(trimmed)) {
      listBuffer.push(trimmed.replace(/^[-*•]\s/, ""));
      return;
    }

    // Paragraphe
    flushList(`list-${i}`);
    if (i === firstContentIndex && trimmed.length <= 140) {
      elements.push(
        <h2 key={i} className="mb-5 text-2xl font-semibold leading-tight tracking-tight text-slate-950">
          {renderInline(trimmed)}
        </h2>
      );
      return;
    }

    elements.push(
      <p key={i} className="max-w-4xl text-[15px] leading-8 text-slate-600">
        {renderInline(trimmed)}
      </p>
    );
  });

  flushList("list-end");
  return elements;
}

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

  const similarQuery = useQuery({
    queryKey: ["project-similar", projectId],
    queryFn: () => fetchLlmSimilarProjects(projectId, 4),
    enabled: Boolean(projectId),
    retry: false,
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
  const scoreDetails = Object.fromEntries(
    Object.entries(project.score_details || {}).filter(([key]) => {
      const normalized = key.toLowerCase();
      return !normalized.includes("source") && normalized !== "poids";
    })
  );

  return (
    <div className="flex h-full flex-col">
      <Header title="Detail projet" />

      <div className="overflow-y-auto p-8">
        <div className="mb-6 flex items-center justify-between gap-4">
          <Button asChild variant="outline">
            <Link href="/projects">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Retour
            </Link>
          </Button>
          <div className="flex items-center gap-2">
            <Button asChild variant="outline">
              <a href={`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/projects/${projectId}/export/pdf`}>
                <FileText className="mr-2 h-4 w-4" />
                Export PDF
              </a>
            </Button>
            <ScoreBadge score={project.score_fiabilite} />
          </div>
        </div>

        <div>
          {/* ─── Contenu projet (pleine largeur) ─── */}
          <div className="min-w-0 space-y-6">
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
            <p className="text-sm leading-6 text-gray-600">
              {project.resume_ai || "Aucun resume disponible pour ce projet."}
            </p>
          </CardContent>
        </Card>

        {project.fiche_synthetique && (
          <Card className="overflow-hidden border-slate-200 bg-white">
            <CardHeader className="border-b border-slate-100 bg-slate-50/70 pb-4">
              <CardTitle className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
                <FileText className="h-4 w-4" />
                Fiche Synthétique
              </CardTitle>
            </CardHeader>
            <CardContent className="px-8 py-7">
              <div className="max-w-5xl">
                {renderFiche(stripEmoji(project.fiche_synthetique))}
              </div>
            </CardContent>
          </Card>
        )}

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

        {similarQuery.data?.items && similarQuery.data.items.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Projets similaires</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {similarQuery.data.items.map((sim: any) => {
                  const p = sim.projet ?? sim;
                  return (
                    <Link key={p.id} href={`/projects/${p.id}`} className="block rounded-lg border p-4 hover:shadow-sm hover:bg-gray-50 transition-all">
                      <p className="text-sm font-semibold text-gray-900 leading-snug">{p.titre}</p>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {p.secteur && <Badge variant="secondary">{p.secteur}</Badge>}
                        {p.region && <Badge variant="outline">{p.region}</Badge>}
                      </div>
                      <p className="mt-2 text-xs font-medium text-green-700">{formatMAD(p.montant_mad)}</p>
                      {sim.similarity !== undefined && (
                        <p className="mt-1 text-xs text-gray-400">Similarité: {Math.round(sim.similarity * 100)}%</p>
                      )}
                      {sim.raison && <p className="mt-1 text-xs italic text-gray-500">{sim.raison}</p>}
                    </Link>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}
          </div>

        </div>
      </div>

      {/* ─── Chat RAG : panneau flottant fixe, fermable ─── */}
      <ProjectRagChat projectId={projectId} />
    </div>
  );
}
