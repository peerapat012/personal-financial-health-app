import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import type { LucideIcon } from "lucide-react";
import {
  ArrowRight,
  CircleCheck,
  Dumbbell,
  LayoutDashboard,
  LockKeyhole,
  Settings,
  ShieldCheck,
  Target,
  WalletCards,
} from "lucide-react";

import { ConfirmationDialog, EmptyState } from "@/components/Feedback";
import { Button } from "@/components/ui/button";
import { FinancePage } from "@/features/finance/pages/FinancePage";
import type { SessionResponse } from "@/lib/api-types";
import {
  ApiError,
  apiRequest,
  clearApiToken,
  setApiToken,
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
  const [tokenInput, setTokenInput] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [confirmLock, setConfirmLock] = useState(false);

  useEffect(() => {
    const syncRoute = () => setActiveRoute(getRouteFromHash());
    window.addEventListener("hashchange", syncRoute);
    return () => window.removeEventListener("hashchange", syncRoute);
  }, []);

  async function unlock(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = tokenInput.trim();
    if (!value) {
      setError("Enter your personal API token.");
      return;
    }

    setSubmitting(true);
    setError("");
    setApiToken(value);
    try {
      const nextSession = await apiRequest<SessionResponse>("/session");
      setTokenInput("");
      setSession(nextSession);
      goTo("/dashboard", true);
    } catch (requestError) {
      clearApiToken();
      setError(
        requestError instanceof ApiError && requestError.status === 401
          ? "That token was not accepted. Check it and try again."
          : requestError instanceof ApiError
            ? requestError.message
            : "The API could not be reached. Try again when it is available.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  function lock() {
    clearApiToken();
    queryClient.clear();
    setSession(null);
    setConfirmLock(false);
    goTo("/dashboard", true);
  }

  if (!session) {
    return (
      <main className="session-page">
        <section className="session-intro" aria-labelledby="welcome-title">
          <div className="brand-mark" aria-hidden="true">PF</div>
          <p className="eyebrow">Private by design</p>
          <h1 id="welcome-title">Your money and health, in one quiet place.</h1>
          <p className="session-lede">
            This desktop app connects only to your private API. Your personal
            token stays in memory for this session and is cleared when you lock
            or close the app.
          </p>
          <div className="privacy-points">
            <p><ShieldCheck aria-hidden="true" /> No token is saved on this device</p>
            <p><CircleCheck aria-hidden="true" /> Your API validates access before data loads</p>
          </div>
        </section>

        <form className="session-card" onSubmit={unlock}>
          <p className="eyebrow">Connect your API</p>
          <h2>Unlock your dashboard</h2>
          <p className="text-muted-foreground">Paste the personal token you provisioned for this app.</p>
          <label htmlFor="token">Personal API token</label>
          <input
            id="token"
            name="token"
            type="password"
            value={tokenInput}
            onChange={(event) => {
              setTokenInput(event.currentTarget.value);
              if (error) setError("");
            }}
            autoComplete="off"
            autoFocus
            required
            aria-invalid={Boolean(error)}
            aria-describedby={error ? "token-error" : "token-help"}
          />
          <p id="token-help" className="field-help">The token is sent only to the configured API.</p>
          {error && <p id="token-error" className="form-error" role="alert">{error}</p>}
          <Button className="session-submit" type="submit" disabled={submitting}>
            {submitting ? "Checking connection…" : "Connect and continue"}
            {!submitting && <ArrowRight aria-hidden="true" />}
          </Button>
          <p className="connection-status" aria-live="polite">
            {submitting ? "Validating your token with the API…" : "Ready to connect"}
          </p>
        </form>
      </main>
    );
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
          <span className="api-pill"><i /> API connected</span>
        </header>
        <div className="route-body">
          {activeRoute.id === "finance" ? <FinancePage /> : <EmptyState
            icon={routeIcons[activeRoute.id]}
            title={`${activeRoute.label} is ready for its data`}
            description={activeRoute.description}
          />}
        </div>
      </main>

      <ConfirmationDialog
        open={confirmLock}
        title="Lock this session?"
        description="Your in-memory token will be cleared. You will need to enter it again to reconnect."
        confirmLabel="Lock session"
        onConfirm={lock}
        onCancel={() => setConfirmLock(false)}
      />
    </div>
  );
}

export default App;
