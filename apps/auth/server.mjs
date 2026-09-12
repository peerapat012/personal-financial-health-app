import { createServer } from "node:http";
import { pathToFileURL } from "node:url";
import { toNodeHandler } from "better-auth/node";
import { Pool } from "pg";
import { createAuth } from "./auth.mjs";

export function createAuthServer(auth) {
  const handle = toNodeHandler(auth);
  const allowed = new Set(["POST /api/auth/sign-in/username", "GET /api/auth/get-session", "POST /api/auth/sign-out"]);
  return createServer({ maxHeaderSize: 8192, requestTimeout: 10_000 }, async (request, response) => {
    response.setHeader("Cache-Control", "no-store");
    const path = new URL(request.url, "http://localhost").pathname;
    if (!allowed.has(`${request.method} ${path}`)) { response.writeHead(404).end(); return; }
    if (request.method === "POST" && (request.headers["transfer-encoding"] || !/^\d+$/.test(request.headers["content-length"] ?? "") || Number(request.headers["content-length"]) > 8192)) {
      response.writeHead(413).end(); return;
    }
    // Trust the connection address, never caller-supplied forwarding headers for rate limiting.
    request.headers["x-forwarded-for"] = request.socket.remoteAddress;
    delete request.headers["x-real-ip"];
    try { await handle(request, response); }
    catch { if (!response.headersSent) response.writeHead(503); response.end(); }
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (!process.env.AUTH_DATABASE_URL) throw new Error("Set AUTH_DATABASE_URL");
  const pool = new Pool({ connectionString: process.env.AUTH_DATABASE_URL, max: 2, connectionTimeoutMillis: 5000 });
  const server = createAuthServer(createAuth(pool));
  server.listen(Number(process.env.PORT ?? 3001), process.env.HOST ?? "127.0.0.1", () => console.log("Auth service listening"));
  const stop = () => server.close(() => { void pool.end(); });
  process.on("SIGINT", stop);
  process.on("SIGTERM", stop);
}
