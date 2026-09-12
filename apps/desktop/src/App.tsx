import { useEffect, useState } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Dumbbell,
  LayoutDashboard,
  LockKeyhole,
  Settings,
  Target,
  WalletCards,
} from "lucide-react";

import { ConfirmationDialog } from "@/components/Feedback";
import { UsernameSignIn } from "@/components/UsernameSignIn";
import { Button } from "@/components/ui/button";
import { FinancePage } from "@/features/finance/pages/FinancePage";
import { HealthPage } from "@/features/health/pages/HealthPage";
import { GoalsPage } from "@/features/goals/pages/GoalsPage";
import { DashboardPage } from "@/features/dashboard/pages/DashboardPage";
import { SettingsPage } from "@/features/settings/pages/SettingsPage";
import { isDark, readTheme } from "@/lib/theme";
import type { SessionResponse } from "@/lib/api-types";
import {
  apiRequest,
  clearApiToken,
} from "@/lib/api-client";
import { appRoutes, getRouteFromHash, type RouteId } from "@/routes/routes";
import { queryClient } from "@/lib/query-client";
import "./App.css";

const routeIcons: Record<RouteId, LucideIcon> = {
  dashboard: LayoutDashboard,
  finance: WalletCards,
  health: Dumbbell,
  goals: Target,
  settings: Settings,
};

function goTo(path: string, replace = false) {
  const hash = `#${path}`;
  if (replace) window.location.replace(hash);
  else window.location.hash = hash;
}

function App() {
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [activeRoute, setActiveRoute] = useState(getRouteFromHash);
  const [error, setError] = useState("");
  const [confirmLock, setConfirmLock] = useState(false);
  const [goalsDirty, setGoalsDirty] = useState(false);
  const [theme, setTheme] = useState(readTheme);
  useEffect(() => {
    const expired = () => {
      clearApiToken(); queryClient.clear(); setSession(null); setGoalsDirty(false);
      setError("Your session expired. Sign in again to continue.");
    };
    window.addEventListener("session-expired", expired);
    return () => window.removeEventListener("session-expired", expired);
  }, []);

  useEffect(() => {
    const system = window.matchMedia("(prefers-color-scheme: dark)");
    const apply = () => {
      const dark = isDark(theme, system.matches);
      document.documentElement.classList.toggle("dark", dark);
      document.documentElement.style.colorScheme = dark ? "dark" : "light";
    };
    apply();
    try { localStorage.setItem("theme", theme); } catch { /* Appearance still works when storage is unavailable. */ }
    system.addEventListener("change", apply);
    return () => system.removeEventListener("change", apply);
  }, [theme]);

  useEffect(() => {
    const syncRoute = () => {
      const next = getRouteFromHash();
      if (next.id !== activeRoute.id && goalsDirty && !window.confirm("Discard unsaved goal changes?")) {
        window.history.replaceState(null, "", `#${activeRoute.path}`);
        return;
      }
      setActiveRoute(next);
    };
    window.addEventListener("hashchange", syncRoute);
    return () => window.removeEventListener("hashchange", syncRoute);
  }, [activeRoute, goalsDirty]);

  function lock() {
    void apiRequest<void>("/auth/sign-out", { method: "POST", body: "{}" }).catch(() => {
      setError("Locked on this device. Server sign-out could not be confirmed; the remote session will expire automatically.");
    });
    setError("");
    setGoalsDirty(false);
    clearApiToken();
    queryClient.clear();
    setSession(null);
    setConfirmLock(false);
    goTo("/dashboard", true);
  }

  if (!session) {
    return <UsernameSignIn notice={error} onConnected={(next) => { setError(""); setSession(next); goTo("/dashboard", true); }} />;
  }

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark brand-mark-small" aria-hidden="true">PF</div>
          <div><p className="eyebrow">Personal</p><h1>Financial Health</h1></div>
        </div>
        <nav aria-label="Main navigation">
          {appRoutes.map((route) => {
            const Icon = routeIcons[route.id];
            const selected = route.id === activeRoute.id;
            return (
              <Button
                key={route.id}
                className="nav-button"
                variant={selected ? "secondary" : "ghost"}
                onClick={() => goTo(route.path)}
                aria-current={selected ? "page" : undefined}
              >
                <Icon strokeWidth={1.8} aria-hidden="true" />
                {route.label}
              </Button>
            );
          })}
        </nav>
        <div className="sidebar-foot">
          <p>{session.currency} · {session.timezone}</p>
          <Button variant="outline" onClick={() => setConfirmLock(true)}>
            <LockKeyhole aria-hidden="true" /> Lock session
          </Button>
        </div>
      </aside>

      <main className="route-page">
        <header className="route-header">
          <div><p className="eyebrow">{activeRoute.kicker}</p><h2>{activeRoute.label}</h2></div>
          <span className="api-pill"><i /> Session unlocked</span>
        </header>
        <div className="route-body">
          {activeRoute.id === "finance" ? <FinancePage /> : activeRoute.id === "health" ? <HealthPage /> : activeRoute.id === "goals" ? <GoalsPage onDirtyChange={setGoalsDirty} /> : activeRoute.id === "settings" ? <SettingsPage session={session} theme={theme} onThemeChange={setTheme} onLock={() => setConfirmLock(true)} /> : <DashboardPage />}
        </div>
      </main>

      <ConfirmationDialog
        open={confirmLock}
        title="Lock this session?"
        description={goalsDirty ? "Your unsaved goal changes will be discarded and your session cleared." : "Your in-memory session will be cleared. You will need to sign in again to reconnect."}
        confirmLabel="Lock session"
        onConfirm={lock}
        onCancel={() => setConfirmLock(false)}
      />
    </div>
  );
}

export default App;
