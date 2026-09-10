import { useQuery } from "@tanstack/react-query";

import { healthApi } from "@/features/health/api/health.api";
import { healthKeys } from "@/features/health/hooks/useWeightLogs";

export function useWorkouts(filters: Record<string, string | number | undefined>) {
  return useQuery({ queryKey: [...healthKeys.workouts, filters], queryFn: () => healthApi.workouts(filters) });
}
