"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  fetchProjects,
  type Project,
} from "@/lib/api";
import Header from "@/components/Header";
import Loading from "@/components/Loading";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  FileText,
  ListChecks,
  RefreshCw,
} from "lucide-react";

type TrackingStatus = "stable" | "a_surveiller" | "bloque" | "avance";

interface FollowReport {
  id: string;
  projectId: string;
  date: string;
  status: TrackingStatus;
  title: string;
  content: string;
  nextAction: string;
  owner: string;
}

const STORAGE_KEY = "investigator43-follow-reports";

const STATUS_LABELS: Record<TrackingStatus, string> = {
  avance: "Avance",
  stable: "Stable",
  a_surveiller: "A surveiller",
  bloque: "Bloque",
};

const STATUS_STYLES: Record<TrackingStatus, string> = {
  avance: "bg-emerald-100 text-emerald-800 border-emerald-200",
  stable: "bg-blue-100 text-blue-800 border-blue-200",
  a_surveiller: "bg-amber-100 text-amber-800 border-amber-200",
  bloque: "bg-red-100 text-red-800 border-red-200",
};

const initialForm = {
  title: "",
  date: new Date().toISOString().slice(0, 10),
  status: "stable" as TrackingStatus,
  owner: "",
  content: "",
  nextAction: "",
};

