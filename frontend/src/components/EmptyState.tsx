import type { LucideIcon } from "lucide-react";

export default function EmptyState({ icon: Icon, title, description }: { icon: LucideIcon; title: string; description: string }) {
  return (
    <div className="grid place-items-center rounded-xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
      <span className="grid h-12 w-12 place-items-center rounded-full bg-indigo-50 text-brand-600"><Icon className="h-6 w-6" /></span>
      <h3 className="mt-4 text-base font-semibold text-slate-900">{title}</h3>
      <p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>
    </div>
  );
}
