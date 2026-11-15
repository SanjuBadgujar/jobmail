import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { FileText, History, LayoutDashboard, Mail, Menu, Send, Settings, Users, X } from "lucide-react";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/compose", label: "Compose Email", icon: FileText },
  { to: "/contacts", label: "Contacts", icon: Users },
  { to: "/campaigns", label: "Campaigns", icon: Send },
  { to: "/history", label: "Sending History", icon: History },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Layout() {
  const [open, setOpen] = useState(false);
  return (
    <div className="min-h-screen bg-slate-50 md:flex">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 md:hidden">
        <span className="font-semibold text-brand-700">JobMail</span>
        <button onClick={() => setOpen(!open)} aria-label="Toggle menu">{open ? <X /> : <Menu />}</button>
      </header>
      <aside className={`${open ? "block" : "hidden"} w-full shrink-0 border-r border-slate-200 bg-white md:block md:w-64`}>
        <div className="hidden items-center gap-2 px-6 py-5 md:flex">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-brand-600 to-violet-600 text-white"><Mail className="h-4 w-4" /></span>
          <span className="text-lg font-semibold text-slate-900">JobMail</span>
        </div>
        <nav className="space-y-1 p-3">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === "/"} onClick={() => setOpen(false)}
              className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${isActive ? "bg-indigo-50 text-brand-700" : "text-slate-600 hover:bg-slate-100"}`}>
              <Icon className="h-4 w-4" />{label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="min-w-0 flex-1 p-4 md:p-8"><Outlet /></main>
    </div>
  );
}
