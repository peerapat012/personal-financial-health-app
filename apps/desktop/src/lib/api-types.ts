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

export type ActivityType = "walk" | "run" | "cycle" | "strength" | "other";

export type WeightLog = Timestamps & {
  id: string;
  log_date: string;
  weight_kg: string | null;
  note: string | null;
};

export type Workout = Timestamps & {
  id: string;
  occurred_on: string;
  activity_type: ActivityType;
  duration_minutes: number;
  note: string | null;
};

export type WeightLogInput = Pick<WeightLog, "weight_kg" | "note">;
export type WorkoutInput = Pick<Workout, "id" | "occurred_on" | "activity_type" | "duration_minutes" | "note">;

export type HealthSummary = {
  from_date: string;
  to_date: string;
  latest_weight_kg: string | null;
  latest_weight_date: string | null;
  average_weight_kg: string | null;
  recorded_weight_days: number;
  workout_minutes: number;
};

export type GoalInput = {
  id: string;
  name: string;
  start_date: string;
  due_date: string | null;
};
export type FinancialGoalInput = GoalInput & { account_id: string; baseline_amount: string; target_amount: string };
export type HealthGoalInput = GoalInput & { baseline_weight_kg: string; target_weight_kg: string };
export type GoalPatch = { name?: string; due_date?: string | null; archived?: boolean };
type GoalProgress = Timestamps & {
  archived_at: string | null;
  progress_ratio: string | null;
  progress_percent: string | null;
  achieved: boolean;
};
export type FinancialGoal = FinancialGoalInput & GoalProgress & { account_name: string; current_amount: string };
export type HealthGoal = HealthGoalInput & GoalProgress & { current_weight_kg: string | null; current_weight_date: string | null };
export type Goal = FinancialGoal | HealthGoal;
export type GoalKind = "financial" | "health";

export type Dashboard = {
  month: string;
  account_balances: { as_of: string; total: string; items: Account[] };
  finance: { month: string; income: string; expense: string; net_cash_flow: string; expense_by_category: { category_id: string; category_name: string; amount: string }[] };
  budgets: { id: string; category_id: string; category_name: string; amount: string; actual: string; remaining: string }[];
  health: { latest_weight_kg: string | null; latest_weight_date: string | null; workout_minutes: number; recorded_weight_days: number; average_weight_kg: string | null; weight_trend: { date: string; weight_kg: string | null }[] };
  goals: Goal[];
  recent_transactions: Transaction[];
};
