import { apiRequest } from "@/lib/api-client";
import type { Account, AccountInput, Budget, BudgetInput, Category, CategoryInput, ListResponse, Transaction, TransactionInput } from "@/lib/api-types";

function query(path: string, values: Record<string, string | number | boolean | undefined>) {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => value !== undefined && value !== "" && params.set(key, String(value)));
  const suffix = params.toString();
  return suffix ? `${path}?${suffix}` : path;
}

export const financeApi = {
  accounts: (includeArchived = false) => apiRequest<ListResponse<Account>>(query("/accounts", { include_archived: includeArchived })),
  createAccount: (data: AccountInput) => apiRequest<Account>("/accounts", { method: "POST", body: JSON.stringify(data) }),
  updateAccount: (id: string, data: { name?: string; archived?: boolean }) => apiRequest<Account>(`/accounts/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteAccount: (id: string) => apiRequest<void>(`/accounts/${id}`, { method: "DELETE" }),
  categories: (includeArchived = false) => apiRequest<ListResponse<Category>>(query("/categories", { include_archived: includeArchived })),
  createCategory: (data: CategoryInput) => apiRequest<Category>("/categories", { method: "POST", body: JSON.stringify(data) }),
  updateCategory: (id: string, data: { name?: string; archived?: boolean }) => apiRequest<Category>(`/categories/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteCategory: (id: string) => apiRequest<void>(`/categories/${id}`, { method: "DELETE" }),
  transactions: (filters: Record<string, string | number | undefined>) => apiRequest<ListResponse<Transaction>>(query("/transactions", filters)),
  createTransaction: (data: TransactionInput) => apiRequest<Transaction>("/transactions", { method: "POST", body: JSON.stringify(data) }),
  updateTransaction: (id: string, data: Omit<TransactionInput, "id">) => apiRequest<Transaction>(`/transactions/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteTransaction: (id: string) => apiRequest<void>(`/transactions/${id}`, { method: "DELETE" }),
  budgets: (month?: string) => apiRequest<ListResponse<Budget>>(query("/budgets", { month })),
  createBudget: (data: BudgetInput) => apiRequest<Budget>("/budgets", { method: "POST", body: JSON.stringify(data) }),
  updateBudget: (id: string, amount: string) => apiRequest<Budget>(`/budgets/${id}`, { method: "PATCH", body: JSON.stringify({ amount }) }),
  deleteBudget: (id: string) => apiRequest<void>(`/budgets/${id}`, { method: "DELETE" }),
};
