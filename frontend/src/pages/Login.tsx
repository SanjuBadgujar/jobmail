import { Mail } from "lucide-react";
import { useState } from "react";
import { useToast } from "../components/Toast";
import { api, errMsg } from "../services/api";

export default function Login() {
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const failed = new URLSearchParams(window.location.search).get("auth") === "failed";
  const connect = async () => {
    setBusy(true);
    try { window.location.href = (await api.post<{ url: string }>("/auth/google")).data.url; }
    catch (e) { toast("error", errMsg(e)); setBusy(false); }
  };
  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 p-4">
      <div className="card w-full max-w-md text-center">
        <span className="mx-auto grid h-12 w-12 place-items-center rounded-xl bg-gradient-to-br from-brand-600 to-violet-600 text-white"><Mail /></span>
        <h1 className="mt-4 text-2xl font-semibold text-slate-900">JobMail</h1>
        <p className="mt-2 text-sm text-slate-500">Send individual application emails from your own Gmail account. JobMail only asks for permission to send; it never sees your password.</p>
        {failed && <p className="mt-3 text-sm text-red-600">Google sign-in did not complete. Please try again.</p>}
        <button className="btn-primary mt-6 w-full" onClick={connect} disabled={busy}>{busy ? "Redirecting…" : "Connect Gmail"}</button>
      </div>
    </main>
  );
}
