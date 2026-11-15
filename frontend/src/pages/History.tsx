import { History as HistoryIcon } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import EmptyState from "../components/EmptyState";
import { useToast } from "../components/Toast";
import { api, errMsg } from "../services/api";
import type { HistoryRow } from "../types";

const STATUSES = ["pending", "processing", "sent", "failed", "cancelled"];
const tone: Record<string, string> = { sent: "bg-emerald-50 text-emerald-700", failed: "bg-red-50 text-red-700", pending: "bg-amber-50 text-amber-700", processing: "bg-indigo-50 text-indigo-700", cancelled: "bg-slate-100 text-slate-600" };

export default function History() {
  const toast = useToast();
  const [rows, setRows] = useState<HistoryRow[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const size = 20;
  const params = { q: q || undefined, status: status || undefined };
  const load = useCallback(() => {
    api.get("/emails/history", { params: { ...params, page, page_size: size } }).then((r) => { setRows(r.data.items); setTotal(r.data.total); });
  }, [q, status, page]);
  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t); }, [load]);
  const retry = (id: number) => api.post(`/queue/retry/${id}`).then(() => { toast("success", "Queued for retry"); load(); }).catch((e) => toast("error", errMsg(e)));
  const exportUrl = `/api/emails/history/export.csv?${new URLSearchParams(Object.entries(params).filter(([, v]) => v) as [string, string][])}`;
  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3"><h1 className="text-2xl font-semibold text-slate-900">Sending History</h1><a className="btn-ghost" href={exportUrl}>Export CSV</a></div>
      <div className="flex gap-3">
        <input className="input max-w-xs" placeholder="Search recipient or subject" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} />
        <select className="input w-40" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}><option value="">All statuses</option>{STATUSES.map((s) => <option key={s}>{s}</option>)}</select>
      </div>
      {rows.length === 0 ? <EmptyState icon={HistoryIcon} title="No emails found" description="Sent, failed and pending emails will appear here." /> : (
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-slate-500"><tr><th className="px-5 py-2">Recipient</th><th>Subject</th><th>Date and time</th><th>Status</th><th>Error</th><th /></tr></thead>
            <tbody>{rows.map((r) => <tr key={r.id} className="border-b border-slate-100">
              <td className="px-5 py-2">{r.recipient}</td><td className="max-w-xs truncate">{r.subject}</td><td>{new Date(r.time).toLocaleString()}</td>
              <td><span className={`rounded-full px-2 py-0.5 text-xs ${tone[r.status]}`}>{r.status}</span></td><td className="max-w-xs truncate text-red-600">{r.error}</td>
              <td className="pr-5 text-right">{["failed", "cancelled"].includes(r.status) && <button className="text-brand-600" onClick={() => retry(r.id)}>Retry</button>}</td></tr>)}</tbody>
          </table>
        </div>)}
      <div className="flex items-center justify-between text-sm text-slate-500"><span>{total} emails</span>
        <div className="space-x-2"><button className="btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button><button className="btn-ghost" disabled={page * size >= total} onClick={() => setPage(page + 1)}>Next</button></div></div>
    </div>
  );
}
