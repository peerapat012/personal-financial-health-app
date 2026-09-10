import { useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Pencil, Trash2 } from "lucide-react";

import { ConfirmationDialog, EmptyState, ErrorState, LoadingState } from "@/components/Feedback";
import { Button } from "@/components/ui/button";
import { healthApi } from "@/features/health/api/health.api";
import { healthKeys, useWeightLogs } from "@/features/health/hooks/useWeightLogs";
import { ApiError } from "@/lib/api-client";
import { formatDate, formatWeight, todayBangkok } from "@/lib/format";
import type { WeightLog } from "@/lib/api-types";

export function WeightLogPanel() {
  const client = useQueryClient();
  const [date, setDate] = useState(todayBangkok);
  const [weight, setWeight] = useState("");
  const [note, setNote] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [page, setPage] = useState(0);
  const [deleting, setDeleting] = useState<WeightLog | null>(null);
  const logs = useWeightLogs({ from, to, limit: 15, offset: page * 15 });
  const save = useMutation({
    mutationFn: () => healthApi.putWeightLog(date, { weight_kg: weight.trim() || null, note: note.trim() || null }),
    onSuccess: async () => {
      setWeight("");
      setNote("");
      await client.invalidateQueries({ queryKey: healthKeys.weights });
    },
  });
  const remove = useMutation({
    mutationFn: healthApi.deleteWeightLog,
    onSuccess: async () => {
      setDeleting(null);
      await client.invalidateQueries({ queryKey: healthKeys.weights });
    },
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    save.mutate();
  }

  function edit(log: WeightLog) {
    setDate(log.log_date);
    setWeight(log.weight_kg ?? "");
    setNote(log.note ?? "");
    save.reset();
  }

  return (
    <div className="health-content">
      <form className="finance-form" onSubmit={submit}>
        <p className="eyebrow">Daily check-in</p>
        <h3>Log weight</h3>
        <label>Date<input type="date" max={todayBangkok()} required value={date} onChange={(event) => setDate(event.target.value)} /></label>
        <label>Weight (kg)<input type="number" min="1" max="500" step="0.01" value={weight} onChange={(event) => setWeight(event.target.value)} /></label>
        <label>Note<textarea maxLength={2000} value={note} onChange={(event) => setNote(event.target.value)} placeholder="Optional" /></label>
        <p className="field-help">Add a weight, a note, or both. Saving the same date updates that day.</p>
        {save.error && <p className="form-error" role="alert">{save.error instanceof ApiError ? save.error.message : "Weight log could not be saved."} Your entry is still here.</p>}
        <Button type="submit" disabled={save.isPending || (!weight.trim() && !note.trim())}>{save.isPending ? "Saving…" : "Save day"}</Button>
      </form>

      <section className="finance-list">
        <div className="list-heading"><div><p className="eyebrow">Recorded days</p><h3>Weight history</h3></div><span>{logs.data?.total ?? 0} days</span></div>
        <div className="health-filters">
          <label>From<input type="date" value={from} onChange={(event) => { setPage(0); setFrom(event.target.value); }} /></label>
          <label>To<input type="date" min={from} value={to} onChange={(event) => { setPage(0); setTo(event.target.value); }} /></label>
        </div>
        {logs.isLoading ? <LoadingState label="Loading weight history…" /> : logs.error ? <ErrorState message="Weight history could not be loaded." onRetry={() => logs.refetch()} /> : !logs.data?.items.length ? (
          <EmptyState title="No weight logs yet" description="Record a weight or a short note to begin your history." />
        ) : (
          <div className="table-scroll"><table><thead><tr><th>Date</th><th>Weight</th><th>Note</th><th /></tr></thead><tbody>{logs.data.items.map((log) => <tr key={log.id}><td>{formatDate(log.log_date)}</td><td>{log.weight_kg ? formatWeight(log.weight_kg) : "—"}</td><td className="note-cell">{log.note || "—"}</td><td><div className="row-actions"><Button size="icon-sm" variant="ghost" aria-label="Edit weight log" onClick={() => edit(log)}><Pencil /></Button><Button size="icon-sm" variant="ghost" aria-label="Delete weight log" onClick={() => setDeleting(log)}><Trash2 /></Button></div></td></tr>)}</tbody></table></div>
        )}
        <div className="pagination"><Button variant="outline" disabled={!page} onClick={() => setPage((value) => value - 1)}>Previous</Button><span>Page {page + 1}</span><Button variant="outline" disabled={(page + 1) * 15 >= (logs.data?.total ?? 0)} onClick={() => setPage((value) => value + 1)}>Next</Button></div>
        {remove.error && <p className="form-error" role="alert">Delete failed. Nothing was removed.</p>}
      </section>

      <ConfirmationDialog open={Boolean(deleting)} title="Delete this weight log?" description="This removes the weight and note recorded for that day." confirmLabel={remove.isPending ? "Deleting…" : "Delete log"} onConfirm={() => deleting && remove.mutate(deleting.log_date)} onCancel={() => setDeleting(null)} />
    </div>
  );
}
