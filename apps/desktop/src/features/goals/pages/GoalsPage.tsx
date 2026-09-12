import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ConfirmationDialog, EmptyState, ErrorState, LoadingState, UnsavedFormFeedback } from "@/components/Feedback";
import { Button } from "@/components/ui/button";
import { goalsApi } from "@/features/goals/api/goals.api";
import { useGoals } from "@/features/goals/hooks/useGoals";
import { ApiError } from "@/lib/api-client";
import type { Goal, GoalKind } from "@/lib/api-types";
import { formatDate, formatThb, formatWeight, todayBangkok } from "@/lib/format";

function blank(): { id: string; name: string; account_id: string; baseline: string; target: string; start_date: string; due_date: string } {
  return { id: crypto.randomUUID(), name: "", account_id: "", baseline: "", target: "", start_date: todayBangkok(), due_date: "" };
}

export function GoalsPage({ onDirtyChange }: { onDirtyChange: (dirty: boolean) => void }) {
  const client = useQueryClient();
  const [kind, setKind] = useState<GoalKind>("financial");
  const [form, setForm] = useState(blank);
  const [dirty, setDirty] = useState(false);
  const [editing, setEditing] = useState<Goal | null>(null);
  const [includeArchived, setIncludeArchived] = useState(false);
  const [page, setPage] = useState(0);
  const [deleting, setDeleting] = useState<Goal | null>(null);
  const [discard, setDiscard] = useState<(() => void) | null>(null);
  const [uncertain, setUncertain] = useState(false);
  const goals = useGoals(kind, includeArchived, page);
  const accounts = useQuery({ queryKey: ["finance", "accounts", "goal-options"], queryFn: goalsApi.accounts, enabled: kind === "financial" });
  const refresh = () => client.invalidateQueries({ queryKey: ["goals"] });

  useEffect(() => { onDirtyChange(dirty); }, [dirty, onDirtyChange]);
  useEffect(() => () => onDirtyChange(false), [onDirtyChange]);
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => { if (dirty) { event.preventDefault(); event.returnValue = ""; } };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  function reset() {
    setEditing(null); setForm(blank()); setDirty(false); setUncertain(false);
  }

  const save = useMutation({
    mutationFn: async () => {
      const metadata = { name: form.name.trim(), due_date: form.due_date || null };
      if (editing) return goalsApi.update(kind, editing.id, metadata);
      const common = { ...metadata, id: form.id, start_date: form.start_date };
      return goalsApi.create(kind, kind === "financial"
        ? { ...common, account_id: form.account_id, baseline_amount: form.baseline, target_amount: form.target }
        : { ...common, baseline_weight_kg: form.baseline, target_weight_kg: form.target }, uncertain);
    },
    onSuccess: async () => { reset(); await refresh(); },
    onError: (error) => { if (error instanceof ApiError && (error.status === 0 || error.status >= 500)) setUncertain(true); },
  });
  const archive = useMutation({
    mutationFn: (goal: Goal) => goalsApi.update(kind, goal.id, { archived: !goal.archived_at }),
    onSuccess: refresh,
  });
  const remove = useMutation({
    mutationFn: (goal: Goal) => goalsApi.remove(kind, goal.id),
    onSuccess: async (_, goal) => {
      setDeleting(null);
      if (editing?.id === goal.id) { reset(); save.reset(); }
      await refresh();
    },
  });
  const busy = save.isPending || archive.isPending || remove.isPending;
  const fields = save.error instanceof ApiError ? save.error.fields : undefined;

  function change(field: keyof typeof form, value: string) {
    setForm({ ...form, [field]: value }); setDirty(true); save.reset();
  }
  function leave(action: () => void) {
    if (dirty) setDiscard(() => action);
    else action();
  }
  function edit(goal: Goal) {
    leave(() => {
      setEditing(goal); setDirty(false); setUncertain(false); save.reset();
      setForm({ id: goal.id, name: goal.name, start_date: goal.start_date, due_date: goal.due_date ?? "",
        account_id: "account_id" in goal ? goal.account_id : "",
        baseline: "baseline_amount" in goal ? goal.baseline_amount : goal.baseline_weight_kg,
        target: "target_amount" in goal ? goal.target_amount : goal.target_weight_kg });
    });
  }
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    save.mutate();
  }
  const fieldError = (field: string) => fields?.[field] && <span className="form-error" role="alert">{fields[field]}</span>;

  return <>
    <div className="finance-tabs" aria-label="Goal sections">
      {(["financial", "health"] as const).map((tab) => <Button key={tab} aria-pressed={kind === tab} disabled={busy} variant={kind === tab ? "secondary" : "ghost"} onClick={() => {
        if (tab !== kind) leave(() => { reset(); save.reset(); archive.reset(); remove.reset(); setKind(tab); setPage(0); });
      }}>{tab === "financial" ? "Financial goals" : "Weight goals"}</Button>)}
    </div>
    <div className="grid items-start gap-8 xl:grid-cols-[minmax(17rem,21rem)_minmax(0,1fr)]">
      <form className="finance-form" onSubmit={submit}>
        <div className="form-heading"><div><p className="eyebrow">Your next milestone</p><h3>{editing ? "Edit goal" : "Create goal"}</h3></div></div>
        <fieldset disabled={busy || uncertain} className="grid min-w-0 gap-4">
          <label>Name<input required maxLength={100} pattern=".*\S.*" value={form.name} onChange={(event) => change("name", event.target.value)} />{fieldError("name")}</label>
          {kind === "financial" && <label>Account<select required disabled={Boolean(editing) || accounts.isPending || Boolean(accounts.error)} value={form.account_id} onChange={(event) => change("account_id", event.target.value)}><option value="">Select account</option>{accounts.data?.map((account) => <option key={account.id} value={account.id}>{account.name}{account.archived_at ? " (archived)" : ""}</option>)}</select>{fieldError("account_id")}</label>}
          {kind === "financial" && accounts.isPending && <LoadingState label="Loading accounts…" />}
          {kind === "financial" && accounts.error && <ErrorState message="Accounts could not be loaded." onRetry={() => accounts.refetch()} />}
          {kind === "financial" && accounts.data?.length === 0 && <p className="field-help">Create an account in Finance to add a balance goal.</p>}
          <label>Baseline ({kind === "financial" ? "THB" : "kg"})<input required type="number" step="0.01" min={kind === "health" ? "1" : "-999999999999.99"} max={kind === "health" ? "500" : "999999999999.99"} disabled={Boolean(editing)} value={form.baseline} onChange={(event) => change("baseline", event.target.value)} />{fieldError(kind === "financial" ? "baseline_amount" : "baseline_weight_kg")}</label>
          <label>Target ({kind === "financial" ? "THB" : "kg"})<input required type="number" step="0.01" min={kind === "health" ? "1" : "-999999999999.99"} max={kind === "health" ? "500" : "999999999999.99"} disabled={Boolean(editing)} value={form.target} ref={(input) => {
            input?.setCustomValidity(!editing && form.target && form.baseline && (kind === "financial" ? Number(form.target) <= Number(form.baseline) : Number(form.target) === Number(form.baseline)) ? kind === "financial" ? "Target must be greater than baseline." : "Target must differ from baseline." : "");
          }} onChange={(event) => change("target", event.target.value)} />{fieldError(kind === "financial" ? "target_amount" : "target_weight_kg")}</label>
          <label>Start date<input type="date" required max={todayBangkok()} disabled={Boolean(editing)} value={form.start_date} onChange={(event) => change("start_date", event.target.value)} />{fieldError("start_date")}</label>
          <label>Due date (optional)<input type="date" min={form.start_date} value={form.due_date} onChange={(event) => change("due_date", event.target.value)} />{fieldError("due_date")}</label>
        </fieldset>
        <p className="field-help">{editing ? "Only the name and due date can change. Create a new goal to change the target or baseline." : kind === "financial" ? "Progress follows the account balance as of today. No money is reserved." : "Progress follows the latest recorded weight on or after the start date."}</p>
        {save.error && <p className="form-error" role="alert">{save.error.message} {fields?.body} {uncertain ? "The result is unknown. Retry checks the original goal before resending; your entry is preserved." : "Your entry is still here."}</p>}
        <Button type="submit" disabled={busy || (!editing && kind === "financial" && !form.account_id)}>{save.isPending ? "Saving…" : uncertain ? "Check and retry" : editing ? "Save changes" : "Create goal"}</Button>
        {(dirty || editing) && <Button type="button" variant="ghost" disabled={busy} onClick={() => leave(() => { reset(); save.reset(); })}>Cancel</Button>}
      </form>

      <section className="finance-list">
        <div className="list-heading"><div><p className="eyebrow">Progress from your records</p><h3>{kind === "financial" ? "Financial goals" : "Weight goals"}</h3></div><label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={includeArchived} onChange={(event) => { setIncludeArchived(event.target.checked); setPage(0); }} />Show archived</label></div>
        {goals.isFetching && !goals.isPending && <p role="status" className="field-help">Updating progress…</p>}
        {goals.isPending ? <LoadingState label="Loading goals…" /> : goals.error ? <ErrorState message="Goals could not be loaded." onRetry={() => goals.refetch()} /> : !goals.data?.items.length ? <EmptyState title="No goals here yet" description="Use the form to add a milestone, or show archived goals to revisit one." /> : <div className="grid gap-5">{goals.data.items.map((goal) => {
          const financial = "current_amount" in goal;
          const percent = goal.progress_percent === null ? null : Number(goal.progress_percent);
          return <article key={goal.id} className="grid gap-3 border-b pb-5 last:border-0">
            <div className="flex flex-wrap items-start justify-between gap-2"><div><h4 className="break-words font-semibold">{goal.name}</h4><p className="field-help">{financial ? goal.account_name : "Weight milestone"}</p></div><span className="kind">{goal.archived_at ? "Archived" : goal.achieved ? "Achieved" : percent === null ? "Awaiting data" : "In progress"}</span></div>
            <p className="text-sm">{financial ? `${formatThb(goal.current_amount)} of ${formatThb(goal.target_amount)}` : `${goal.current_weight_kg === null ? "No recorded weight" : formatWeight(goal.current_weight_kg)} → ${formatWeight(goal.target_weight_kg)}`}</p>
            {percent === null ? <p className="field-help">Record a weight on or after {formatDate(goal.start_date)} to see progress.</p> : <div className="flex items-center gap-3"><progress className="h-2 w-full accent-primary" max={100} value={percent} aria-label={`${goal.name} progress`} /><span className="text-xs tabular-nums">{percent.toFixed(1)}%</span></div>}
            <p className="field-help">Baseline {financial ? formatThb(goal.baseline_amount) : formatWeight(goal.baseline_weight_kg)} · Started {formatDate(goal.start_date)}{goal.due_date ? ` · Due ${formatDate(goal.due_date)}` : " · No due date"}{!financial && goal.current_weight_date ? ` · Latest weight ${formatDate(goal.current_weight_date)}` : ""}</p>
            <div className="flex flex-wrap gap-2"><Button size="sm" variant="outline" disabled={busy} onClick={() => edit(goal)}>Edit</Button><Button size="sm" variant="ghost" disabled={busy} onClick={() => archive.mutate(goal)}>{goal.archived_at ? "Unarchive" : "Archive"}</Button><Button size="sm" variant="ghost" disabled={busy} onClick={() => { remove.reset(); setDeleting(goal); }}>Delete</Button></div>
          </article>;
        })}</div>}
        {archive.error && <p role="alert" className="form-error">{archive.error.message} Refresh the list to check the result before trying again.<Button variant="ghost" onClick={() => goals.refetch()}>Refresh</Button></p>}
        <div className="pagination"><Button variant="outline" disabled={!page || goals.isFetching} onClick={() => setPage(page - 1)}>Previous</Button><span>Page {page + 1}</span><Button variant="outline" disabled={goals.isFetching || (page + 1) * 15 >= (goals.data?.total ?? 0)} onClick={() => setPage(page + 1)}>Next</Button></div>
      </section>
    </div>
    <ConfirmationDialog open={Boolean(deleting)} title="Delete this goal?" description={remove.error ? `${remove.error.message} The result may be unknown. Retry safely checks removal of the same goal.` : "This permanently removes the goal. Your transactions and health records remain."} confirmLabel={remove.isPending ? "Deleting…" : "Delete goal"} onConfirm={() => { if (deleting && !remove.isPending) remove.mutate(deleting); }} onCancel={() => { if (!remove.isPending) setDeleting(null); }} />
    <UnsavedFormFeedback open={Boolean(discard)} onDiscard={() => { discard?.(); setDiscard(null); }} onKeepEditing={() => setDiscard(null)} />
  </>;
}
