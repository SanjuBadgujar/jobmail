import axios from "axios";
import type { DashboardStats } from "../types";

export const api = axios.create({ baseURL: "/api", withCredentials: true });
export const getHealth = () => api.get<{ status: string; database: string }>("/health");
export const getStats = () => api.get<DashboardStats>("/stats");
export const errMsg = (e: unknown, fallback = "Something went wrong") =>
  (axios.isAxiosError(e) && (typeof e.response?.data?.detail === "string" ? e.response.data.detail : null)) || fallback;
