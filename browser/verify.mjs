import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

const sha256 = bytes => createHash("sha256").update(bytes).digest("hex");
const exactKeys = (value, keys) => assert.deepEqual(Object.keys(value).sort(), [...keys].sort());
const reportBytes = await readFile(process.argv[2]);
const manifestBytes = await readFile(process.argv[3]);
const staticBytes = await readFile("evidence/failing-report.json");
assert(reportBytes.length <= 131_072);
assert(manifestBytes.length <= 16_384);
const report = JSON.parse(reportBytes);
const manifest = JSON.parse(manifestBytes);
exactKeys(report, ["schema", "tool_version", "provenance", "checks", "limitations"]);
exactKeys(manifest, ["schema", "browser_report_sha256", "static_report_sha256"]);
assert.equal(report.schema, "access-audit/browser-evidence/v1");
assert.equal(manifest.schema, "access-audit/combined-evidence/v1");
assert.equal(manifest.browser_report_sha256, sha256(reportBytes));
assert.equal(manifest.static_report_sha256, sha256(staticBytes));
assert.equal(report.provenance.static_report_sha256, sha256(staticBytes));
assert.equal(report.checks.network.external_request_succeeded, false);
assert.equal(report.checks.reflow.horizontal_overflow, false);
assert.equal(report.checks.reduced_motion.media_matches, true);
assert(report.limitations.includes("automated_evidence_is_not_wcag_conformance"));
const serialized = reportBytes.toString("utf8");
for (const forbidden of ["<html", "127.0.0.1", "example.invalid", "/workspace/", "file://", "exception"]) {
  assert.equal(serialized.includes(forbidden), false);
}
