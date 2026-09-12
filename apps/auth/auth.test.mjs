import assert from "node:assert/strict";
import { once } from "node:events";
import test from "node:test";
import { memoryAdapter } from "better-auth/adapters/memory";
import { createAuth, authOptions } from "./auth.mjs";
import { createAuthServer } from "./server.mjs";

test("private username login, bearer session, revocation, and public signup denial", async () => {
  const env = { BETTER_AUTH_URL: "http://127.0.0.1:3001", BETTER_AUTH_SECRET: "test-only-secret-".repeat(4) };
  const store = { auth_user: [], auth_session: [], auth_account: [], auth_verification: [] };
  const database = memoryAdapter(store);
  const provisioning = createAuth(database, true, env);
  const owner = await provisioning.api.signUpEmail({ body: { name: "Owner", email: "owner@example.com", username: "owner", password: "a-long-test-password" } });
  assert.ok(owner.user.id);
  const auth = createAuth(database, false, env);
  assert.equal(auth.options.emailAndPassword.disableSignUp, true);
  assert.throws(() => authOptions(database, false, { ...env, BETTER_AUTH_SECRET: "short" }));
  assert.throws(() => authOptions(database, false, { ...env, BETTER_AUTH_URL: "http://remote.example.com" }));
  const server = createAuthServer(auth);
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const base = `http://127.0.0.1:${server.address().port}/api/auth/`;
  const post = (path, body, token) => fetch(base + path, { method: "POST", headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: JSON.stringify(body) });
  try {
    assert.equal((await post("sign-up/email", {})).status, 404);
    assert.equal((await post("update-user", {})).status, 404);
    const login = await post("sign-in/username", { username: "owner", password: "a-long-test-password" });
    assert.equal(login.status, 200, await login.clone().text());
    assert.equal(login.headers.get("cache-control"), "no-store");
    const { token } = await login.json();
    assert.ok(token);
    const getSession = () => fetch(base + "get-session?disableCookieCache=true", { headers: { Authorization: `Bearer ${token}` } });
    const session = await (await getSession()).json();
    assert.equal(session.user.id, owner.user.id);
    const logout = await post("sign-out", {}, token);
    assert.equal(logout.status, 200, await logout.clone().text());
    assert.equal(await (await getSession()).json(), null);
    let denied;
    for (let attempt = 0; attempt < 6; attempt++) denied = await post("sign-in/username", { username: "owner", password: "wrong" });
    assert.equal(denied.status, 429);
  } finally {
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
  }
});
