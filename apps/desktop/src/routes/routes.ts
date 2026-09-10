export type RouteId = "dashboard" | "finance" | "health" | "goals" | "settings";

export type AppRoute = {
  id: RouteId;
  path: `/${RouteId}`;
  label: string;
  kicker: string;
  description: string;
};

export const appRoutes: AppRoute[] = [
  { id: "dashboard", path: "/dashboard", label: "Dashboard", kicker: "Today at a glance", description: "Your balances, monthly activity, health, and goals will meet here." },
  { id: "finance", path: "/finance", label: "Finance", kicker: "Money in motion", description: "Accounts, transactions, categories, and budgets will live here." },
  { id: "health", path: "/health", label: "Health", kicker: "Daily signals", description: "Weight entries, workouts, and simple trends will live here." },
  { id: "goals", path: "/goals", label: "Goals", kicker: "Progress with context", description: "Financial milestones and weight goals will live here." },
  { id: "settings", path: "/settings", label: "Settings", kicker: "App controls", description: "Display preferences, API status, export, and session controls will live here." },
];

export function getRoute(path: string): AppRoute {
  return appRoutes.find((route) => route.path === path) ?? appRoutes[0];
}

export function getRouteFromHash(): AppRoute {
  return getRoute(window.location.hash.slice(1));
}
