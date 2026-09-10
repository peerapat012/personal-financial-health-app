import { useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Pencil, Trash2 } from "lucide-react";

import { ConfirmationDialog, EmptyState, ErrorState, LoadingState } from "@/components/Feedback";
import { Button } from "@/components/ui/button";
import { healthApi } from "@/features/health/api/health.api";
import { healthKeys } from "@/features/health/hooks/useWeightLogs";
import { useWorkouts } from "@/features/health/hooks/useWorkouts";
import { ApiError } from "@/lib/api-client";
import { formatDate, formatDuration, todayBangkok } from "@/lib/format";
import type { ActivityType, Workout, WorkoutInput } from "@/lib/api-types";

function blank(): WorkoutInput {
  return { id: crypto.randomUUID(), occurred_on: todayBangkok(), activity_type: "walk", duration_minutes: 30, note: null };
}

export function WorkoutPanel() {
  const client = useQueryClient();
  const [form, setForm] = useState<WorkoutInput>(blank);
  const [editing, setEditing] = useState<Workout | null>(null);
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [activity, setActivity] = useState<ActivityType | "">("");
  const [page, setPage] = useState(0);
  const [deleting, setDeleting] = useState<Workout | null>(null);
  const workouts = useWorkouts({ from, to, activity_type: activity, limit: 15, offset: page * 15 });
  const save = useMutation({
    mutationFn: (data: WorkoutInput) => {
      if (!editing) return healthApi.createWorkout(data);
      const { id: _id, ...update } = data;
      return healthApi.updateWorkout(editing.id, update);
    },
    onSuccess: async () => {
      setEditing(null);
      setForm(blank());
      await client.invalidateQueries({ queryKey: healthKeys.workouts });
    },
  });
  const remove = useMutation({
    mutationFn: healthApi.deleteWorkout,
    onSuccess: async () => {
      setDeleting(null);
      await client.invalidateQueries({ queryKey: healthKeys.workouts });
    },
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    save.mutate({ ...form, note: form.note?.trim() || null });
  }

  function edit(workout: Workout) {
    setEditing(workout);
    setForm({ id: workout.id, occurred_on: workout.occurred_on, activity_type: workout.activity_type, duration_minutes: workout.duration_minutes, note: workout.note });
    save.reset();
  }

  function cancelEdit() {
    setEditing(null);
    setForm(blank());
    save.reset();
  }

  return (
    <div className="health-content">
      <form className="finance-form" onSubmit={submit}>
        <div className="form-heading"><div><p className="eyebrow">Movement</p><h3>{editing ? "Edit workout" : "Log workout"}</h3></div>{editing && <Button type="button" variant="ghost" onClick={cancelEdit}>Cancel</Button>}</div>
        <label>Date<input type="date" max={todayBangkok()} required value={form.occurred_on} onChange={(event) => setForm({ ...form, occurred_on: event.target.value })} /></label>
        <label>Activity<select value={form.activity_type} onChange={(event) => setForm({ ...form, activity_type: event.target.value as ActivityType })}><option value="walk">Walk</option><option value="run">Run</option><option value="cycle">Cycle</option><option value="strength">Strength</option><option value="other">Other</option></select></label>
        <label>Duration (minutes)<input type="number" min="1" max="1440" step="1" required value={form.duration_minutes} onChange={(event) => setForm({ ...form, duration_minutes: Number(event.target.value) })} /></label>
        <label>Note<textarea maxLength={2000} value={form.note ?? ""} onChange={(event) => setForm({ ...form, note: event.target.value })} placeholder="Optional" /></label>
        {save.error && <p className="form-error" role="alert">{save.error instanceof ApiError ? save.error.message : "Workout could not be saved."} Your entry is still here; retry uses the same ID.</p>}
        <Button type="submit" disabled={save.isPending}>{save.isPending ? "Saving…" : editing ? "Save workout" : "Add workout"}</Button>
      </form>

      <section className="finance-list">
        <div className="list-heading"><div><p className="eyebrow">Activity log</p><h3>Workouts</h3></div><span>{workouts.data?.total ?? 0} sessions</span></div>
        <div className="health-filters health-filters-workout">
          <label>From<input type="date" value={from} onChange={(event) => { setPage(0); setFrom(event.target.value); }} /></label>
          <label>To<input type="date" min={from} value={to} onChange={(event) => { setPage(0); setTo(event.target.value); }} /></label>
          <label>Activity<select value={activity} onChange={(event) => { setPage(0); setActivity(event.target.value as ActivityType | ""); }}><option value="">All activities</option><option value="walk">Walk</option><option value="run">Run</option><option value="cycle">Cycle</option><option value="strength">Strength</option><option value="other">Other</option></select></label>
        </div>
        {workouts.isLoading ? <LoadingState label="Loading workouts…" /> : workouts.error ? <ErrorState message="Workouts could not be loaded." onRetry={() => workouts.refetch()} /> : !workouts.data?.items.length ? (
          <EmptyState title="No workouts yet" description="Log a walk, run, ride, strength session, or other activity." />
        ) : (
          <div className="table-scroll"><table><thead><tr><th>Date</th><th>Activity</th><th>Duration</th><th>Note</th><th /></tr></thead><tbody>{workouts.data.items.map((workout) => <tr key={workout.id}><td>{formatDate(workout.occurred_on)}</td><td><span className="kind">{workout.activity_type}</span></td><td>{formatDuration(workout.duration_minutes)}</td><td className="note-cell">{workout.note || "—"}</td><td><div className="row-actions"><Button size="icon-sm" variant="ghost" aria-label="Edit workout" onClick={() => edit(workout)}><Pencil /></Button><Button size="icon-sm" variant="ghost" aria-label="Delete workout" onClick={() => setDeleting(workout)}><Trash2 /></Button></div></td></tr>)}</tbody></table></div>
        )}
        <div className="pagination"><Button variant="outline" disabled={!page} onClick={() => setPage((value) => value - 1)}>Previous</Button><span>Page {page + 1}</span><Button variant="outline" disabled={(page + 1) * 15 >= (workouts.data?.total ?? 0)} onClick={() => setPage((value) => value + 1)}>Next</Button></div>
        {remove.error && <p className="form-error" role="alert">Delete failed. Nothing was removed.</p>}
      </section>

      <ConfirmationDialog open={Boolean(deleting)} title="Delete this workout?" description="This permanently removes the activity from your history." confirmLabel={remove.isPending ? "Deleting…" : "Delete workout"} onConfirm={() => deleting && remove.mutate(deleting.id)} onCancel={() => setDeleting(null)} />
    </div>
  );
}
