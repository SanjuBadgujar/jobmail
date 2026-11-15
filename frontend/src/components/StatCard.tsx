import type { LucideIcon } from "lucide-react";

export default function StatCard({ icon: Icon, label, value, tone = "indigo" }: { icon: LucideIcon; label: string; value: string | number; tone?: "indigo" | "violet" | "amber" | "red" | "emerald" }) {
  const tones = { indigo: "bg-indigo-50 text-indigo-600", violet: "bg-violet-50 text-violet-600", amber: "bg-amber-50 text-amber-600", red: "bg-red-50 text-red-600", emerald: "bg-emerald-50 text-emerald-600" };
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <span className={`grid h-9 w-9 place-items-center rounded-lg ${tones[tone]}`}><Icon className="h-5 w-5" /></span>
      <p className="mt-4 text-2xl font-semibold text-slate-900">{value}</p>
      <p className="text-sm text-slate-500">{label}</p>
    </div>
  );
}
