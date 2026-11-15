import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import ConfirmDialog from "../components/ConfirmDialog";
import { useToast } from "../components/Toast";
import { api, errMsg } from "../services/api";
import type { Recipient, ResumeInfo } from "../types";

const TEMPLATE = `Dear {{name}},

I hope you are doing well.

I am writing to express my interest in the {{position}} opportunity at {{company}}.

I have attached my resume for your consideration. I would appreciate the opportunity to discuss how my skills can contribute to your team.

Thank you for your time and consideration.

Best regards,
Your Name`;

export default function Compose() {
  const toast = useToast();
  const nav = useNavigate();
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState(TEMPLATE);
  const [recs, setRecs] = useState<Recipient[]>([]);
  const [sel, setSel] = useState<Set<number>>(new Set());
  const [resume, setResume] = useState<ResumeInfo | null>(null);
  const [delay, setDelay] = useState(10);
  const [idx, setIdx] = useState(0);
  const [prev, setPrev] = useState<{ to: string; subject: string; body: string } | null>(null);
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get<Recipient[]>("/recipients").then((r) => { setRecs(r.data); setSel(new Set(r.data.map((x) => x.id))); });
    api.get("/resume").then((r) => setResume(r.data));
    api.get("/settings").then((r) => setDelay(r.data.sendDelaySeconds));
    api.get("/emails/draft").then((r) => { if (r.data.subject || r.data.body) { setSubject(r.data.subject); setBody(r.data.body); } });
  }, []);

  const chosen = useMemo(() => recs.filter((r) => sel.has(r.id)), [recs, sel]);
  const cur = chosen[Math.min(idx, Math.max(chosen.length - 1, 0))];

  useEffect(() => {
    if (!cur) { setPrev(null); return; }
    const t = setTimeout(() => api.post("/emails/preview", { subject, body, recipient_id: cur.id }).then((r) => setPrev(r.data)).catch(() => setPrev(null)), 300);
    return () => clearTimeout(t);
  }, [subject, body, cur]);

  const toggle = (id: number) => setSel((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });
  const upload = (f?: File) => {
    if (!f) return;
    const fd = new FormData(); fd.append("file", f);
    api.post<ResumeInfo>("/resume/upload", fd).then((r) => setResume(r.data)).catch((e) => toast("error", errMsg(e)));
  };
  const removeResume = () => api.delete("/resume").then(() => setResume(null));
  const draft = () => api.post("/emails/draft", { subject, body }).then(() => toast("success", "Draft saved"));
  const review = () => {
    if (!subject.trim() || !body.trim()) return toast("error", "Subject and body are required");
    if (!chosen.length) return toast("error", "Select at least one recipient");
    if (!resume) return toast("error", "Upload your resume first");
    setConfirm(true);
  };
  const send = () => {
    setBusy(true);
    api.post("/emails/send", { subject, body, recipient_ids: chosen.map((r) => r.id) })
      .then(() => { toast("success", "Sending started"); nav("/campaigns"); })
      .catch((e) => { toast("error", errMsg(e)); setConfirm(false); }).finally(() => setBusy(false));
  };
  const mins = Math.ceil((chosen.length * delay) / 60);

  return (
    <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-2">
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold text-slate-900">Compose Email</h1>
        <input className="input" placeholder="Subject, e.g. Application for AI/ML Engineer" value={subject} onChange={(e) => setSubject(e.target.value)} />
        <textarea className="input h-80 font-mono" value={body} onChange={(e) => setBody(e.target.value)} />
        <p className="text-xs text-slate-500">{body.length} characters. Variables: {"{{name}} {{company}} {{position}}"}</p>
        <div className="card">
          <h2 className="text-sm font-medium">Resume</h2>
          {resume ? <p className="mt-2 text-sm">{resume.filename} ({(resume.fileSize / 1024).toFixed(0)} KB) <button className="ml-2 text-red-600" onClick={removeResume}>Remove</button></p> : <p className="mt-2 text-sm text-slate-500">PDF or DOCX, up to 5 MB.</p>}
          <label className="btn-ghost mt-3 inline-block cursor-pointer">{resume ? "Replace" : "Upload resume"}<input type="file" hidden accept=".pdf,.docx" onChange={(e) => { upload(e.target.files?.[0]); e.target.value = ""; }} /></label>
        </div>
        <div className="flex gap-3"><button className="btn-ghost" onClick={draft}>Save draft</button><button className="btn-primary" onClick={review}>Review and send</button></div>
      </div>
      <div className="space-y-4 lg:pt-11">
        <div className="card">
          <h2 className="text-sm font-medium">Recipients ({chosen.length} of {recs.length} selected)</h2>
          {recs.length === 0 ? <p className="mt-2 text-sm text-slate-500">Add recipients on the Contacts page first.</p> :
            <div className="mt-2 max-h-40 space-y-1 overflow-y-auto text-sm">{recs.map((r) => <label key={r.id} className="flex gap-2"><input type="checkbox" checked={sel.has(r.id)} onChange={() => toggle(r.id)} />{r.email}</label>)}</div>}
        </div>
        <div className="card">
          <div className="flex items-center justify-between"><h2 className="text-sm font-medium">Preview</h2>
            <div className="space-x-2 text-sm"><button className="btn-ghost !px-2 !py-1" disabled={idx <= 0} onClick={() => setIdx(idx - 1)}>Previous</button><span>{chosen.length ? Math.min(idx, chosen.length - 1) + 1 : 0}/{chosen.length}</span><button className="btn-ghost !px-2 !py-1" disabled={idx >= chosen.length - 1} onClick={() => setIdx(idx + 1)}>Next</button></div></div>
          {prev ? <div className="mt-3 text-sm"><p className="text-slate-500">To: {prev.to}</p><p className="font-medium">{prev.subject}</p><pre className="mt-2 whitespace-pre-wrap font-sans text-slate-700">{prev.body}</pre></div> : <p className="mt-3 text-sm text-slate-500">Select a recipient to preview the email.</p>}
        </div>
      </div>
      <ConfirmDialog open={confirm} title="Send these emails?" confirmLabel={busy ? "Starting…" : `Send ${chosen.length} emails`} onCancel={() => setConfirm(false)} onConfirm={send}
        message={`${chosen.length} separate emails will be sent from your connected Gmail account, one every ${delay} seconds (about ${mins} min). Subject: "${subject}". Attachment: ${resume?.filename}. This cannot be undone once sent.`} />
    </div>
  );
}
