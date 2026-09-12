import { ApiError, apiRequest } from "@/lib/api-client";
import type { Account, FinancialGoalInput, Goal, GoalKind, GoalPatch, HealthGoalInput, ListResponse } from "@/lib/api-types";

export const goalsApi = {
  list: (kind: GoalKind, includeArchived: boolean, offset: number) =>
    apiRequest<ListResponse<Goal>>(`/${kind}-goals?include_archived=${includeArchived}&limit=15&offset=${offset}`),
  get: (kind: GoalKind, id: string) => apiRequest<Goal>(`/${kind}-goals/${id}`),
  create: async (kind: GoalKind, data: FinancialGoalInput | HealthGoalInput, checkFirst: boolean) => {
    if (checkFirst) {
      try {
        await goalsApi.get(kind, data.id);
      } catch (error) {
        if (!(error instanceof ApiError) || error.status !== 404) throw error;
      }
    }
    // The server compares the same ID and payload, returning an existing goal or a conflict.
    return apiRequest<Goal>(`/${kind}-goals`, { method: "POST", body: JSON.stringify(data) });
  },
  update: async (kind: GoalKind, id: string, data: GoalPatch) => {
    const existing = await goalsApi.get(kind, id);
    if ((data.name === undefined || data.name === existing.name)
      && (data.due_date === undefined || data.due_date === existing.due_date)
      && (data.archived === undefined || data.archived === Boolean(existing.archived_at))) return existing;
    return apiRequest<Goal>(`/${kind}-goals/${id}`, { method: "PATCH", body: JSON.stringify(data) });
  },
  remove: async (kind: GoalKind, id: string) => {
    try {
      await goalsApi.get(kind, id);
      await apiRequest<void>(`/${kind}-goals/${id}`, { method: "DELETE" });
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 404) throw error;
    }
  },
  accounts: async () => {
    const items: Account[] = [];
    let page: ListResponse<Account>;
    do {
      page = await apiRequest<ListResponse<Account>>(`/accounts?include_archived=true&limit=200&offset=${items.length}`);
      items.push(...page.items);
    } while (page.items.length && items.length < page.total);
    return items;
  },
};
