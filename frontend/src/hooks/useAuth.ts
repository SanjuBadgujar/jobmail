import { useCallback, useEffect, useState } from "react";
import { api } from "../services/api";
import type { AuthStatus } from "../types";

export function useAuth() {
  const [status, setStatus] = useState<AuthStatus | null>(null);
  const refresh = useCallback(() => {
    api.get<AuthStatus>("/auth/status").then((r) => setStatus(r.data))
      .catch(() => setStatus({ authenticated: false, gmailConnected: false, email: null }));
  }, []);
  useEffect(refresh, [refresh]);
  return { status, refresh };
}
