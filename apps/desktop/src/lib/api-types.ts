export type ErrorEnvelope = {
  error: {
    code: string;
    message: string;
    fields?: Record<string, string>;
    request_id: string;
  };
};

export type SessionResponse = {
  authenticated: true;
  currency: "THB";
  timezone: "Asia/Bangkok";
  units: { weight: "kg"; water: "ml" };
};

export type HealthResponse = { status: "ok" };

export type ListResponse<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};

export type AccountKind = "cash" | "bank" | "ewallet";
export type CategoryKind = "income" | "expense";
export type TransactionKind = "income" | "expense" | "transfer";
type Timestamps = { created_at: string; updated_at: string };

export type Account = Timestamps & {
  id: string;
  name: string;
  kind: AccountKind;
  opening_balance: string;
  opening_date: string;
  archived_at: string | null;
  current_balance: string;
};

export type Category = Timestamps & {
  id: string;
  name: string;
  kind: CategoryKind;
  archived_at: string | null;
};

export type Transaction = Timestamps & {
  id: string;
  kind: TransactionKind;
  account_id: string;
  account_name: string;
  to_account_id: string | null;
  to_account_name: string | null;
  category_id: string | null;
  category_name: string | null;
  amount: string;
  occurred_on: string;
  note: string | null;
};

export type Budget = Timestamps & {
  id: string;
  category_id: string;
  category_name: string;
  month: string;
  amount: string;
};

export type AccountInput = Pick<Account, "id" | "name" | "kind" | "opening_balance" | "opening_date">;
export type CategoryInput = Pick<Category, "id" | "name" | "kind">;
export type TransactionInput = Pick<Transaction, "id" | "kind" | "account_id" | "to_account_id" | "category_id" | "amount" | "occurred_on" | "note">;
export type BudgetInput = Pick<Budget, "id" | "category_id" | "month" | "amount">;
