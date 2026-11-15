import { Trash2, Users } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import ConfirmDialog from "../components/ConfirmDialog";
import EmptyState from "../components/EmptyState";
import { useToast } from "../components/Toast";
import { api, errMsg } from "../services/api";
import type { Recipient } from "../types";

export default function Contacts() {
  const toast = useToast();
  const [rows, setRows] = useState<Recipient[]>([]);
  const [text, setText] = useState("");
  const [edit, setEdit] = useState<Recipient | null>(null);
  const [del, setDel] = useState<Recipient | null>(null);
  const load = useCallback(() => { api.get<Recipient[]>("/recipients").then((r) => setRows(r.data)); }, []);
  useEffect(load, [load]);
  const report = (d: { added: number; invalid: string[]; duplicates: string[] }) => {
    toast(d.added ? "success" : "error", `${d.added} added, ${d.invalid.length} invalid, ${d.duplicates.length} duplicates`);
    load();
  };
  const add = () => api.post("/recipients", { text }).then((r) => { report(r.data); setText(""); }).catch((e) => toast("error", errMsg(e)));
  const csv = (f?: File) => {
    if (!f) return;
    const fd = new FormData(); fd.append("file", f);
    api.post("/recipients/import-csv", fd).then((r) => report(r.data)).catch((e) => toast("error", errMsg(e)));
  };
  const saveEdit = () => edit && api.put(`/recipients/${edit.id}`, edit).then(() => { setEdit(null); load(); }).catch((e) => toast("error", errMsg(e)));
  const remove = () => del && api.delete(`/recipients/${del.id}`).then(() => { setDel(null); load(); });
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900">Contacts</h1>
      <div className="card space-y-3">
        <textarea className="input h-28" placeholder="Paste email addresses separated by commas, spaces or new lines" value={text} onChange={(e) => setText(e.target.value)} />
        <div className="flex flex-wrap items-center gap-3">
          <button className="btn-primary" disabled={!text.trim()} onClick={add}>Add recipients</button>
          <label className="btn-ghost cursor-pointer">Upload CSV<input type="file" accept=".csv" hidden onChange={(e) => { csv(e.target.files?.[0]); e.target.value = ""; }} /></label>
          <span className="text-xs text-slate-500">CSV columns: email, name, company, position</span>
        </div>
      </div>
      {rows.length === 0 ? <EmptyState icon={Users} title="No recipients yet" description="Paste addresses or upload a CSV to add recruiters." /> : (
        <div className="card overflow-x-auto p-0">
          <p className="px-5 pt-4 text-sm text-slate-500">{rows.length} recipients</p>
          <table className="mt-2 w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-slate-500"><tr><th className="px-5 py-2">Email</th><th>Name</th><th>Company</th><th>Position</th><th /></tr></thead>
            <tbody>{rows.map((r) => edit?.id === r.id ? (
              <tr key={r.id} className="border-b border-slate-100">
                <td className="px-5 py-2">{r.email}</td>
                {(["name", "company", "position"] as const).map((f) => <td key={f}><input className="input" value={edit[f] ?? ""} onChange={(e) => setEdit({ ...edit, [f]: e.target.value })} /></td>)}
                <td className="space-x-2 pr-5 text-right"><button className="text-brand-600" onClick={saveEdit}>Save</button><button className="text-slate-500" onClick={() => setEdit(null)}>Cancel</button></td>
              </tr>
            ) : (
              <tr key={r.id} className="border-b border-slate-100">
                <td className="px-5 py-2">{r.email}</td><td>{r.name}</td><td>{r.company}</td><td>{r.position}</td>
                <td className="space-x-3 pr-5 text-right"><button className="text-brand-600" onClick={() => setEdit(r)}>Edit</button><button aria-label="Delete" onClick={() => setDel(r)}><Trash2 className="inline h-4 w-4 text-slate-400" /></button></td>
              </tr>))}</tbody>
          </table>
        </div>)}
      <ConfirmDialog open={!!del} danger title="Delete recipient?" message={`${del?.email} will be removed, including its history.`} confirmLabel="Delete" onConfirm={remove} onCancel={() => setDel(null)} />
    </div>
  );
}
