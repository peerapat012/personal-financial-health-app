import { useQuery } from "@tanstack/react-query";

import { healthApi } from "@/features/health/api/health.api";

export const healthKeys = {
  all: ["health"] as const,
  weights: ["health", "weights"] as const,
  workouts: ["health", "workouts"] as const,
};

export function useWeightLogs(filters: Record<string, string | number | undefined>) {
  return useQuery({ queryKey: [...healthKeys.weights, filters], queryFn: () => healthApi.weightLogs(filters) });
}
