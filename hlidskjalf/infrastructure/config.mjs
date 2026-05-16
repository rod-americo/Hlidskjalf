
import fs from "node:fs";
import process from "node:process";


function candidatePaths() {
  const envPath = process.env.HLIDSKJALF_CONFIG_FILE;
  return [envPath, "config/settings.local.json", "config/settings.example.json"].filter(Boolean);
}


export function loadSettings() {
  for (const path of candidatePaths()) {
    if (!fs.existsSync(path)) {
      continue;
    }

    const payload = JSON.parse(fs.readFileSync(path, "utf-8"));
    return {
      app: {
        name: payload.app?.name ?? "Hlidskjalf",
        env: payload.app?.env ?? process.env.NODE_ENV ?? "dev",
        logLevel: payload.app?.logLevel ?? "INFO"
      },
      questions: {
        publicDbPath: payload.questions?.publicDbPath ?? "data/questions/tps-comentado-2019-public.db"
      },
      progress: {
        dbPath: payload.progress?.dbPath ?? "runtime/question-practice/progress.db"
      },
      configPath: path
    };
  }

  return {
    app: {
      name: "Hlidskjalf",
      env: process.env.NODE_ENV ?? "dev",
      logLevel: "INFO"
    },
    questions: {
      publicDbPath: "data/questions/tps-comentado-2019-public.db"
    },
    progress: {
      dbPath: "runtime/question-practice/progress.db"
    },
    configPath: null
  };
}
