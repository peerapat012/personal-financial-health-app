import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

import { formatDate, formatDuration, formatThb, formatWeight } from "./format.ts";
import { getRoute } from "../routes/routes.ts";
import { isDark } from "./theme.ts";

test("Phase 1 shared behavior", () => {
  assert.equal(getRoute("/health").id, "health");
  assert.equal(getRoute("/unknown").id, "dashboard");
  assert.equal(formatDate("2026-09-10"), "10 Sept 2026");
  assert.equal(formatThb("1250.5"), "฿1,250.50");
  assert.equal(formatWeight("82.40"), "82.4 kg");
  assert.equal(formatDuration(90), "1 hr 30 min");
});

test("Phase 5 quick-add routes and theme selection", () => {
  assert.equal(getRoute("/finance?view=accounts").id, "finance");
  assert.equal(getRoute("/health?view=workouts").id, "health");
  assert.equal(isDark("system", true), true);
  assert.equal(isDark("system", false), false);
  assert.equal(isDark("light", true), false);
  assert.equal(isDark("dark", false), true);
});

test("Phase 6 mutation failures retain the form and client ID", () => {
  const source = readFileSync(new URL("../features/finance/components/TransactionForm.tsx", import.meta.url), "utf8");
  assert.match(source, /mutation\.mutate\(\{ \.\.\.form,/);
  assert.match(source, /onSuccess:[\s\S]*setForm\(blank\(\)\)/);
  assert.match(source, /retry with the same ID/);
});
