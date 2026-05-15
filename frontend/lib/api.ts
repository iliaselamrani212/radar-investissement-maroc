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
