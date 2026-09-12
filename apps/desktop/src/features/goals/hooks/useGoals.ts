import { useQuery } from "@tanstack/react-query";
import { goalsApi } from "@/features/goals/api/goals.api";
import type { GoalKind } from "@/lib/api-types";

export function useGoals(kind: GoalKind, includeArchived: boolean, page: number) {
  return useQuery({
    queryKey: ["goals", kind, includeArchived, page],
    queryFn: () => goalsApi.list(kind, includeArchived, page * 15),
    staleTime: 0,
    refetchOnMount: "always",
  });
}
