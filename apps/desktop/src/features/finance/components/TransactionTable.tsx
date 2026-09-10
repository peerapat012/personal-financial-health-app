import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Pencil, Trash2 } from "lucide-react";

import { ConfirmationDialog, EmptyState, ErrorState, LoadingState } from "@/components/Feedback";
import { Button } from "@/components/ui/button";
import { financeApi } from "@/features/finance/api/finance.api";
import { financeKeys } from "@/features/finance/hooks/useFinance";
import { useTransactions } from "@/features/finance/hooks/useTransactions";
import { formatDate, formatThb } from "@/lib/format";
import type { Account, Category, Transaction, TransactionKind } from "@/lib/api-types";

type Props = { accounts: Account[]; categories: Category[]; onEdit: (transaction: Transaction) => void };

export function TransactionTable({ accounts, categories, onEdit }: Props) {
  const client = useQueryClient();
  const [page, setPage] = useState(0);
  const [kind, setKind] = useState<TransactionKind | "">("");
  const [account, setAccount] = useState("");
  const [category, setCategory] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [search, setSearch] = useState("");
  const [deleting, setDeleting] = useState<Transaction | null>(null);
  const transactions = useTransactions({ kind, account_id: account, category_id: category, from, to, q: search, limit: 10, offset: page * 10 });
  const remove = useMutation({
    mutationFn: (id: string) => financeApi.deleteTransaction(id),
    onSuccess: async () => {
      setDeleting(null);
      await client.invalidateQueries({ queryKey: financeKeys.all });
    },
  });

  function filter(value: string, setter: (value: string) => void) {
    setPage(0);
    setter(value);
  }

  return (
    <section className="finance-list">
      <div className="list-heading"><div><p className="eyebrow">Ledger</p><h3>Transactions</h3></div><span>{transactions.data?.total ?? 0} entries</span></div>
      <div className="transaction-filters">
        <input aria-label="Search notes" placeholder="Search notes…" value={search} onChange={(event) => filter(event.target.value, setSearch)} />
        <select aria-label="Transaction type" value={kind} onChange={(event) => filter(event.target.value, (value) => setKind(value as TransactionKind | ""))}><option value="">All types</option><option value="income">Income</option><option value="expense">Expense</option><option value="transfer">Transfer</option></select>
        <select aria-label="Account" value={account} onChange={(event) => filter(event.target.value, setAccount)}><option value="">All accounts</option>{accounts.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
        <select aria-label="Category" value={category} onChange={(event) => filter(event.target.value, setCategory)}><option value="">All categories</option>{categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
        <input aria-label="From date" type="date" value={from} onChange={(event) => filter(event.target.value, setFrom)} />
        <input aria-label="To date" type="date" min={from} value={to} onChange={(event) => filter(event.target.value, setTo)} />
      </div>
      {transactions.isLoading ? <LoadingState label="Loading transactions…" /> : transactions.error ? <ErrorState message="Transactions could not be loaded." onRetry={() => transactions.refetch()} /> : !transactions.data?.items.length ? (
        <EmptyState title="No transactions match" description="Add an income, expense, or transfer—or clear a filter to see more." />
      ) : (
        <div className="table-scroll"><table><thead><tr><th>Date</th><th>Type</th><th>Category / destination</th><th>Account</th><th className="amount">Amount</th><th><span className="sr-only">Actions</span></th></tr></thead><tbody>{transactions.data.items.map((item) => <tr key={item.id}><td>{formatDate(item.occurred_on)}</td><td><span className={`kind kind-${item.kind}`}>{item.kind}</span></td><td>{item.kind === "transfer" ? item.to_account_name : item.category_name}</td><td>{item.account_name}</td><td className={`amount money-${item.kind}`}>{item.kind === "expense" ? "−" : item.kind === "income" ? "+" : ""}{formatThb(item.amount)}</td><td><div className="row-actions"><Button size="icon-sm" variant="ghost" aria-label="Edit transaction" onClick={() => onEdit(item)}><Pencil /></Button><Button size="icon-sm" variant="ghost" aria-label="Delete transaction" onClick={() => setDeleting(item)}><Trash2 /></Button></div></td></tr>)}</tbody></table></div>
      )}
      <div className="pagination"><Button variant="outline" disabled={!page} onClick={() => setPage((value) => value - 1)}>Previous</Button><span>Page {page + 1}</span><Button variant="outline" disabled={(page + 1) * 10 >= (transactions.data?.total ?? 0)} onClick={() => setPage((value) => value + 1)}>Next</Button></div>
      {remove.error && <p className="form-error" role="alert">Delete failed. Nothing was removed; try again.</p>}
      <ConfirmationDialog open={Boolean(deleting)} title="Delete this transaction?" description="This permanently removes the entry and updates its account balance." confirmLabel={remove.isPending ? "Deleting…" : "Delete transaction"} onConfirm={() => deleting && remove.mutate(deleting.id)} onCancel={() => setDeleting(null)} />
    </section>
  );
}
