import assert from "node:assert/strict";
import test from "node:test";

import { formatDate, formatDuration, formatThb, formatWeight } from "./format.ts";
import { getRoute } from "../routes/routes.ts";

test("Phase 1 shared behavior", () => {
  assert.equal(getRoute("/health").id, "health");
  assert.equal(getRoute("/unknown").id, "dashboard");
  assert.equal(formatDate("2026-09-10"), "10 Sept 2026");
  assert.equal(formatThb("1250.5"), "฿1,250.50");
  assert.equal(formatWeight("82.40"), "82.4 kg");
  assert.equal(formatDuration(90), "1 hr 30 min");
});
