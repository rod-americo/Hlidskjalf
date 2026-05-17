
import { loadSettings } from "./infrastructure/config.mjs";
import { logEvent } from "./infrastructure/logger.mjs";
import { assertSqliteAvailable } from "./infrastructure/sqlite-cli.mjs";
import { createPracticeService } from "./application/practice-service.mjs";
import { createHttpServer } from "./interfaces/http-server.mjs";


export function main({ startServer = false } = {}) {
  const settings = loadSettings();
  assertSqliteAvailable();
  const practiceService = createPracticeService(settings);
  logEvent({
    lvl: settings.app.logLevel,
    svc: settings.app.name,
    mod: "main",
    evt: "startup",
    msg: "service initialized"
  });
  if (!startServer) {
    return { status: 0, settings, practiceService };
  }

  const server = createHttpServer({
    practiceService,
    logger: (payload) => logEvent({ svc: settings.app.name, ...payload })
  });
  server.listen(settings.server.port, settings.server.host, () => {
    logEvent({
      lvl: settings.app.logLevel,
      svc: settings.app.name,
      mod: "http",
      evt: "listening",
      msg: `server listening on http://${settings.server.host}:${settings.server.port}`
    });
  });
  return { status: 0, settings, practiceService, server };
}


if (import.meta.url === `file://${process.argv[1]}`) {
  main({ startServer: true });
}
