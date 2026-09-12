import { apiRequest } from "@/lib/api-client";
import type { Dashboard } from "@/lib/api-types";

export const getDashboard = (month: string) => apiRequest<Dashboard>(`/dashboard?month=${encodeURIComponent(month)}`);
