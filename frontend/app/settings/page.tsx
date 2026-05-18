"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Header from "@/components/Header";
import Loading from "@/components/Loading";
import { Button } from "@/components/ui/button";
import {
  fetchScoringConfig,
  fetchVeilleSchedulerStatus,
  recalculateScoring,
  runVeilleNow,
  updateScoringConfig,
  type ScoringConfig,
} from "@/lib/api";
import { RefreshCcw, Save, ShieldCheck, TimerReset } from "lucide-react";

const LABELS: Record<keyof Omit<ScoringConfig, "id" | "updated_at">, string> = {
  poids_source: "Fiabilite institutionnelle",
  poids_triangulation: "Triangulation",
  poids_precision: "Precision des donnees",
  poids_fraicheur: "Fraicheur",
  poids_llm: "Confiance LLM",
};

const DEFAULT_CONFIG: ScoringConfig = {
  poids_source: 0.3,
  poids_triangulation: 0.3,
  poids_precision: 0.15,
  poids_fraicheur: 0.15,
  poids_llm: 0.1,
};

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const scoringQuery = useQuery({
    queryKey: ["scoring-config"],
    queryFn: fetchScoringConfig,
  });
  const schedulerQuery = useQuery({
    queryKey: ["veille-scheduler"],
    queryFn: fetchVeilleSchedulerStatus,
  });
  const [config, setConfig] = useState<ScoringConfig>(DEFAULT_CONFIG);

  useEffect(() => {
    if (scoringQuery.data) setConfig(scoringQuery.data);
  }, [scoringQuery.data]);

  const total = useMemo(
    () =>
      config.poids_source +
      config.poids_triangulation +
      config.poids_precision +
      config.poids_fraicheur +
      config.poids_llm,
    [config]
  );

  const saveMutation = useMutation({
    mutationFn: updateScoringConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scoring-config"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  const recalcMutation = useMutation({
    mutationFn: recalculateScoring,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  const veilleMutation = useMutation({
    mutationFn: runVeilleNow,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["veille-scheduler"] }),
  });

  const setWeight = (key: keyof typeof LABELS, value: number) => {
    setConfig((prev) => ({ ...prev, [key]: value / 100 }));
  };

  if (scoringQuery.isLoading || schedulerQuery.isLoading) return <Loading />;

  return (
    <div className="flex h-full flex-col">
      <Header title="Settings" subtitle="Scoring de fiabilite et veille automatique" />

      <div className="space-y-6 overflow-y-auto p-8">
        <section className="surface p-6">
          <div className="mb-5 flex items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Ponderations du scoring</h2>
              <p className="mt-1 text-sm text-slate-500">
                La somme doit rester egale a 100%. Le recalcul est applique a tous les projets.
              </p>
            </div>
            <div className={total === 1 ? "text-sm font-semibold text-emerald-700" : "text-sm font-semibold text-red-600"}>
              Total: {Math.round(total * 100)}%
            </div>
          </div>

          <div className="space-y-5">
            {(Object.keys(LABELS) as Array<keyof typeof LABELS>).map((key) => (
              <div key={key} className="grid gap-3 md:grid-cols-[220px_1fr_64px] md:items-center">
                <label className="text-sm font-medium text-slate-700">{LABELS[key]}</label>
                <input
                  className="h-2 w-full accent-emerald-700"
                  type="range"
                  min={0}
                  max={60}
                  step={5}
                  value={Math.round((config[key] ?? 0) * 100)}
                  onChange={(event) => setWeight(key, Number(event.target.value))}
                />
                <span className="text-right text-sm tabular-nums text-slate-600">
                  {Math.round((config[key] ?? 0) * 100)}%
                </span>
              </div>
            ))}
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Button
              disabled={Math.abs(total - 1) > 0.001 || saveMutation.isPending}
              onClick={() => saveMutation.mutate(config)}
            >
              <Save className="mr-2 h-4 w-4" />
              Sauvegarder et recalculer
            </Button>
            <Button
              variant="outline"
              disabled={recalcMutation.isPending}
              onClick={() => recalcMutation.mutate()}
            >
              <RefreshCcw className="mr-2 h-4 w-4" />
              Recalculer
            </Button>
          </div>
        </section>

        <section className="surface p-6">
          <div className="mb-5 flex items-center gap-3">
            <ShieldCheck className="h-5 w-5 text-emerald-700" />
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Veille automatique</h2>
              <p className="mt-1 text-sm text-slate-500">
                Scheduler backend actif avec execution periodique du rapport de veille.
              </p>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-lg border p-4">
              <p className="text-xs uppercase text-slate-400">Statut</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">
                {schedulerQuery.data?.enabled ? "Actif" : "Desactive"}
              </p>
            </div>
            <div className="rounded-lg border p-4">
              <p className="text-xs uppercase text-slate-400">Intervalle</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">
                {schedulerQuery.data?.interval_hours} h
              </p>
            </div>
            <div className="rounded-lg border p-4">
              <p className="text-xs uppercase text-slate-400">Derniere execution</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">
                {schedulerQuery.data?.last_run?.created_at ?? "Aucune"}
              </p>
            </div>
          </div>

          <Button
            className="mt-5"
            variant="outline"
            disabled={veilleMutation.isPending}
            onClick={() => veilleMutation.mutate()}
          >
            <TimerReset className="mr-2 h-4 w-4" />
            Lancer maintenant
          </Button>
        </section>
      </div>
    </div>
  );
}
