import type { LucideIcon } from "lucide-react";
import EmptyState from "../components/EmptyState";

export default function PlaceholderPage({ title, icon, description }: { title: string; icon: LucideIcon; description: string }) {
  return (
    <div className="mx-auto max-w-6xl">
      <h1 className="mb-6 text-2xl font-semibold text-slate-900">{title}</h1>
      <EmptyState icon={icon} title={`${title} is coming soon`} description={description} />
    </div>
  );
}
