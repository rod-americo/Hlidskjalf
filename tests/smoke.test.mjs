
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { main } from "../hlidskjalf/main.mjs";
import { createPracticeService } from "../hlidskjalf/application/practice-service.mjs";


test("main initializes without starting the server", () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "hlidskjalf-main-"));
  const configPath = path.join(tempDir, "settings.json");
  fs.writeFileSync(configPath, JSON.stringify({
    questions: {
      publicDbPath: "data/questions/tps-comentado-2019-public.db",
      pilotChapterNumber: 1
    },
    progress: {
      dbPath: path.join(tempDir, "progress.db")
    }
  }));

  const previousConfig = process.env.HLIDSKJALF_CONFIG_FILE;
  process.env.HLIDSKJALF_CONFIG_FILE = configPath;
  try {
    const result = main();
    assert.equal(result.status, 0);
    assert.ok(result.practiceService);
  } finally {
    if (previousConfig === undefined) {
      delete process.env.HLIDSKJALF_CONFIG_FILE;
    } else {
      process.env.HLIDSKJALF_CONFIG_FILE = previousConfig;
    }
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
});


test("practice service loads and grades a Portuguese question", () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "hlidskjalf-practice-"));
  const settings = {
    questions: {
      publicDbPath: "data/questions/tps-comentado-2019-public.db",
      pilotChapterNumber: 1
    },
    progress: {
      dbPath: path.join(tempDir, "progress.db")
    }
  };
  try {
    const service = createPracticeService(settings);
    const question = service.nextQuestion();
    assert.equal(question.chapterNumber, 1);
    assert.ok(question.items.length > 0);

    const answers = Object.fromEntries(
      question.items
        .filter((item) => !item.is_annulled)
        .map((item) => [item.id, item.answer_normalized])
    );
    const result = service.submitAttempt({
      groupId: question.id,
      difficulty: "good",
      answers
    });
    assert.equal(result.grade.correctItems, question.items.length);
    assert.ok(result.schedule.dueAt);
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
});
