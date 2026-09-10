import { useQuery } from "@tanstack/react-query";
import { financeApi } from "@/features/finance/api/finance.api";

export const financeKeys = {
  all: ["finance"] as const,
  accounts: ["finance", "accounts"] as const,
  categories: ["finance", "categories"] as const,
  transactions: ["finance", "transactions"] as const,
  budgets: ["finance", "budgets"] as const,
};

export function useAccounts(includeArchived = false) {
  return useQuery({ queryKey: [...financeKeys.accounts, includeArchived], queryFn: () => financeApi.accounts(includeArchived) });
}

export function useCategories(includeArchived = false) {
  return useQuery({ queryKey: [...financeKeys.categories, includeArchived], queryFn: () => financeApi.categories(includeArchived) });
}

export function useBudgets(month?: string) {
  return useQuery({ queryKey: [...financeKeys.budgets, month], queryFn: () => financeApi.budgets(month) });
}
