import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000",
});

const cleanParams = (params?: Record<string, any>) => {
  if (!params) return undefined;

  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => {
      return value !== "" && value !== null && value !== undefined;
    })
  );
};

// Interfaces
export interface Project {
  id: string;
  titre: string;
  resume_ai?: string | null;
  fiche_synthetique?: string | null;
  montant_mad?: number | null;
  secteur: string;
  region?: string | null;
  porteur?: string | null;
  stade?: string | null;
  date_annonce?: string | null;
  sources?: any[] | null;
  nb_sources_confirmees?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  score_fiabilite?: number | null;
  score_details?: {
    score_niveau_source?: number;
    score_triangulation?: number;
    score_precision_montant?: number;
    score_fraicheur?: number;
    score_llm?: number;
  } | null;
  created_at?: string | null;
}

export interface Stats {
  total_projects: number;
  total_amount_mad: number;
  average_score: number;
  by_sector: { secteur: string; count: number; total: number }[];
  by_region: { region: string; count: number; total: number }[];
  by_stade: { stade: string; count: number }[];
  timeline: { mois: string; count: number }[];
}

export interface ScoringConfig {
  id?: number;
  poids_source: number;
  poids_triangulation: number;
  poids_precision: number;
  poids_fraicheur: number;
  poids_llm: number;
  updated_at?: string;
}

export interface LlmStatus {
  base_url: string;
  model: string;
  timeout_seconds: number;
  available: boolean;
  model_available: boolean;
  models: string[];
  message: string;
}

export interface LlmProject extends Project {
  description?: string | null;
  fiche_synthetique?: string | null;
  stade_avancement?: string | null;
  updated_at?: string | null;
  llm?: {
    score_confiance_extraction?: number | null;
    sous_secteur?: string | null;
    type_projet?: string | null;
    nombre_emplois?: number | null;
    horizon_temporel_annees?: number | null;
    tags_esg?: string[];
    strategies_nationales?: string[];
    ville?: string | null;
    contexte_macro?: Record<string, any> | null;
    anomalies?: Record<string, any>[];
    source_principale?: string | null;
    url_source?: string | null;
  };
}

export interface LlmExtractionInput {
  title: string;
  content: string;
  source: string;
  url?: string;
  snippet?: string;
}

export interface LlmExtractionResponse {
  status: "ok" | "rejected";
  project?: LlmProject;
  reason?: string;
}

export interface LlmProjectsResponse {
  total: number;
  items: LlmProject[];
  limit: number;
  offset: number;
}

export interface LlmWeeklyWatch {
  nb_projets_analyses: number;
  chiffres_cles: Record<string, any>;
  rapport_markdown: string;
}

// API Calls
export const fetchProjects = (params?: Record<string, any>) =>
  api.get("/projects", { params: cleanParams(params) }).then((res) => res.data);

export const fetchProject = (id: string) =>
  api.get(`/projects/${id}`).then((res) => res.data);

export const fetchProjectSources = (id: string) =>
  api.get(`/projects/${id}/sources`).then((res) => res.data);

export const fetchStats = () => api.get("/stats").then((res) => res.data);

export const fetchRegions = () => api.get("/regions").then((res) => res.data);

export const fetchSectors = () => api.get("/sectors").then((res) => res.data);

export const fetchRecentAlerts = (params?: Record<string, any>) =>
  api.get("/alerts/recent", { params: cleanParams(params) }).then((res) => res.data);

export const fetchLlmStatus = () =>
  api.get("/llm/status", { timeout: 5000 }).then((res) => res.data as LlmStatus);

export const fetchLlmProjects = (params?: Record<string, any>) =>
  api.get("/llm/projects", { params: cleanParams(params) }).then((res) => res.data as LlmProjectsResponse);

export const fetchLlmProject = (id: string) =>
  api.get(`/llm/projects/${id}`).then((res) => res.data as LlmProject);

export const fetchLlmSimilarProjects = (id: string, topN = 5) =>
  api.get(`/llm/projects/${id}/similar`, { params: { top_n: topN } }).then((res) => res.data);

export const extractProjectWithLlm = (payload: LlmExtractionInput) =>
  api.post("/llm/extract", payload).then((res) => res.data as LlmExtractionResponse);

export const fetchLlmWeeklyWatch = () =>
  api.get("/llm/veille/hebdo").then((res) => res.data as LlmWeeklyWatch);

export const exportCsv = (params?: Record<string, any>) =>
  api.get("/export/csv", { params: cleanParams(params), responseType: "blob" }).then((res) => {
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "projets_investissement.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
  });

export const exportPdf = (params?: Record<string, any>) =>
  api.get("/export/pdf", { params: cleanParams(params), responseType: "blob" }).then((res) => {
    const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "projets_investissement.pdf");
    document.body.appendChild(link);
    link.click();
    link.remove();
  });

export const fetchScoringConfig = () =>
  api.get("/config/scoring").then((res) => res.data as ScoringConfig);

export const updateScoringConfig = (payload: ScoringConfig) =>
  api.put("/config/scoring", payload).then((res) => res.data);

export const recalculateScoring = () =>
  api.post("/config/scoring/recalculate").then((res) => res.data);

export const fetchVeilleSchedulerStatus = () =>
  api.get("/veille/scheduler/status").then((res) => res.data);

export const runVeilleNow = () =>
  api.post("/veille/run", null, { timeout: 120000 }).then((res) => res.data);

// ─── RAG ───────────────────────────────────────────────────────
export interface RagSource {
  n: number;
  titre?: string | null;
  source?: string | null;
  url?: string | null;
  doc_type?: string | null;
  score?: number | null;
  extrait?: string | null;
}

export interface RagAnswer {
  reponse: string;
  sources: RagSource[];
  contexte_trouve: boolean;
}

export interface RagStatus {
  ok: boolean;
  total_chunks: number;
  par_source: { source: string; nb: number }[];
}

export const fetchRagStatus = () =>
  api.get("/rag/status", { timeout: 8000 }).then((res) => res.data as RagStatus);

export const ingestRag = () =>
  api.post("/rag/ingest", null, { timeout: 600000 }).then((res) => res.data);

export const askProjectRag = (projectId: string, question: string, topK = 5) =>
  api
    .post(`/projects/${projectId}/ask`, { question, top_k: topK }, { timeout: 120000 })
    .then((res) => res.data as RagAnswer);

export const askGlobalRag = (question: string, topK = 5) =>
  api
    .post("/rag/ask", { question, top_k: topK }, { timeout: 120000 })
    .then((res) => res.data as RagAnswer);

// Helpers
export const formatMAD = (amount: number | null | undefined) => {
  if (!amount) return "N/A";
  return new Intl.NumberFormat("fr-MA", {
    style: "currency",
    currency: "MAD",
    maximumFractionDigits: 0,
  }).format(amount);
};

export const scoreColor = (score: number | null | undefined) => {
  if (score === null || score === undefined) return "bg-gray-200 text-gray-600";
  if (score >= 80) return "bg-green-100 text-green-800";
  if (score >= 60) return "bg-blue-100 text-blue-800";
  if (score >= 40) return "bg-yellow-100 text-yellow-800";
  return "bg-gray-100 text-gray-800";
};
