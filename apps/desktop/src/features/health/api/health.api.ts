import { apiRequest } from "@/lib/api-client";
import type { ListResponse, WeightLog, WeightLogInput, Workout, WorkoutInput } from "@/lib/api-types";

function query(path: string, values: Record<string, string | number | undefined>) {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => value !== undefined && value !== "" && params.set(key, String(value)));
  const suffix = params.toString();
  return suffix ? `${path}?${suffix}` : path;
}

export const healthApi = {
  weightLogs: (filters: Record<string, string | number | undefined>) => apiRequest<ListResponse<WeightLog>>(query("/weight-logs", filters)),
  putWeightLog: (date: string, data: WeightLogInput) => apiRequest<WeightLog>(`/weight-logs/${date}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteWeightLog: (date: string) => apiRequest<void>(`/weight-logs/${date}`, { method: "DELETE" }),
  workouts: (filters: Record<string, string | number | undefined>) => apiRequest<ListResponse<Workout>>(query("/workouts", filters)),
  createWorkout: (data: WorkoutInput) => apiRequest<Workout>("/workouts", { method: "POST", body: JSON.stringify(data) }),
  updateWorkout: (id: string, data: Omit<WorkoutInput, "id">) => apiRequest<Workout>(`/workouts/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteWorkout: (id: string) => apiRequest<void>(`/workouts/${id}`, { method: "DELETE" }),
};
