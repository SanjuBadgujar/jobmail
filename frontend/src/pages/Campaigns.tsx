import { Send } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import ConfirmDialog from "../components/ConfirmDialog";
import EmptyState from "../components/EmptyState";
import { useToast } from "../components/Toast";
import { api, errMsg } from "../services/api";
import type { QueueCampaign } from "../types";

export default function Campaigns() {
  const toast = useToast();
  const [c, setC] = useState<QueueCampaign | null>(null);
  const [ask, setAsk] = useState(false);
  const load = useCallback(() => { api.get("/queue/status").then((r) => setC(r.data.campaign)); }, []);
  useEffect(() => { load(); const t = setInterval(load, 2000); return () => clearInterval(t); }, [load]);
  const act = (a: string) => api.post(`/queue/${a}`, { campaign_id: c?.id }).then(load).catch((e) => toast("error", errMsg(e)));
  if (!c) return <div className="mx-auto max-w-6xl"><h1 className="mb-6 text-2xl font-semibold">Campaigns</h1><EmptyState icon={Send} title="No campaigns yet" description="Compose an email and send it to start a campaign." /></div>;
  const done = c.sent + c.failed + c.cancelled;
  const pct = c.total ? Math.round((done / c.total) * 100) : 0;
  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <h1 className="text-2xl font-semibold text-slate-900">Campaigns</h1>
      <div className="card">
        <div className="flex items-start justify-between"><div><p className="font-medium">{c.subject}</p><p className="text-sm capitalize text-slate-500">{c.status}</p></div>
          <div className="space-x-2">
            {c.status === "running" && <button className="btn-ghost" onClick={() => act("pause")}>Pause</button>}
            {c.status === "paused" && <button className="btn-primary" onClick={() => act("resume")}>Resume</button>}
            {["running", "paused"].includes(c.status) && <button className="btn-ghost" onClick={() => setAsk(true)}>Cancel pending</button>}
          </div></div>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full bg-brand-600 transition-all" style={{ width: `${pct}%` }} /></div>
        <p className="mt-2 text-sm text-slate-600">{c.sent} sent, {c.pending} pending, {c.failed} failed, {c.cancelled} cancelled of {c.total}</p>
        {c.note && <p className="mt-2 text-sm text-amber-700">{c.note}</p>}
      </div>
      <ConfirmDialog open={ask} danger title="Cancel pending emails?" message="Emails not yet sent will be cancelled. Already sent emails are not affected." confirmLabel="Cancel pending" onCancel={() => setAsk(false)} onConfirm={() => { setAsk(false); act("cancel"); }} />
    </div>
  );
}
