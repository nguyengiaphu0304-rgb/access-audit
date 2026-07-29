import assert from "node:assert/strict";
import test from "node:test";
import { SECURITY_HEADERS, startServer } from "./server.mjs";

test("server exposes a fixed security policy", () => {
  assert.equal(SECURITY_HEADERS["referrer-policy"], "no-referrer");
  assert.equal(SECURITY_HEADERS["x-content-type-options"], "nosniff");
  assert.match(SECURITY_HEADERS["content-security-policy"], /connect-src 'none'/);
});

test("server allows only known GET paths", async () => {
  const server = await startServer();
  try {
    assert.equal((await fetch(server.origin)).status, 200);
    assert.equal((await fetch(`${server.origin}/fixture.css`)).status, 200);
    assert.equal((await fetch(`${server.origin}/../package.json`)).status, 404);
    assert.equal((await fetch(`${server.origin}/unknown`)).status, 404);
    assert.equal((await fetch(server.origin, { method: "POST" })).status, 404);
  } finally {
    await server.close();
  }
});
