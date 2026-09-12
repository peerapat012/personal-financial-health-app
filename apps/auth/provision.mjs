import { Pool } from "pg";
import { getMigrations } from "better-auth/db/migration";
import { authOptions, createAuth } from "./auth.mjs";

const operation = process.argv[2];
if (!["migrate", "owner"].includes(operation)) throw new Error("Choose migrate or owner");
if (!process.env.AUTH_DATABASE_DIRECT_URL) throw new Error("Set AUTH_DATABASE_DIRECT_URL");
const pool = new Pool({ connectionString: process.env.AUTH_DATABASE_DIRECT_URL, max: 1, connectionTimeoutMillis: 5000 });
try {
  if (operation === "migrate") {
    const plan = await getMigrations(authOptions(pool));
    await plan.runMigrations();
    console.log("Auth tables migrated");
  } else {
    const values = ["OWNER_NAME", "OWNER_EMAIL", "OWNER_USERNAME", "OWNER_PASSWORD"];
    if (values.some((key) => !process.env[key])) throw new Error("Set owner values in .env.owner first");
    if (process.env.OWNER_PASSWORD.startsWith("replace-")) throw new Error("Replace the example owner password");
    // This CLI never listens for HTTP and refuses to provision a second owner.
    const existing = await pool.query('SELECT id FROM auth_user LIMIT 1');
    if (existing.rowCount) throw new Error("An owner already exists; no account was changed");
    const auth = createAuth(pool, true);
    const result = await auth.api.signUpEmail({ body: {
      name: process.env.OWNER_NAME, email: process.env.OWNER_EMAIL,
      username: process.env.OWNER_USERNAME, password: process.env.OWNER_PASSWORD,
    } });
    console.log(`OWNER_USER_ID=${result.user.id}`);
  }
} catch {
  // Upstream database/auth exceptions can contain secrets; keep provisioning output generic.
  console.error("Provisioning failed. Check configuration, database access, and whether an owner already exists.");
  process.exitCode = 1;
} finally { await pool.end(); }
