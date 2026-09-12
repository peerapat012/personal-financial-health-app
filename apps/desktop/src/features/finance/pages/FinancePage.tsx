import { useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Archive, Pencil, RotateCcw, Trash2 } from "lucide-react";

import { ConfirmationDialog, EmptyState, ErrorState, LoadingState } from "@/components/Feedback";
import { Button } from "@/components/ui/button";
import { financeApi } from "@/features/finance/api/finance.api";
import { TransactionForm } from "@/features/finance/components/TransactionForm";
import { TransactionTable } from "@/features/finance/components/TransactionTable";
import { financeKeys, useAccounts, useBudgets, useCategories } from "@/features/finance/hooks/useFinance";
import { ApiError } from "@/lib/api-client";
import { formatDate, formatThb, todayBangkok } from "@/lib/format";
import type { Account, AccountKind, Budget, Category, CategoryKind, Transaction } from "@/lib/api-types";

type View = "transactions" | "accounts" | "categories" | "budgets";

function MutationError({ error }: { error: Error | null }) {
  return error && <p className="form-error" role="alert">{error instanceof ApiError ? error.message : "The change could not be saved."}</p>;
}

function AccountsPanel({ accounts }: { accounts: Account[] }) {
  const client = useQueryClient();
  const [name, setName] = useState("");
  const [kind, setKind] = useState<AccountKind>("bank");
  const [balance, setBalance] = useState("0.00");
  const [openingDate, setOpeningDate] = useState(todayBangkok);
  const [editing, setEditing] = useState<Account | null>(null);
  const [editName, setEditName] = useState("");
  const [deleting, setDeleting] = useState<Account | null>(null);
  const refresh = () => client.invalidateQueries({ queryKey: financeKeys.all });
  const create = useMutation({ mutationFn: financeApi.createAccount, onSuccess: async () => { setName(""); setBalance("0.00"); await refresh(); } });
  const update = useMutation({ mutationFn: ({ id, data }: { id: string; data: { name?: string; archived?: boolean } }) => financeApi.updateAccount(id, data), onSuccess: async () => { setEditing(null); await refresh(); } });
  const remove = useMutation({ mutationFn: financeApi.deleteAccount, onSuccess: async () => { setDeleting(null); await refresh(); } });

  function submit(event: FormEvent) {
    event.preventDefault();
    create.mutate({ id: crypto.randomUUID(), name, kind, opening_balance: balance, opening_date: openingDate });
  }

  return <div className="finance-split"><form className="finance-form" onSubmit={submit}><p className="eyebrow">New account</p><h3>Add an account</h3><label>Name<input required maxLength={100} value={name} onChange={(event) => setName(event.target.value)} /></label><label>Type<select value={kind} onChange={(event) => setKind(event.target.value as AccountKind)}><option value="cash">Cash</option><option value="bank">Bank</option><option value="ewallet">E-wallet</option></select></label><label>Opening balance<input required type="number" step="0.01" value={balance} onChange={(event) => setBalance(event.target.value)} /></label><label>Opening date<input required type="date" max={todayBangkok()} value={openingDate} onChange={(event) => setOpeningDate(event.target.value)} /></label><MutationError error={create.error} /><Button type="submit" disabled={create.isPending}>{create.isPending ? "Adding…" : "Add account"}</Button></form><section className="finance-list"><div className="list-heading"><div><p className="eyebrow">Balances</p><h3>Accounts</h3></div><span>{accounts.length} accounts</span></div>{!accounts.length ? <EmptyState title="No accounts yet" description="Create your first cash, bank, or e-wallet account to begin." /> : <div className="account-grid">{accounts.map((account) => <article className={account.archived_at ? "account-card archived" : "account-card"} key={account.id}><div><span className="kind">{account.kind}</span><strong>{account.name}</strong><p>Opened {formatDate(account.opening_date)}</p></div><b>{formatThb(account.current_balance)}</b>{editing?.id === account.id ? <form className="inline-edit" onSubmit={(event) => { event.preventDefault(); update.mutate({ id: account.id, data: { name: editName } }); }}><input required maxLength={100} value={editName} onChange={(event) => setEditName(event.target.value)} /><Button type="submit">Save</Button><Button type="button" variant="ghost" onClick={() => setEditing(null)}>Cancel</Button></form> : <div className="row-actions"><Button size="icon-sm" variant="ghost" aria-label="Rename account" onClick={() => { setEditing(account); setEditName(account.name); }}><Pencil /></Button><Button size="icon-sm" variant="ghost" aria-label={account.archived_at ? "Unarchive account" : "Archive account"} onClick={() => update.mutate({ id: account.id, data: { archived: !account.archived_at } })}>{account.archived_at ? <RotateCcw /> : <Archive />}</Button><Button size="icon-sm" variant="ghost" aria-label="Delete account" onClick={() => setDeleting(account)}><Trash2 /></Button></div>}</article>)}</div>}<MutationError error={update.error ?? remove.error} /></section><ConfirmationDialog open={Boolean(deleting)} title="Delete this account?" description="Only an unused account can be deleted. This action cannot be undone." confirmLabel="Delete account" onConfirm={() => deleting && remove.mutate(deleting.id)} onCancel={() => setDeleting(null)} /></div>;
}

