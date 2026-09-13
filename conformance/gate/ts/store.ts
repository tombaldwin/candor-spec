import { writeFileSync } from "fs";
export function save(p: string): void { writeFileSync(p, ""); }
// SOUNDNESS R411 — the DEFECT arm: a benign ALLOWED literal beside a caller-controlled write.
export function masked(p: string): void {
  writeFileSync("/var/data", "");
  writeFileSync(p, "");
}
export function add(a: number, b: number): number { return a + b; }
