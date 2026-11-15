import { useEffect, useState } from "react";
import ConfirmDialog from "../components/ConfirmDialog";
import { useToast } from "../components/Toast";
import { api, errMsg } from "../services/api";
import type { AuthStatus } from "../types";

export default function Settings() {
  const toast = useToast();
  const [auth, setAuth] = useState<AuthStatus | null>(null);
  const [delay, setDelay] = useState(10);
  const [ask, setAsk] = useState(false);
  useEffect(() => {
    api.get<AuthStatus>("/auth/status").then((r) => setAuth(r.data));
    api.get("/settings").then((r) => setDelay(r.data.sendDelaySeconds));
  }, []);
  const save = () => api.put("/settings", { sendDelaySeconds: delay }).then(() => toast("success", "Settings saved")).catch((e) => toast("error", errMsg(e, "Delay must be 5–600 seconds")));
  const disconnect = async () => { await api.post("/auth/disconnect"); window.location.href = "/"; };
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900">Settings</h1>
      <div className="card">
        <h2 className="font-medium">Gmail connection</h2>
        <p className="mt-1 text-sm text-slate-500">{auth?.gmailConnected ? `Connected as ${auth.email}` : "Not connected"}</p>
        {auth?.gmailConnected && <button className="btn-ghost mt-3" onClick={() => setAsk(true)}>Disconnect Gmail</button>}
      </div>
      <div className="card">
        <h2 className="font-medium">Delay between emails (seconds)</h2>
        <p className="mt-1 text-sm text-slate-500">Between 5 and 600. Gmail limits sending to about 500 emails per day; JobMail stops at 450.</p>
        <div className="mt-3 flex gap-3"><input type="number" min={5} max={600} className="input w-32" value={delay} onChange={(e) => setDelay(Number(e.target.value))} /><button className="btn-primary" onClick={save}>Save settings</button></div>
      </div>
      <ConfirmDialog open={ask} danger title="Disconnect Gmail?" message="JobMail will revoke its access and you will be signed out. Pending emails will not be sent." confirmLabel="Disconnect" onConfirm={disconnect} onCancel={() => setAsk(false)} />
    </div>
  );
}
