import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { GoogleGenAI } from "@google/genai";
import { DEFAULT_MODEL, extractProfile } from "./profile-extraction.js";

const PUBLIC_ROOT = fileURLToPath(new URL("../public", import.meta.url));
const PORT = Number(process.env.PORT || 3000);
const MAX_AUDIO_BYTES = 12 * 1024 * 1024;
const MAX_JSON_BYTES = 32 * 1024;
const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
};

function sendJson(response, status, body) {
  response.writeHead(status, { "content-type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(body));
}

async function readBody(request, limit) {
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > limit) throw Object.assign(new Error("Request body is too large"), { status: 413 });
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}

async function transcribe(request, response) {
  const apiKey = process.env.SARVAM_API_KEY;
  if (!apiKey) return sendJson(response, 500, { error: "Server is missing SARVAM_API_KEY" });
  const receivedContentType = request.headers["content-type"] || "audio/webm";
  const contentType = receivedContentType.split(";", 1)[0].trim().toLowerCase();
  if (!contentType.startsWith("audio/") && contentType !== "video/webm") return sendJson(response, 415, { error: "Expected an audio recording" });
  const applicantId = request.headers["x-applicant-id"]?.trim();
  if (!applicantId || applicantId.length > 100) return sendJson(response, 400, { error: "A valid applicant ID is required" });

  try {
    const audio = await readBody(request, MAX_AUDIO_BYTES);
    if (!audio.length) return sendJson(response, 400, { error: "The recording is empty" });
    const extension = contentType.includes("ogg") ? "ogg" : contentType.includes("mp4") ? "mp4" : "webm";
    const form = new FormData();
    form.append("file", new Blob([audio], { type: contentType }), `intake.${extension}`);
    form.append("model", "saaras:v3");
    form.append("mode", "translate");
    const upstream = await fetch("https://api.sarvam.ai/speech-to-text", {
      method: "POST", headers: { "api-subscription-key": apiKey }, body: form, signal: AbortSignal.timeout(45_000),
    });
    const result = await upstream.json().catch(() => ({}));
    if (!upstream.ok) {
      console.error("Sarvam request failed", upstream.status, result);
      const retryable = upstream.status === 429 || upstream.status >= 500;
      return sendJson(response, upstream.status, { error: retryable ? "Speech processing is temporarily unavailable. Please try again." : "Sarvam could not process this recording. Please record again." });
    }
    if (!result.transcript?.trim()) return sendJson(response, 502, { error: "No speech was detected. Please record again." });
    return sendJson(response, 200, { applicant_id: applicantId, language: result.language_code || "unknown", transcript_en: result.transcript.trim() });
  } catch (error) {
    console.error(error);
    const status = error.status || (error.name === "TimeoutError" ? 504 : 500);
    return sendJson(response, status, { error: status === 504 ? "Speech processing timed out. Please try again." : error.message || "Unexpected server error" });
  }
}

async function extract(request, response) {
  if (!process.env.GEMINI_API_KEY) return sendJson(response, 500, { error: "Server is missing GEMINI_API_KEY" });
  try {
    const raw = await readBody(request, MAX_JSON_BYTES);
    let input;
    try { input = JSON.parse(raw.toString("utf8")); }
    catch { return sendJson(response, 400, { error: "Request body must be valid JSON" }); }
    const client = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
    const profile = await extractProfile(input, { client, model: process.env.GEMINI_MODEL || DEFAULT_MODEL });
    return sendJson(response, 200, profile);
  } catch (error) {
    console.error(error);
    return sendJson(response, error.status || 502, { error: error.status ? error.message : "Profile extraction failed. Please try again." });
  }
}

async function serveStatic(request, response) {
  const requestedPath = request.url === "/" ? "/index.html" : new URL(request.url, "http://localhost").pathname;
  const safePath = normalize(requestedPath).replace(/^(\.\.(\/|\\|$))+/, "");
  const filePath = join(PUBLIC_ROOT, safePath);
  if (!filePath.startsWith(PUBLIC_ROOT)) return sendJson(response, 403, { error: "Forbidden" });
  try {
    const body = await readFile(filePath);
    response.writeHead(200, { "content-type": MIME_TYPES[extname(filePath)] || "application/octet-stream", "cache-control": "no-store" });
    response.end(body);
  } catch { sendJson(response, 404, { error: "Not found" }); }
}

export function createAppServer() {
  return createServer(async (request, response) => {
    // Permissive dev/demo CORS so the separately-deployed frontend can call this
    // API cross-origin, matching Phase 5's approach.
    response.setHeader("access-control-allow-origin", "*");
    response.setHeader("access-control-allow-methods", "GET, POST, OPTIONS");
    response.setHeader("access-control-allow-headers", "content-type, x-applicant-id");
    if (request.method === "OPTIONS") {
      response.writeHead(204);
      return response.end();
    }
    if (request.method === "GET" && request.url === "/api/health") return sendJson(response, 200, { status: "ok", model: process.env.GEMINI_MODEL || DEFAULT_MODEL });
    if (request.method === "POST" && request.url === "/api/transcribe") return transcribe(request, response);
    if (request.method === "POST" && request.url === "/api/extract-profile") return extract(request, response);
    if (request.method === "GET") return serveStatic(request, response);
    return sendJson(response, 405, { error: "Method not allowed" });
  });
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  // Bind to all interfaces, not just loopback -- required for Render (and any
  // host behind a reverse proxy) to route traffic to this process.
  createAppServer().listen(PORT, "0.0.0.0", () => console.log(`Kaam Sahayak running on port ${PORT}`));
}
