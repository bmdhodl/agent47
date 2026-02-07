import postgres from "postgres";

// Lazy-init: DATABASE_URL is validated at first query, not at import time.
// This prevents `next build` from crashing in CI where env vars aren't set.
let _sql: ReturnType<typeof postgres> | null = null;

function getSql() {
  if (!_sql) {
    if (!process.env.DATABASE_URL) {
      throw new Error("DATABASE_URL not set");
    }
    _sql = postgres(process.env.DATABASE_URL, {
      max: 10,
      idle_timeout: 20,
      connect_timeout: 10,
    });
  }
  return _sql;
}

// Tagged-template wrapper so callers keep using sql`SELECT ...` unchanged.
const sql: ReturnType<typeof postgres> = new Proxy(
  Function.prototype as unknown as ReturnType<typeof postgres>,
  {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    apply(_target, _thisArg, args: any[]) {
      const db = getSql();
      // eslint-disable-next-line @typescript-eslint/no-unsafe-function-type
      return (db as unknown as Function).apply(db, args);
    },
    get(_target, prop, receiver) {
      if (prop === Symbol.toPrimitive || prop === "then") return undefined;
      const db = getSql();
      const val = Reflect.get(db, prop, receiver);
      return typeof val === "function" ? val.bind(db) : val;
    },
  },
);

export default sql;
