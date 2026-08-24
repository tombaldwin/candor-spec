#!/usr/bin/env node
/**
 * PART 67's MCP ARM — drive candor-ts's `candor_gate` tool over its REAL stdio JSON-RPC transport and
 * assert that the ⟨0.32⟩ unread-code refusal reaches it.
 *
 * WHY A SEPARATE ROUTE IS PROBED AT ALL. `candor_gate` calls `loadGateReport`, the same reader the CLI's
 * `gate --report` uses, so it was BELIEVED to inherit ⟨0.32⟩ for free. "Believed to inherit" is exactly
 * what was said about candor-ts enforcing this rule on both of its CLI routes, and that turned out false
 * — PART 62's ts row records the pre-fix measurement, `scan=2 gate--report=0`. A shared helper is a
 * reason to expect inheritance, never evidence of it: the CLI defect was not in the reader either, it
 * was in the caller that ignored what the reader returned.
 *
 * WHAT IS ASSERTED, and why not the exact document. This surface has no exit code, so the claim lives in
 * the JSON the tool returns:
 *
 *   over a report whose producer never opened an excluded class   `ok` is NOT true, `incomplete` is true,
 *                                                                 and `unread` NAMES the class
 *   over the same tree scanned WITH the policy (`peeked: true`)   `ok` is true, with no `incomplete`
 *                                                                 and no `unread`
 *
 * The second half is the over-charge control and it is not optional: `ok !== true` alone is satisfied by
 * a tool that refuses everything, which passes the arm while deleting the surface. `ok` is checked as
 * "not true" rather than pinned to `false` or to absence deliberately — ⟨0.24⟩ omits the field on the
 * ADVISORY verbs and this one mirrors the GATE, whose `--gate-json` document carries `ok: false`; which
 * of the two spellings this tool owes is a shape question §3.1 settles elsewhere, and pinning a guess
 * here would redden this part for a divergence it is not about. What it must never do is certify.
 *
 *     node mcp_gate_probe.mjs <mcp.mjs> <unread-prefix> <peeked-prefix> <policy>
 *     exit 0 = both halves hold · exit 1 = the reason, on stdout, ready to paste into the row
 */
import { spawn } from "node:child_process";

const [, , mcpPath, unreadPrefix, peekedPrefix, policy] = process.argv;
if (!mcpPath || !unreadPrefix || !peekedPrefix || !policy) {
  console.log("usage: mcp_gate_probe.mjs <mcp.mjs> <unread-prefix> <peeked-prefix> <policy>");
  process.exit(1);
}

// One session per report: CANDOR_REPORT is read at startup, which is also how a real agent runs it.
// A 20s deadline so a server that never answers lands as a named failure rather than a stalled suite —
// the same posture test-lsp.mjs takes, for the same reason.
function gateOver(report) {
  return new Promise((resolve) => {
    const srv = spawn("node", [mcpPath], { env: { ...process.env, CANDOR_REPORT: report } });
    const timer = setTimeout(() => { srv.kill("SIGKILL"); resolve({ error: "no reply within 20s" }); }, 20000);
    let buf = "", replies = [], stderr = "";
    srv.stderr.on("data", (d) => { stderr += d; });
    srv.on("error", (e) => { clearTimeout(timer); resolve({ error: `could not spawn: ${e.message}` }); });
    srv.on("exit", () => { clearTimeout(timer); if (!replies.length) resolve({ error: `server exited with no reply (stderr: ${stderr.slice(0, 200)})` }); });
    srv.stdout.on("data", (d) => {
      buf += d;
      let nl;
      while ((nl = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, nl).trim(); buf = buf.slice(nl + 1);
        if (!line) continue;
        try { replies.push(JSON.parse(line)); } catch { /* not a frame */ }
        if (replies.length >= 2) {
          clearTimeout(timer);
          srv.stdin.end();
          const r = replies.find((x) => x.id === 2);
          const text = r?.result?.content?.[0]?.text;
          if (typeof text !== "string") return resolve({ error: `no tool text in the reply: ${JSON.stringify(r).slice(0, 200)}` });
          try { return resolve({ doc: JSON.parse(text) }); }
          catch { return resolve({ error: `the tool's text is not JSON: ${text.slice(0, 200)}` }); }
        }
      }
    });
    for (const req of [
      { jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2025-06-18" } },
      { jsonrpc: "2.0", id: 2, method: "tools/call", params: { name: "candor_gate", arguments: { policy } } },
    ]) srv.stdin.write(JSON.stringify(req) + "\n");
  });
}

const fails = [];
const unread = await gateOver(unreadPrefix);
if (unread.error) fails.push(`over the unread report: ${unread.error}`);
else {
  const d = unread.doc;
  if (d.ok === true) fails.push(`over the unread report the tool CERTIFIED (\`ok: true\`) — the CLI gate exits 2 on these bytes: ${JSON.stringify(d).slice(0, 200)}`);
  if (d.incomplete !== true) fails.push(`over the unread report \`incomplete\` is ${JSON.stringify(d.incomplete)}, not true — the verdict is not marked as un-greenable`);
  if (!Array.isArray(d.unread) || d.unread.length === 0)
    fails.push(`over the unread report \`unread\` is ${JSON.stringify(d.unread)} — the tool's own contract says the key beside \`incomplete\` names which cause fired, and a refusal that does not name its class cannot be acted on`);
}
const peeked = await gateOver(peekedPrefix);
if (peeked.error) fails.push(`over the peeked control: ${peeked.error}`);
else {
  const d = peeked.doc;
  // THE OVER-CHARGE CONTROL — same tree, scanned WITH the policy, nothing unread. A tool that refuses
  // here refuses everything, and would pass the three checks above having deleted itself.
  if (d.ok !== true) fails.push(`the OVER-CHARGE CONTROL moved: over the peeked report (same tree, scanned WITH the policy, no Exec anywhere) the tool answered ${JSON.stringify(d).slice(0, 200)} instead of \`ok: true\``);
  if (d.incomplete !== undefined || d.unread !== undefined)
    fails.push(`the peeked control carries ${JSON.stringify({ incomplete: d.incomplete, unread: d.unread })} — a complete report must not be hedged, or the disclosure means nothing where it fires`);
}

if (fails.length) { console.log(fails.join(" | ")); process.exit(1); }
process.exit(0);