function loadReports(): FollowReport[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveReports(reports: FollowReport[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(reports));
}

function firstSentence(text: string) {
  const cleaned = text.replace(/\s+/g, " ").trim();
  if (!cleaned) return "Aucun constat detaille n'a encore ete renseigne.";
  const match = cleaned.match(/^(.{1,220}?)([.!?]|$)/);
  return match?.[1]?.trim() || cleaned.slice(0, 220);
}

function generateSummary(project: Project | undefined, reports: FollowReport[]) {
  if (!project) return "Selectionnez un projet pour generer un resume de suivi.";
  if (reports.length === 0) {
    return `Le projet "${project.titre}" est place en suivi. Aucun rapport n'a encore ete ajoute; le prochain point doit qualifier l'avancement, les risques et les actions a mener.`;
  }

  const sorted = [...reports].sort((a, b) => b.date.localeCompare(a.date));
  const latest = sorted[0];
  const blockers = sorted.filter((r) => r.status === "bloque").length;
  const watch = sorted.filter((r) => r.status === "a_surveiller").length;
  const trend =
    latest.status === "avance"
      ? "la dynamique recente est positive"
      : latest.status === "bloque"
        ? "un blocage doit etre traite rapidement"
        : latest.status === "a_surveiller"
          ? "le projet demande une surveillance rapprochee"
          : "la situation reste stable";

  return `${project.titre} fait l'objet de ${reports.length} rapport(s) de suivi. Au dernier point du ${latest.date}, ${trend}. Constat principal: ${firstSentence(latest.content)}. ${blockers || watch ? `Points sensibles: ${blockers} blocage(s) et ${watch} sujet(s) a surveiller.` : "Aucun point critique majeur n'est ressorti des rapports."} Prochaine action: ${latest.nextAction || "planifier un nouveau point de suivi."}`;
}

export default function TrackingPage() {
  const [reports, setReports] = useState<FollowReport[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [form, setForm] = useState(initialForm);

  const { data, isLoading } = useQuery({
    queryKey: ["tracking-projects"],
    queryFn: () => fetchProjects({ limit: 200 }),
  });

  const projects: Project[] = data?.items || [];
  const trackedProjects = useMemo(() => {
    const preferred = projects.filter((project) => {
      const stage = `${project.stade || ""}`.toLowerCase();
      return stage.includes("construction") || stage.includes("operation") || stage.includes("real");
    });
    return preferred.length ? preferred : projects;
  }, [projects]);

  useEffect(() => {
    setReports(loadReports());
  }, []);

  useEffect(() => {
    if (!selectedProjectId && trackedProjects.length) {
      setSelectedProjectId(trackedProjects[0].id);
    }
  }, [selectedProjectId, trackedProjects]);

  const selectedProject = trackedProjects.find((project) => project.id === selectedProjectId);
  const selectedReports = reports
    .filter((report) => report.projectId === selectedProjectId)
    .sort((a, b) => b.date.localeCompare(a.date));
  const latestReport = selectedReports[0];
  const summary = generateSummary(selectedProject, selectedReports);

  const reportCounts = useMemo(() => {
    return reports.reduce<Record<string, number>>((acc, report) => {
      acc[report.projectId] = (acc[report.projectId] || 0) + 1;
      return acc;
    }, {});
  }, [reports]);

  const submitReport = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedProjectId || !form.content.trim()) return;

    const nextReports = [
      {
        id: crypto.randomUUID(),
        projectId: selectedProjectId,
        date: form.date,
        status: form.status,
        title: form.title.trim() || "Rapport de suivi",
        content: form.content.trim(),
        nextAction: form.nextAction.trim(),
        owner: form.owner.trim(),
      },
      ...reports,
    ];

    setReports(nextReports);
    saveReports(nextReports);
    setForm({ ...initialForm, date: new Date().toISOString().slice(0, 10) });
  };

  if (isLoading) return <Loading />;

  return (
    <div className="flex h-full flex-col">
      <Header
        title="Suivi des projets"
        subtitle="Rapports, avancement et resume de suivi"
      />

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-6 overflow-y-auto p-8 xl:grid-cols-[360px_minmax(0,1fr)]">
        <Card className="h-fit">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <ClipboardList className="h-5 w-5 text-primary" />
              Projets suivis
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {trackedProjects.map((project) => {
              const active = project.id === selectedProjectId;
              return (
                <button
                  key={project.id}
                  onClick={() => setSelectedProjectId(project.id)}
                  className={`w-full rounded-lg border p-4 text-left transition-colors ${
                    active
                      ? "border-primary bg-primary/5"
                      : "border-border bg-white hover:bg-secondary/40"
                  }`}
                >
                  <p className="line-clamp-2 text-sm font-semibold text-foreground">
                    {project.titre}
                  </p>
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    {project.secteur && <Badge variant="secondary">{project.secteur}</Badge>}
                    {project.region && <Badge variant="outline">{project.region}</Badge>}
                  </div>
                  <p className="mt-3 text-xs text-muted-foreground">
                    {reportCounts[project.id] || 0} rapport(s) de suivi
                  </p>
                </button>
              );
            })}
          </CardContent>
        </Card>

        <div className="min-w-0 space-y-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="p-5">
                <p className="text-xs font-medium uppercase text-muted-foreground">Projet</p>
                <p className="mt-2 text-2xl font-semibold text-foreground">
                  {trackedProjects.length}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-5">
                <p className="text-xs font-medium uppercase text-muted-foreground">Rapports</p>
                <p className="mt-2 text-2xl font-semibold text-foreground">{reports.length}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-5">
                <p className="text-xs font-medium uppercase text-muted-foreground">Dernier etat</p>
                <p className="mt-2 text-sm font-semibold text-foreground">
                  {latestReport ? STATUS_LABELS[latestReport.status] : "Non renseigne"}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-5">
                <p className="text-xs font-medium uppercase text-muted-foreground">Dernier point</p>
                <p className="mt-2 text-sm font-semibold text-foreground">
                  {latestReport?.date || "Aucun rapport"}
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader className="border-b border-border bg-secondary/30">
              <CardTitle className="flex items-center gap-2 text-base">
                <FileText className="h-5 w-5 text-primary" />
                Resume genere
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <p className="max-w-4xl text-sm leading-7 text-muted-foreground">{summary}</p>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[0.9fr_1.1fr]">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <RefreshCw className="h-5 w-5 text-primary" />
                  Nouveau rapport
                </CardTitle>
              </CardHeader>
              <CardContent>
                <form className="space-y-4" onSubmit={submitReport}>
                  <Input
                    value={form.title}
                    onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
                    placeholder="Titre du rapport"
                  />
                  <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                    <Input
                      type="date"
                      value={form.date}
                      onChange={(event) => setForm((prev) => ({ ...prev, date: event.target.value }))}
                    />
                    <select
                      value={form.status}
                      onChange={(event) =>
                        setForm((prev) => ({ ...prev, status: event.target.value as TrackingStatus }))
                      }
                      className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                    >
                      <option value="stable">Stable</option>
                      <option value="avance">Avance</option>
                      <option value="a_surveiller">A surveiller</option>
                      <option value="bloque">Bloque</option>
                    </select>
                  </div>
                  <Input
                    value={form.owner}
                    onChange={(event) => setForm((prev) => ({ ...prev, owner: event.target.value }))}
                    placeholder="Responsable du suivi"
                  />
                  <textarea
                    value={form.content}
                    onChange={(event) => setForm((prev) => ({ ...prev, content: event.target.value }))}
                    placeholder="Constats du rapport, avancement, risques, blocages..."
                    className="min-h-[170px] w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  />
                  <textarea
                    value={form.nextAction}
                    onChange={(event) => setForm((prev) => ({ ...prev, nextAction: event.target.value }))}
                    placeholder="Prochaine action de suivi"
                    className="min-h-[90px] w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  />
                  <Button className="w-full" type="submit" disabled={!selectedProjectId || !form.content.trim()}>
                    Ajouter le rapport
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <ListChecks className="h-5 w-5 text-primary" />
                  Historique des rapports
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {selectedReports.map((report) => (
                    <article key={report.id} className="rounded-lg border border-border p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold text-foreground">{report.title}</p>
                          <p className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
                            <CalendarDays className="h-3.5 w-3.5" />
                            {report.date}
                            {report.owner && ` - ${report.owner}`}
                          </p>
                        </div>
                        <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${STATUS_STYLES[report.status]}`}>
                          {STATUS_LABELS[report.status]}
                        </span>
                      </div>
                      <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-muted-foreground">
                        {report.content}
                      </p>
                      {report.nextAction && (
                        <div className="mt-4 rounded-md bg-secondary/50 p-3">
                          <p className="flex items-center gap-2 text-xs font-semibold uppercase text-muted-foreground">
                            {report.status === "bloque" ? (
                              <AlertTriangle className="h-4 w-4 text-red-500" />
                            ) : (
                              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                            )}
                            Prochaine action
                          </p>
                          <p className="mt-1 text-sm text-foreground">{report.nextAction}</p>
                        </div>
                      )}
                    </article>
                  ))}

                  {selectedReports.length === 0 && (
                    <div className="rounded-lg border border-dashed border-border p-8 text-center">
                      <FileText className="mx-auto h-7 w-7 text-muted-foreground/50" />
                      <p className="mt-3 text-sm text-muted-foreground">
                        Aucun rapport pour ce projet. Ajoutez un premier point de suivi pour generer un resume exploitable.
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
