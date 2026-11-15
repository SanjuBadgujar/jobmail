import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { ToastProvider } from "./components/Toast";
import { useAuth } from "./hooks/useAuth";
import Campaigns from "./pages/Campaigns";
import Compose from "./pages/Compose";
import Contacts from "./pages/Contacts";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import Login from "./pages/Login";
import Settings from "./pages/Settings";

function Gate() {
  const { status } = useAuth();
  if (!status) return <p className="p-8 text-slate-500">Loading…</p>;
  if (!status.authenticated) return <Login />;
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/compose" element={<Compose />} />
        <Route path="/contacts" element={<Contacts />} />
        <Route path="/campaigns" element={<Campaigns />} />
        <Route path="/history" element={<History />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return <ToastProvider><Gate /></ToastProvider>;
}
