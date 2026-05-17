import http from "node:http";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";


const HERE = dirname(fileURLToPath(import.meta.url));
const STATIC_DIR = join(HERE, "static");


function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store"
  });
  response.end(JSON.stringify(payload));
}


function readRequestJson(request) {
  return new Promise((resolve, reject) => {
    let body = "";
    request.setEncoding("utf-8");
    request.on("data", (chunk) => {
      body += chunk;
      if (body.length > 1024 * 1024) {
        reject(new Error("request too large"));
        request.destroy();
      }
    });
    request.on("end", () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch {
        reject(new Error("invalid json"));
      }
    });
    request.on("error", reject);
  });
}


export function createHttpServer({ practiceService, logger }) {
  return http.createServer(async (request, response) => {
    try {
      const url = new URL(request.url, "http://localhost");

      if (request.method === "GET" && url.pathname === "/") {
        const html = readFileSync(join(STATIC_DIR, "practice.html"), "utf-8");
        response.writeHead(200, { "content-type": "text/html; charset=utf-8" });
        response.end(html);
        return;
      }

      if (request.method === "GET" && url.pathname === "/app.js") {
        const js = readFileSync(join(STATIC_DIR, "practice.js"), "utf-8");
        response.writeHead(200, { "content-type": "text/javascript; charset=utf-8" });
        response.end(js);
        return;
      }

      if (request.method === "GET" && url.pathname === "/styles.css") {
        const css = readFileSync(join(STATIC_DIR, "styles.css"), "utf-8");
        response.writeHead(200, { "content-type": "text/css; charset=utf-8" });
        response.end(css);
        return;
      }

      if (request.method === "GET" && url.pathname === "/api/next-question") {
        const question = practiceService.nextQuestion();
        sendJson(response, question ? 200 : 404, question ? { question } : { error: "no due question" });
        return;
      }

      if (request.method === "POST" && url.pathname === "/api/attempts") {
        const payload = await readRequestJson(request);
        const result = practiceService.submitAttempt(payload);
        sendJson(response, 201, result);
        return;
      }

      if (request.method === "POST" && url.pathname === "/api/corrections") {
        const payload = await readRequestJson(request);
        const result = practiceService.gradeAttempt(payload);
        sendJson(response, 200, result);
        return;
      }

      sendJson(response, 404, { error: "not found" });
    } catch (error) {
      logger?.({
        lvl: "ERROR",
        mod: "http",
        evt: "request_failed",
        msg: error.message
      });
      sendJson(response, 400, { error: error.message });
    }
  });
}
