import { AlertCircle, CheckCircle2, Clock, Mail, Users } from "lucide-react";
import StatCard from "../components/StatCard";
import { useStats } from "../hooks/useStats";

export default function Dashboard() {
  const { stats, loading } = useStats();
  const v = (n: number) => (loading ? "…" : n);
  return (
    <div className="mx-auto max-w-6xl">
      <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
      <p className="mt-1 text-sm text-slate-500">Your application emails at a glance.</p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard icon={Users} label="Total recipients" value={v(stats.totalRecipients)} />
        <StatCard icon={CheckCircle2} label="Emails sent" value={v(stats.sent)} tone="emerald" />
        <StatCard icon={Clock} label="Emails pending" value={v(stats.pending)} tone="amber" />
        <StatCard icon={AlertCircle} label="Failed emails" value={v(stats.failed)} tone="red" />
        <StatCard icon={Mail} label="Gmail connection" value={stats.gmailConnected ? "Connected" : "Not connected"} tone="violet" />
      </div>
    </div>
  );
}
