// Independent Node/OpenSSL fixture generator. Only the PUBLIC RFC 8032 test seed.
// Never use this seed, fixture policy, or signer in a real publication system.
import { createHash, createPrivateKey, createPublicKey, sign } from "node:crypto";
import { writeFileSync } from "node:fs";

const seed = "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60";
const key = createPrivateKey({
  key: Buffer.from("302e020100300506032b657004220420" + seed, "hex"),
  format: "der", type: "pkcs8",
});
const publicKey = createPublicKey(key).export({ format: "der", type: "spki" }).subarray(-32);
const canonical = value => {
  if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
  if (value !== null && typeof value === "object") {
    return "{" + Object.keys(value).sort().map(k =>
      JSON.stringify(k) + ":" + canonical(value[k])).join(",") + "}";
  }
  return JSON.stringify(value);
};
const hash = value => createHash("sha256").update(value).digest("hex");
const policy = {
  version: 1, contract: "xevents-publication-proof/v1", algorithm: "Ed25519",
  repository_id: 123, repository_name: "example/synthetic", base_branch: "main",
  limits: {
    body_bytes: 8192, file_bytes: 1048576, candidate_bytes: 4194304,
    scan_lifetime: 900, sign_delay: 300, clock_skew: 60,
  },
  aggregate_files: ["data/aggregates/view1.jsonl", "data/aggregates/view2.jsonl"],
  profiles: ["synthetic-v1"],
  keys: [{
    key_id: "rfc8032-test-only", public_key: publicKey.toString("base64url"),
    profiles: ["synthetic-v1"], not_before: 0, not_after: 2000000, revoked: false,
  }],
};
const files = [
  { path: "coverage-boundary-statement.md", data: "Synthetic coverage only.\n" },
  { path: "data/aggregates/view1.jsonl", data: "{\"synthetic\":true}\n" },
  { path: "evidence-manifest.jsonl", data: "{\"synthetic\":true}\n" },
];
const descriptor = { files: files.map(f => ({
  path: f.path, mode: "100644", size: Buffer.byteLength(f.data), sha256: hash(f.data),
})) };
const payload = {
  version: 1, repository_id: 123, pr_number: 7,
  base_sha: "a".repeat(40), head_sha: "b".repeat(40),
  candidate_sha256: hash(canonical(descriptor)), policy_sha256: hash(canonical(policy)),
  profile_id: "synthetic-v1", key_id: "rfc8032-test-only", proof_id: "1".repeat(32),
  scan_completed_at: 1000000, issued_at: 1000030, expires_at: 1000900,
};
const message = Buffer.from("xevents-publication-proof/v1\0" + canonical(payload));
const vector = {
  warning: "PUBLIC TEST KEY. Never use for production.",
  source: "https://www.rfc-editor.org/rfc/rfc8032#section-7.1",
  public_key_hex: publicKey.toString("hex"),
  empty_message_signature_hex: sign(null, Buffer.alloc(0), key).toString("hex"),
  policy, files, descriptor, payload,
  canonical_policy: canonical(policy), canonical_descriptor: canonical(descriptor),
  canonical_payload: canonical(payload), message_hex: message.toString("hex"),
  envelope: { payload, signature: sign(null, message, key).toString("base64url") },
};
writeFileSync(new URL("./vector.json", import.meta.url), JSON.stringify(vector, null, 2) + "\n");
