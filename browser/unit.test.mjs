import assert from "node:assert/strict";
import test from "node:test";
import {
  EXPLORER_SECURITY_HEADERS,
  SECURITY_HEADERS,
  startServer,
} from "./server.mjs";

test("server exposes a fixed security policy", () => {
  assert.equal(SECURITY_HEADERS["referrer-policy"], "no-referrer");
  assert.equal(SECURITY_HEADERS["x-content-type-options"], "nosniff");
  assert.match(SECURITY_HEADERS["content-security-policy"], /connect-src 'none'/);
  assert.match(
    EXPLORER_SECURITY_HEADERS["content-security-policy"],
    /script-src 'self'/,
  );
  assert.doesNotMatch(
    EXPLORER_SECURITY_HEADERS["content-security-policy"],
    /unsafe-inline/,
  );
});

test("server allows only known GET paths", async () => {
  const server = await startServer();
  try {
    assert.equal((await fetch(server.origin)).status, 200);
    assert.equal((await fetch(`${server.origin}/fixture.css`)).status, 200);
    const explorer = await fetch(`${server.origin}/explorer`);
    assert.equal(explorer.status, 200);
    assert.match(
      explorer.headers.get("content-security-policy") ?? "",
      /script-src 'self'/,
    );
    assert.doesNotMatch(
      explorer.headers.get("content-security-policy") ?? "",
      /unsafe-inline/,
    );
    assert.equal((await fetch(`${server.origin}/explorer.css`)).status, 200);
    assert.equal((await fetch(`${server.origin}/explorer.js`)).status, 200);
    assert.equal((await fetch(`${server.origin}/../package.json`)).status, 404);
    assert.equal((await fetch(`${server.origin}/unknown`)).status, 404);
    assert.equal((await fetch(server.origin, { method: "POST" })).status, 404);
  } finally {
    await server.close();
  }
});
