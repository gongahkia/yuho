import {
  ConsoleStdout,
  File,
  OpenFile,
  WASI,
  WASIProcExit,
} from "@bjorn3/browser_wasi_shim";

const encoder = new TextEncoder();
const decoder = new TextDecoder("utf-8", { fatal: false });

export async function checkSource(wasmSource, source, options = {}) {
  return runEuclidPlayground(wasmSource, {
    command: "check",
    fileName: options.fileName ?? "<playground>",
    source,
  });
}

export async function exportSource(wasmSource, source, options = {}) {
  return runEuclidPlayground(wasmSource, {
    command: "export",
    fileName: options.fileName ?? "<playground>",
    format: options.format ?? "svg",
    source,
  });
}

export async function runEuclidPlayground(wasmSource, request) {
  const stdoutChunks = [];
  const stderrChunks = [];
  const stdin = encoder.encode(JSON.stringify(request));
  const wasi = new WASI(
    ["euclid-playground-wasi"],
    [],
    [
      new OpenFile(new File(stdin, { readonly: true })),
      new ConsoleStdout((chunk) => stdoutChunks.push(chunk.slice())),
      new ConsoleStdout((chunk) => stderrChunks.push(chunk.slice())),
    ],
  );
  const instance = await instantiateEuclid(wasmSource, {
    wasi_snapshot_preview1: wasi.wasiImport,
  });

  try {
    wasi.start(instance);
  } catch (error) {
    if (!(error instanceof WASIProcExit && error.code === 0)) {
      throw error;
    }
  }

  const stderr = decodeChunks(stderrChunks).trim();
  if (stderr.length > 0) {
    throw new Error(stderr);
  }

  const stdout = decodeChunks(stdoutChunks);
  try {
    return JSON.parse(stdout);
  } catch (error) {
    throw new Error(`invalid Euclid playground response: ${stdout}`, {
      cause: error,
    });
  }
}

async function instantiateEuclid(wasmSource, imports) {
  if (wasmSource instanceof WebAssembly.Module) {
    return WebAssembly.instantiate(wasmSource, imports);
  }

  if (wasmSource instanceof Response) {
    return instantiateResponse(wasmSource, imports);
  }

  if (typeof wasmSource === "string" || wasmSource instanceof URL) {
    return instantiateResponse(await fetch(wasmSource), imports);
  }

  if (wasmSource instanceof ArrayBuffer) {
    const { instance } = await WebAssembly.instantiate(wasmSource, imports);
    return instance;
  }

  if (ArrayBuffer.isView(wasmSource)) {
    const bytes = wasmSource.buffer.slice(
      wasmSource.byteOffset,
      wasmSource.byteOffset + wasmSource.byteLength,
    );
    const { instance } = await WebAssembly.instantiate(bytes, imports);
    return instance;
  }

  throw new TypeError("wasmSource must be a URL, Response, ArrayBuffer, typed array, or WebAssembly.Module");
}

async function instantiateResponse(response, imports) {
  try {
    const { instance } = await WebAssembly.instantiateStreaming(response.clone(), imports);
    return instance;
  } catch (_error) {
    const bytes = await response.arrayBuffer();
    const { instance } = await WebAssembly.instantiate(bytes, imports);
    return instance;
  }
}

function decodeChunks(chunks) {
  const byteLength = chunks.reduce((total, chunk) => total + chunk.byteLength, 0);
  const bytes = new Uint8Array(byteLength);
  let offset = 0;

  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }

  return decoder.decode(bytes);
}
