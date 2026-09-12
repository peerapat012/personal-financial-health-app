import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { ApiError, apiRequest, clearApiToken, setApiToken } from "@/lib/api-client";
import type { SessionResponse } from "@/lib/api-types";

export function UsernameSignIn({ onConnected, notice }: { onConnected: (session: SessionResponse) => void; notice: string }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault(); setPending(true); setError("");
    try {
      const result = await apiRequest<{ token: string }>("/auth/sign-in", { method: "POST", body: JSON.stringify({ username: username.trim(), password }), credentials: "omit" });
      if (!result || typeof result.token !== "string" || !result.token) throw new Error("Invalid sign-in response");
      setApiToken(result.token);
      const session = await apiRequest<SessionResponse>("/session");
      setPassword("");
      onConnected(session);
    } catch (failure) {
      clearApiToken();
      setError(failure instanceof ApiError && failure.status === 401 ? "Username or password was not accepted." : failure instanceof ApiError ? failure.message : "Sign-in could not be completed. Try again.");
    } finally { setPending(false); }
  }

  return <main className="session-page">
    <section className="session-intro"><div className="brand-mark" aria-hidden="true">PF</div><p className="eyebrow">Private by design</p><h1>Your money and health, in one quiet place.</h1><p className="session-lede">Sign in to your private account. This app keeps your session in memory and clears it when you lock or close the app.</p></section>
    <form className="session-card" onSubmit={submit}><p className="eyebrow">Welcome back</p><h2>Sign in</h2><p className="text-sm text-muted-foreground">Use the username and password provisioned for your account.</p><label htmlFor="username">Username</label><input id="username" required minLength={3} maxLength={30} pattern="[a-zA-Z0-9_.]+" autoComplete="username" value={username} disabled={pending} onChange={(event) => setUsername(event.target.value)} /><label htmlFor="password">Password</label><input id="password" type="password" required maxLength={128} autoComplete="current-password" value={password} disabled={pending} onChange={(event) => setPassword(event.target.value)} />{(error || notice) && <p className="form-error" role="alert">{error || notice}</p>}<Button className="session-submit" type="submit" disabled={pending}>{pending ? "Signing in…" : "Sign in"}</Button><p className="field-help">Your password and session are not saved by this app.</p></form>
  </main>;
}
