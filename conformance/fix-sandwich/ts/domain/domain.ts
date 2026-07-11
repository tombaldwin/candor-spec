import { fetch } from "../infra/infra";
import { mid } from "../api/api";
export function inner(): void { fetch(); }
export function top(): void { mid(); }
