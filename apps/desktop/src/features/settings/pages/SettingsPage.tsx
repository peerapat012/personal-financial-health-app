import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { save } from "@tauri-apps/plugin-dialog";
import { writeTextFile } from "@tauri-apps/plugin-fs";
import { Download } from "lucide-react";

import { ConfirmationDialog } from "@/components/Feedback";
import { Button } from "@/components/ui/button";
import { apiRequest } from "@/lib/api-client";
import type { SessionResponse } from "@/lib/api-types";
import type { Theme } from "@/lib/theme";
import { version } from "../../../../package.json";

type Props = {
  session: SessionResponse;
  theme: Theme;
  onThemeChange: (theme: Theme) => void;
  onLock: () => void;
};

export function SettingsPage({ session, theme, onThemeChange, onLock }: Props) {
  const status = useQuery({ queryKey: ["session-status"], queryFn: () => apiRequest<SessionResponse>("/session"), staleTime: 0, refetchOnMount: "always", retry: false });
  const [confirmExport, setConfirmExport] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportStatus, setExportStatus] = useState("");

  async function exportData() {
    setConfirmExport(false);
    setExporting(true);
    setExportStatus("");
    try {
      const data = await apiRequest<unknown>("/export");
      const path = await save({ defaultPath: `personal-financial-health-${new Date().toISOString().slice(0, 10)}.json`, filters: [{ name: "JSON", extensions: ["json"] }] });
      if (path) {
        await writeTextFile(path, JSON.stringify(data, null, 2));
        setExportStatus("Export saved.");
      }
    } catch {
      setExportStatus("Export could not be saved. Your data was not changed.");
    } finally {
      setExporting(false);
    }
  }

  return <div className="grid max-w-3xl gap-6">
    <section className="grid gap-5 rounded-2xl border bg-card p-6"><h3 className="text-xl font-semibold">Display</h3><dl className="grid grid-cols-2 gap-3 text-sm"><dt className="text-muted-foreground">Currency</dt><dd>{session.currency}</dd><dt className="text-muted-foreground">Timezone</dt><dd>{session.timezone}</dd><dt className="text-muted-foreground">Weight</dt><dd>{session.units.weight}</dd><dt className="text-muted-foreground">Duration</dt><dd>Minutes</dd></dl><label className="grid max-w-xs gap-2 text-sm font-medium">Appearance<select className="rounded-lg border bg-background px-3 py-2" value={theme} onChange={(event) => onThemeChange(event.target.value as Theme)}><option value="system">Follow system</option><option value="light">Light</option><option value="dark">Dark</option></select></label><p className="text-xs text-muted-foreground">Only your appearance preference is saved on this device.</p></section>
    <section className="grid gap-4 rounded-2xl border bg-card p-6"><h3 className="text-xl font-semibold">Connection & session</h3><p role="status" className="text-sm">{status.isFetching ? "Checking API…" : status.error ? "API unavailable or session expired. Check the connection or sign in again." : "API reachable · session valid"}</p><div className="flex gap-3"><Button variant="outline" disabled={status.isFetching} onClick={() => status.refetch()}>Check connection</Button><Button onClick={onLock}>Lock session</Button></div></section>
    <section className="grid gap-4 rounded-2xl border bg-card p-6"><div><h3 className="text-xl font-semibold">Data export</h3><p className="mt-1 text-sm text-muted-foreground">Save a JSON snapshot of your finance and health records. Credentials and sessions are excluded.</p></div><div><Button variant="outline" disabled={exporting} onClick={() => setConfirmExport(true)}><Download />{exporting ? "Exporting…" : "Export JSON"}</Button></div>{exportStatus && <p role="status" className="text-sm">{exportStatus}</p>}</section>
    <p className="text-sm text-muted-foreground">Personal Financial Health · Version {version}</p>
    <ConfirmationDialog open={confirmExport} title="Export your personal data?" description="The file contains sensitive finance, health, and note data. Store it somewhere private." confirmLabel="Choose save location" destructive={false} onConfirm={exportData} onCancel={() => setConfirmExport(false)} />
  </div>;
}
