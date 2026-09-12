import { betterAuth } from "better-auth";
import { bearer, username } from "better-auth/plugins";

export function authOptions(database, allowSignUp = false, env = process.env) {
  if (!env.BETTER_AUTH_SECRET || env.BETTER_AUTH_SECRET.length < 32 || env.BETTER_AUTH_SECRET.startsWith("replace-")) {
    throw new Error("Set BETTER_AUTH_SECRET to at least 32 random characters");
  }
  const url = new URL(env.BETTER_AUTH_URL);
  if (url.protocol !== "https:" && !(url.protocol === "http:" && ["127.0.0.1", "localhost", "[::1]"].includes(url.hostname))) {
    throw new Error("BETTER_AUTH_URL requires HTTPS except on loopback");
  }
  return {
    database, baseURL: env.BETTER_AUTH_URL, secret: env.BETTER_AUTH_SECRET,
    emailAndPassword: { enabled: true, disableSignUp: !allowSignUp, minPasswordLength: 12, maxPasswordLength: 128, autoSignIn: false },
    user: { modelName: "auth_user" },
    session: { modelName: "auth_session", expiresIn: 60 * 60 * 12, cookieCache: { enabled: false } },
    account: { modelName: "auth_account" },
    verification: { modelName: "auth_verification" },
    plugins: [username(), bearer()],
    // ponytail: one auth process uses memory rate limits; use database storage before adding replicas.
    rateLimit: { enabled: true, window: 60, max: 1000, customRules: { "/sign-in/username": { window: 60, max: 5 } } },
    logger: { disabled: true },
  };
}

export const createAuth = (database, allowSignUp = false, env = process.env) => betterAuth(authOptions(database, allowSignUp, env));
