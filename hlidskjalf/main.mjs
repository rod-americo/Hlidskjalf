
import { loadSettings } from "./infrastructure/config.mjs";
import { logEvent } from "./infrastructure/logger.mjs";


export function main() {
  const settings = loadSettings();
  logEvent({
    lvl: settings.app.logLevel,
    svc: settings.app.name,
    mod: "main",
    evt: "startup",
    msg: "service initialized"
  });
  return 0;
}


if (import.meta.url === `file://${process.argv[1]}`) {
  process.exit(main());
}
