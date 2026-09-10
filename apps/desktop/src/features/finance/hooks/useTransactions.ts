import { useQuery } from "@tanstack/react-query";

import { financeApi } from "@/features/finance/api/finance.api";
import { financeKeys } from "@/features/finance/hooks/useFinance";

export function useTransactions(filters: Record<string, string | number | undefined>) {
  return useQuery({ queryKey: [...financeKeys.transactions, filters], queryFn: () => financeApi.transactions(filters) });
}
