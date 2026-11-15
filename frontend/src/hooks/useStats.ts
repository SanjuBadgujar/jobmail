import { useEffect, useState } from "react";
import { getStats } from "../services/api";
import { emptyStats, type DashboardStats } from "../types";

// Reads /api/stats (added with the backend models in Phase 3).
// Until that endpoint exists the dashboard shows zeros, not fake numbers.
export function useStats() {
  const [stats, setStats] = useState<DashboardStats>(emptyStats);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    getStats().then((r) => setStats(r.data)).catch(() => setStats(emptyStats)).finally(() => setLoading(false));
  }, []);
  return { stats, loading };
}
