import { writeFileSync } from "fs";
export function save(p: string): void { writeFileSync(p, ""); }
export function add(a: number, b: number): number { return a + b; }
