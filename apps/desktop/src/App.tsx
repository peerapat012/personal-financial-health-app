import type { FormEvent } from "react";
import { useState } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Dumbbell,
  LayoutDashboard,
  LockKeyhole,
  Settings,
  Target,
  WalletCards,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  ApiError,
  apiRequest,
  clearApiToken,
  setApiToken,
} from "@/lib/api-client";
import "./App.css";

type Session = {
  authenticated: true;
  currency: "THB";
  timezone: "Asia/Bangkok";
};

type Section = {
  name: string;
  icon: LucideIcon;
};

const sections: Section[] = [
  { name: "Dashboard", icon: LayoutDashboard },
  { name: "Finance", icon: WalletCards },
  { name: "Health", icon: Dumbbell },
  { name: "Goals", icon: Target },
  { name: "Settings", icon: Settings },
];

function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [activeSection, setActiveSection] = useState("Dashboard");
  const [tokenInput, setTokenInput] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

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
      await apiRequest<Session>("/session");
      setTokenInput("");
      setAuthenticated(true);
    } catch (requestError) {
      clearApiToken();
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Unable to unlock app.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  function lock() {
    clearApiToken();
    setAuthenticated(false);
    setActiveSection("Dashboard");
  }

  if (!authenticated) {
    return (
      <main className="grid min-h-screen place-items-center p-6">
        <form
          className="grid w-full max-w-md gap-4 rounded-2xl bg-card p-8 text-card-foreground shadow-[0_18px_50px_rgb(31_50_42/0.10)]"
          onSubmit={unlock}
        >
          <p className="text-xs font-bold tracking-[0.12em] text-primary uppercase">
            Private desktop app
          </p>
          <div className="space-y-2">
            <h1 className="text-balance text-3xl font-semibold tracking-tight">
              Personal Financial Health
            </h1>
            <p className="text-pretty text-muted-foreground">
              Connect to your API with your personal token.
            </p>
          </div>
          <label className="mt-2 text-sm font-semibold" htmlFor="token">
            Personal API token
          </label>
          <input
            id="token"
            className="h-10 rounded-lg border bg-background px-3 text-sm shadow-xs focus-visible:ring-3 focus-visible:ring-ring/30 focus-visible:outline-none"
            type="password"
            value={tokenInput}
            onChange={(event) => setTokenInput(event.currentTarget.value)}
            autoComplete="off"
            autoFocus
          />
          {error && (
            <p className="text-sm text-destructive" aria-live="polite">
              {error}
            </p>
          )}
          <Button className="h-10" type="submit" disabled={submitting}>
            {submitting ? "Connecting…" : "Unlock"}
          </Button>
        </form>
      </main>
    );
  }

  return (
    <div className="grid min-h-screen grid-cols-[220px_1fr] max-sm:grid-cols-1">
      <aside className="flex flex-col gap-6 border-r border-sidebar-border bg-sidebar p-5 text-sidebar-foreground max-sm:border-r-0 max-sm:border-b">
        <div className="px-2">
          <p className="text-xs font-bold tracking-[0.12em] text-sidebar-primary uppercase">
            Personal
          </p>
          <h1 className="mt-1 text-lg font-semibold">Financial Health</h1>
        </div>
        <nav className="grid gap-1" aria-label="Main navigation">
          {sections.map(({ name, icon: Icon }) => (
            <Button
              key={name}
              className="h-10 justify-start gap-3 px-3"
              variant={name === activeSection ? "secondary" : "ghost"}
              onClick={() => setActiveSection(name)}
            >
              <Icon strokeWidth={2} />
              {name}
            </Button>
          ))}
        </nav>
        <Button
          className="mt-auto h-10 justify-start gap-3 px-3"
          variant="outline"
          onClick={lock}
        >
          <LockKeyhole strokeWidth={2} />
          Lock
        </Button>
      </aside>
      <main className="p-12 max-sm:p-6">
        <p className="text-xs font-bold tracking-[0.12em] text-primary uppercase">
          Phase 0 foundation
        </p>
        <h2 className="mt-2 text-balance text-3xl font-semibold tracking-tight">
          {activeSection}
        </h2>
        <p className="mt-3 text-pretty text-muted-foreground">
          Feature screen arrives in its roadmap phase.
        </p>
      </main>
    </div>
  );
}

export default App;
