/* tslint:disable */
/* eslint-disable */
/**
 * Parse Yuho source code and return JSON AST
 */
export function parse(source: string): string;
/**
 * Check Yuho source for semantic errors
 * Returns JSON array of error messages
 */
export function check(source: string): string;
/**
 * Transpile Yuho to Mermaid diagram
 */
export function to_mermaid(source: string): string;
/**
 * Transpile Yuho to Alloy specification
 */
export function to_alloy(source: string): string;
/**
 * Transpile Yuho to JSON
 */
export function to_json(source: string): string;
/**
 * Transpile Yuho to LaTeX
 */
export function to_latex(source: string): string;
/**
 * Transpile Yuho to natural English
 */
export function to_english(source: string): string;
/**
 * Transpile Yuho to TypeScript type definitions
 */
export function to_typescript(source: string): string;
/**
 * Get version information
 */
export function version(): string;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
  readonly memory: WebAssembly.Memory;
  readonly parse: (a: number, b: number) => [number, number, number, number];
  readonly check: (a: number, b: number) => [number, number, number, number];
  readonly to_mermaid: (a: number, b: number) => [number, number, number, number];
  readonly to_alloy: (a: number, b: number) => [number, number, number, number];
  readonly to_json: (a: number, b: number) => [number, number, number, number];
  readonly to_latex: (a: number, b: number) => [number, number, number, number];
  readonly to_english: (a: number, b: number) => [number, number, number, number];
  readonly to_typescript: (a: number, b: number) => [number, number, number, number];
  readonly version: () => [number, number];
  readonly __wbindgen_externrefs: WebAssembly.Table;
  readonly __wbindgen_malloc: (a: number, b: number) => number;
  readonly __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
  readonly __externref_table_dealloc: (a: number) => void;
  readonly __wbindgen_free: (a: number, b: number, c: number) => void;
  readonly __wbindgen_start: () => void;
}

export type SyncInitInput = BufferSource | WebAssembly.Module;
/**
* Instantiates the given `module`, which can either be bytes or
* a precompiled `WebAssembly.Module`.
*
* @param {{ module: SyncInitInput }} module - Passing `SyncInitInput` directly is deprecated.
*
* @returns {InitOutput}
*/
export function initSync(module: { module: SyncInitInput } | SyncInitInput): InitOutput;

/**
* If `module_or_path` is {RequestInfo} or {URL}, makes a request and
* for everything else, calls `WebAssembly.instantiate` directly.
*
* @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
*
* @returns {Promise<InitOutput>}
*/
export default function __wbg_init (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;
