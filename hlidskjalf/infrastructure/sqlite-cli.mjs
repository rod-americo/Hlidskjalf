import { spawnSync } from "node:child_process";


function quoteSqlValue(value) {
  return `'${String(value).replaceAll("'", "''")}'`;
}


export function assertSqliteAvailable() {
  const result = spawnSync("sqlite3", ["-version"], { encoding: "utf-8" });
  if (result.status !== 0) {
    throw new Error("sqlite3 command not available");
  }
}


export function runSql(dbPath, sql) {
  const result = spawnSync("sqlite3", [dbPath, sql], { encoding: "utf-8" });
  if (result.status !== 0) {
    const detail = result.stderr.trim() || result.stdout.trim() || "unknown sqlite error";
    throw new Error(detail);
  }
  return result.stdout;
}


export function queryJson(dbPath, sql) {
  const result = spawnSync("sqlite3", ["-json", dbPath, sql], { encoding: "utf-8" });
  if (result.status !== 0) {
    const detail = result.stderr.trim() || result.stdout.trim() || "unknown sqlite error";
    throw new Error(detail);
  }
  const payload = result.stdout.trim();
  return payload ? JSON.parse(payload) : [];
}


export function quoteAttachPath(path) {
  return quoteSqlValue(path);
}


export function sqlValue(value) {
  if (value === null || value === undefined) {
    return "NULL";
  }
  if (typeof value === "number") {
    return Number.isFinite(value) ? String(value) : "NULL";
  }
  return quoteSqlValue(value);
}
