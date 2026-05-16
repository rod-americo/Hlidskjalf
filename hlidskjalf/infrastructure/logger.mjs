
export function logEvent(payload = {}) {
  const event = {
    ts: payload.ts ?? new Date().toISOString(),
    lvl: payload.lvl ?? "INFO",
    svc: payload.svc ?? "service-name",
    mod: payload.mod ?? "main",
    evt: payload.evt ?? "log",
    msg: payload.msg ?? "",
    ...payload
  };
  process.stdout.write(`${JSON.stringify(event)}\n`);
}