function CategoriesPanel({ categories }: { categories: Category[] }) {
  const client = useQueryClient();
  const [name, setName] = useState("");
  const [kind, setKind] = useState<CategoryKind>("expense");
  const [editing, setEditing] = useState<Category | null>(null);
  const [editName, setEditName] = useState("");
  const [deleting, setDeleting] = useState<Category | null>(null);
  const refresh = () => client.invalidateQueries({ queryKey: financeKeys.all });
  const create = useMutation({ mutationFn: financeApi.createCategory, onSuccess: async () => { setName(""); await refresh(); } });
  const update = useMutation({ mutationFn: ({ id, data }: { id: string; data: { name?: string; archived?: boolean } }) => financeApi.updateCategory(id, data), onSuccess: async () => { setEditing(null); await refresh(); } });
  const remove = useMutation({ mutationFn: financeApi.deleteCategory, onSuccess: async () => { setDeleting(null); await refresh(); } });

  return <div className="finance-split"><form className="finance-form" onSubmit={(event) => { event.preventDefault(); create.mutate({ id: crypto.randomUUID(), name, kind }); }}><p className="eyebrow">New category</p><h3>Organize transactions</h3><label>Name<input required maxLength={100} value={name} onChange={(event) => setName(event.target.value)} /></label><label>Type<select value={kind} onChange={(event) => setKind(event.target.value as CategoryKind)}><option value="expense">Expense</option><option value="income">Income</option></select></label><MutationError error={create.error} /><Button type="submit" disabled={create.isPending}>Add category</Button></form><section className="finance-list"><div className="list-heading"><div><p className="eyebrow">Classification</p><h3>Categories</h3></div><span>{categories.length} categories</span></div><div className="table-scroll"><table><thead><tr><th>Name</th><th>Type</th><th>Status</th><th /></tr></thead><tbody>{categories.map((category) => <tr key={category.id}><td>{editing?.id === category.id ? <form className="inline-edit" onSubmit={(event) => { event.preventDefault(); update.mutate({ id: category.id, data: { name: editName } }); }}><input required value={editName} onChange={(event) => setEditName(event.target.value)} /><Button type="submit">Save</Button></form> : category.name}</td><td><span className={`kind kind-${category.kind}`}>{category.kind}</span></td><td>{category.archived_at ? "Archived" : "Active"}</td><td><div className="row-actions"><Button size="icon-sm" variant="ghost" aria-label="Rename category" onClick={() => { setEditing(category); setEditName(category.name); }}><Pencil /></Button><Button size="icon-sm" variant="ghost" aria-label={category.archived_at ? "Unarchive category" : "Archive category"} onClick={() => update.mutate({ id: category.id, data: { archived: !category.archived_at } })}>{category.archived_at ? <RotateCcw /> : <Archive />}</Button><Button size="icon-sm" variant="ghost" aria-label="Delete category" onClick={() => setDeleting(category)}><Trash2 /></Button></div></td></tr>)}</tbody></table></div><MutationError error={update.error ?? remove.error} /></section><ConfirmationDialog open={Boolean(deleting)} title="Delete this category?" description="Only an unused category can be deleted. Historical categories should be archived instead." confirmLabel="Delete category" onConfirm={() => deleting && remove.mutate(deleting.id)} onCancel={() => setDeleting(null)} /></div>;
}

