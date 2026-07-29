import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const ROOT = new URL("./", import.meta.url);
const FILES = new Map([
  ["/", ["fixture.html", "text/html; charset=utf-8"]],
  ["/fixture.css", ["fixture.css", "text/css; charset=utf-8"]],
]);
export const SECURITY_HEADERS = Object.freeze({
  "content-security-policy":
    "default-src 'none'; style-src 'self'; script-src 'unsafe-inline'; img-src 'self'; " +
    "connect-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
  "referrer-policy": "no-referrer",
  "x-content-type-options": "nosniff",
});

export async function startServer() {
  const server = createServer(async (request, response) => {
    const entry = FILES.get(request.url ?? "");
    if (request.method !== "GET" || entry === undefined) {
      response.writeHead(404, SECURITY_HEADERS);
      response.end("Not found");
      return;
    }
    const [relativePath, contentType] = entry;
    const body = await readFile(fileURLToPath(new URL(relativePath, ROOT)));
    response.writeHead(200, { ...SECURITY_HEADERS, "content-type": contentType });
    response.end(body);
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const address = server.address();
  if (address === null || typeof address === "string") throw new Error("server-address");
  return {
    origin: `http://127.0.0.1:${address.port}`,
    close: () => new Promise((resolve, reject) =>
      server.close(error => error ? reject(error) : resolve())),
  };
}
