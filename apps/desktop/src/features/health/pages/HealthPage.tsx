import { useState } from "react";

import { Button } from "@/components/ui/button";
import { WeightLogPanel } from "@/features/health/components/WeightLogPanel";
import { WorkoutPanel } from "@/features/health/components/WorkoutPanel";

export function HealthPage() {
  const [view, setView] = useState<"weight" | "workouts">("weight");
  return <><div className="finance-tabs" role="tablist" aria-label="Health sections"><Button role="tab" aria-selected={view === "weight"} variant={view === "weight" ? "secondary" : "ghost"} onClick={() => setView("weight")}>Weight</Button><Button role="tab" aria-selected={view === "workouts"} variant={view === "workouts" ? "secondary" : "ghost"} onClick={() => setView("workouts")}>Workouts</Button></div>{view === "weight" ? <WeightLogPanel /> : <WorkoutPanel />}</>;
}
