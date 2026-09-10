import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { financeApi } from "@/features/finance/api/finance.api";
import { financeKeys } from "@/features/finance/hooks/useFinance";
import { ApiError } from "@/lib/api-client";
import { todayBangkok } from "@/lib/format";
import type { Account, Category, Transaction, TransactionInput, TransactionKind } from "@/lib/api-types";

type Props = {
  accounts: Account[];
  categories: Category[];
  editing: Transaction | null;
  onDone: () => void;
};

function blank(): TransactionInput {
  return { id: crypto.randomUUID(), kind: "expense", account_id: "", to_account_id: null, category_id: "", amount: "", occurred_on: todayBangkok(), note: null };
}

export function TransactionForm({ accounts, categories, editing, onDone }: Props) {
  const client = useQueryClient();
  const [form, setForm] = useState<TransactionInput>(blank);
  const mutation = useMutation({
    mutationFn: (data: TransactionInput) => {
      if (!editing) return financeApi.createTransaction(data);
      const { id: _id, ...update } = data;
      return financeApi.updateTransaction(editing.id, update);
    },
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: financeKeys.all });
      setForm(blank());
      onDone();
    },
  });

  useEffect(() => {
    setForm(editing ? {
      id: editing.id,
      kind: editing.kind,
      account_id: editing.account_id,
      to_account_id: editing.to_account_id,
      category_id: editing.category_id,
      amount: editing.amount,
      occurred_on: editing.occurred_on,
      note: editing.note,
    } : blank());
    mutation.reset();
  }, [editing]);

  function set<K extends keyof TransactionInput>(key: K, value: TransactionInput[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function changeKind(kind: TransactionKind) {
    setForm((current) => ({ ...current, kind, category_id: kind === "transfer" ? null : "", to_account_id: kind === "transfer" ? "" : null }));
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate({ ...form, note: form.note?.trim() || null });
  }

  const activeAccounts = accounts.filter((account) => !account.archived_at || account.id === form.account_id || account.id === form.to_account_id);
  const matchingCategories = categories.filter((category) => category.kind === form.kind && (!category.archived_at || category.id === form.category_id));

  return (
    <form className="finance-form transaction-form" onSubmit={submit}>
      <div className="form-heading"><div><p className="eyebrow">{editing ? "Edit entry" : "Quick entry"}</p><h3>{editing ? "Update transaction" : "Add transaction"}</h3></div>{editing && <Button type="button" variant="ghost" onClick={onDone}>Cancel</Button>}</div>
      <label>Type<select value={form.kind} onChange={(event) => changeKind(event.target.value as TransactionKind)}><option value="expense">Expense</option><option value="income">Income</option><option value="transfer">Transfer</option></select></label>
      <label>Amount<input type="number" min="0.01" step="0.01" required value={form.amount} onChange={(event) => set("amount", event.target.value)} /></label>
      <label>Account<select required value={form.account_id} onChange={(event) => set("account_id", event.target.value)}><option value="">Select account</option>{activeAccounts.map((account) => <option key={account.id} value={account.id}>{account.name}</option>)}</select></label>
      {form.kind === "transfer" ? (
        <label>To account<select required value={form.to_account_id ?? ""} onChange={(event) => set("to_account_id", event.target.value)}><option value="">Select destination</option>{activeAccounts.filter((account) => account.id !== form.account_id).map((account) => <option key={account.id} value={account.id}>{account.name}</option>)}</select></label>
      ) : (
        <label>Category<select required value={form.category_id ?? ""} onChange={(event) => set("category_id", event.target.value)}><option value="">Select category</option>{matchingCategories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label>
      )}
      <label>Date<input type="date" max={todayBangkok()} required value={form.occurred_on} onChange={(event) => set("occurred_on", event.target.value)} /></label>
      <label className="form-wide">Note<textarea maxLength={2000} value={form.note ?? ""} onChange={(event) => set("note", event.target.value)} placeholder="Optional" /></label>
      {mutation.error && <p className="form-error form-wide" role="alert">{mutation.error instanceof ApiError ? mutation.error.message : "Transaction could not be saved."} Your entry is still here; submit again to retry with the same ID.</p>}
      <Button className="form-wide" type="submit" disabled={mutation.isPending}>{mutation.isPending ? "Saving…" : editing ? "Save changes" : "Add transaction"}</Button>
    </form>
  );
}
