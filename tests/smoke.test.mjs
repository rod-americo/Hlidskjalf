
import test from "node:test";
import assert from "node:assert/strict";
import { main } from "../hlidskjalf/main.mjs";


test("main returns zero", () => {
  assert.equal(main(), 0);
});