function BudgetsPanel({ categories }: { categories: Category[] }) {
  const client = useQueryClient();
  const [month, setMonth] = useState(todayBangkok().slice(0, 7));
  const [categoryId, setCategoryId] = useState("");
  const [amount, setAmount] = useState("");
  const [editing, setEditing] = useState<Budget | null>(null);
  const [editAmount, setEditAmount] = useState("");
  const [deleting, setDeleting] = useState<Budget | null>(null);
  const budgets = useBudgets(month);
  const refresh = () => client.invalidateQueries({ queryKey: financeKeys.budgets });
  const create = useMutation({ mutationFn: financeApi.createBudget, onSuccess: async () => { setAmount(""); await refresh(); } });
  const update = useMutation({ mutationFn: ({ id, value }: { id: string; value: string }) => financeApi.updateBudget(id, value), onSuccess: async () => { setEditing(null); await refresh(); } });
  const remove = useMutation({ mutationFn: financeApi.deleteBudget, onSuccess: async () => { setDeleting(null); await refresh(); } });
  const expenseCategories = categories.filter((category) => category.kind === "expense" && !category.archived_at);

  return <div className="finance-split"><form className="finance-form" onSubmit={(event) => { event.preventDefault(); create.mutate({ id: crypto.randomUUID(), category_id: categoryId, month, amount }); }}><p className="eyebrow">Monthly guide</p><h3>Set a budget</h3><label>Month<input type="month" required value={month} onChange={(event) => setMonth(event.target.value)} /></label><label>Expense category<select required value={categoryId} onChange={(event) => setCategoryId(event.target.value)}><option value="">Select category</option>{expenseCategories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label><label>Amount<input type="number" min="0.01" step="0.01" required value={amount} onChange={(event) => setAmount(event.target.value)} /></label><MutationError error={create.error} /><Button type="submit" disabled={create.isPending}>Set budget</Button></form><section className="finance-list"><div className="list-heading"><div><p className="eyebrow">{month}</p><h3>Budgets</h3></div><span>{budgets.data?.total ?? 0} categories</span></div>{budgets.isLoading ? <LoadingState /> : budgets.error ? <ErrorState message="Budgets could not be loaded." onRetry={() => budgets.refetch()} /> : !budgets.data?.items.length ? <EmptyState title="No budgets this month" description="Choose an expense category and set a practical monthly amount." /> : <div className="budget-list">{budgets.data.items.map((budget) => <article key={budget.id}><div><strong>{budget.category_name}</strong><span>{budget.month}</span></div>{editing?.id === budget.id ? <form className="inline-edit" onSubmit={(event) => { event.preventDefault(); update.mutate({ id: budget.id, value: editAmount }); }}><input type="number" min="0.01" step="0.01" required value={editAmount} onChange={(event) => setEditAmount(event.target.value)} /><Button type="submit">Save</Button></form> : <b>{formatThb(budget.amount)}</b>}<div className="row-actions"><Button size="icon-sm" variant="ghost" aria-label="Edit budget" onClick={() => { setEditing(budget); setEditAmount(budget.amount); }}><Pencil /></Button><Button size="icon-sm" variant="ghost" aria-label="Delete budget" onClick={() => setDeleting(budget)}><Trash2 /></Button></div></article>)}</div>}<MutationError error={update.error ?? remove.error} /></section><ConfirmationDialog open={Boolean(deleting)} title="Delete this budget?" description="Spending records stay unchanged; only this monthly target is removed." confirmLabel="Delete budget" onConfirm={() => deleting && remove.mutate(deleting.id)} onCancel={() => setDeleting(null)} /></div>;
}

export function FinancePage() {
  const [view, setView] = useState<View>(() => {
    const requested = new URLSearchParams(window.location.hash.split("?")[1]).get("view");
    return requested === "accounts" || requested === "categories" || requested === "budgets" ? requested : "transactions";
  });
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null);
  const accounts = useAccounts(true);
  const categories = useCategories(true);
  const loading = accounts.isLoading || categories.isLoading;
  const failed = accounts.error || categories.error;

  return <><div className="finance-tabs" role="tablist" aria-label="Finance sections">{(["transactions", "accounts", "categories", "budgets"] as View[]).map((item) => <Button key={item} role="tab" aria-selected={view === item} variant={view === item ? "secondary" : "ghost"} onClick={() => setView(item)}>{item}</Button>)}</div>{loading ? <LoadingState label="Loading finance…" /> : failed ? <ErrorState message="Finance data could not be loaded." onRetry={() => { accounts.refetch(); categories.refetch(); }} /> : <div className="finance-content">{view === "transactions" && <><TransactionForm accounts={accounts.data?.items ?? []} categories={categories.data?.items ?? []} editing={editingTransaction} onDone={() => setEditingTransaction(null)} /><TransactionTable accounts={accounts.data?.items ?? []} categories={categories.data?.items ?? []} onEdit={setEditingTransaction} /></>}{view === "accounts" && <AccountsPanel accounts={accounts.data?.items ?? []} />}{view === "categories" && <CategoriesPanel categories={categories.data?.items ?? []} />}{view === "budgets" && <BudgetsPanel categories={categories.data?.items ?? []} />}</div>}</>;
}
