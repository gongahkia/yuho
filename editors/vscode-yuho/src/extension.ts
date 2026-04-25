// Yuho VS Code extension — activates the LSP, registers commands, and
// surfaces L1/L2/L3 coverage in the status bar.

import {
  Event,
  EventEmitter,
  ExtensionContext,
  StatusBarAlignment,
  StatusBarItem,
  ThemeColor,
  ThemeIcon,
  TreeDataProvider,
  TreeItem,
  TreeItemCollapsibleState,
  Uri,
  commands,
  env,
  window,
  workspace,
} from "vscode";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  TransportKind,
} from "vscode-languageclient/node";
import * as path from "path";
import * as fs from "fs";
import * as cp from "child_process";

let client: LanguageClient | undefined;
let statusBar: StatusBarItem | undefined;

// -------------------------------------------------------------------------
// Activation
// -------------------------------------------------------------------------

export async function activate(context: ExtensionContext): Promise<void> {
  const config = workspace.getConfiguration("yuho");

  // 1. Launch the LSP server (`yuho lsp`) if enabled.
  if (config.get<boolean>("lsp.enabled", true)) {
    await startLsp(context, config);
  }

  // 2. Register commands.
  const treeProvider = new YuhoLibraryTreeProvider();
  context.subscriptions.push(
    commands.registerTextEditorCommand("yuho.openSSO", openSSO),
    commands.registerCommand("yuho.check", runCheck),
    commands.registerCommand("yuho.transpileMermaid", () => runTranspile("mermaid")),
    commands.registerCommand("yuho.transpileEnglish", () => runTranspile("english")),
    commands.registerCommand("yuho.showCoverage", showCoverage),
    commands.registerCommand("yuho.openLibrarySection", openLibrarySection),
    commands.registerCommand("yuho.refreshTreeView", () => treeProvider.refresh()),
    window.registerTreeDataProvider("yuho.libraryTree", treeProvider),
  );

  // 3. Status bar: L3 coverage summary.
  statusBar = window.createStatusBarItem(StatusBarAlignment.Right, 100);
  statusBar.command = "yuho.showCoverage";
  context.subscriptions.push(statusBar);
  refreshStatusBar();

  const refreshOnCoverageChange = workspace.onDidSaveTextDocument((doc) => {
    if (doc.fileName.endsWith("coverage.json") || doc.fileName.endsWith(".yh")) {
      refreshStatusBar();
    }
  });
  context.subscriptions.push(refreshOnCoverageChange);
}

// -------------------------------------------------------------------------
// Deactivation
// -------------------------------------------------------------------------

export async function deactivate(): Promise<void> {
  if (client) await client.stop();
}

// -------------------------------------------------------------------------
// LSP
// -------------------------------------------------------------------------

async function startLsp(
  context: ExtensionContext,
  config: ReturnType<typeof workspace.getConfiguration>,
): Promise<void> {
  // Resolution order for the `yuho` binary:
  //   1. Explicit user override via `yuho.lsp.command` setting.
  //   2. `<workspaceFolder>/.venv-lsp/bin/yuho` (the project's bundled
  //      Python-3.12 venv that has pygls installed).
  //   3. `yuho` on PATH.
  const explicit = config.get<string>("lsp.command", "");
  let command = explicit;
  if (!command) {
    const folder = (workspace.workspaceFolders ?? [])[0];
    if (folder) {
      const venv = path.join(folder.uri.fsPath, ".venv-lsp", "bin", "yuho");
      if (fs.existsSync(venv)) {
        command = venv;
      }
    }
    if (!command) {
      command = "yuho";
    }
  }
  const args = config.get<string[]>("lsp.args", ["lsp"]);

  const serverOptions: ServerOptions = {
    run: { command, args, transport: TransportKind.stdio },
    debug: { command, args, transport: TransportKind.stdio },
  };

  const clientOptions: LanguageClientOptions = {
    documentSelector: [{ scheme: "file", language: "yuho" }],
    synchronize: {
      fileEvents: workspace.createFileSystemWatcher("**/*.yh"),
    },
  };

  client = new LanguageClient("yuho", "Yuho LSP", serverOptions, clientOptions);
  try {
    await client.start();
    context.subscriptions.push({ dispose: () => client?.stop() });
  } catch (err) {
    window.showWarningMessage(
      `Yuho LSP failed to start (is \`${command}\` on PATH?). ` +
        `Set yuho.lsp.enabled = false to silence, or yuho.lsp.command to the full path.`,
    );
  }
}

// -------------------------------------------------------------------------
// Command: Open SSO page for section under cursor
// -------------------------------------------------------------------------

async function openSSO(): Promise<void> {
  const editor = window.activeTextEditor;
  if (!editor || editor.document.languageId !== "yuho") return;
  const text = editor.document.getText();

  // First try to pull the anchor from a @meta source line
  const metaMatch = text.match(
    /@meta\s+source=(https:\/\/sso\.agc\.gov\.sg\/Act\/[^\s]+)/,
  );
  if (metaMatch) {
    env.openExternal(Uri.parse(metaMatch[1]));
    return;
  }

  // Fall back to `statute N "..."` — synthesise the PC anchor.
  const stMatch = text.match(/statute\s+(\d+[A-Za-z]*)/);
  if (stMatch) {
    const num = stMatch[1];
    const url = `https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr${num}-#pr${num}-`;
    env.openExternal(Uri.parse(url));
    return;
  }

  window.showInformationMessage("Yuho: no section number detected in this file.");
}

// -------------------------------------------------------------------------
// Command: run `yuho check` on the active file
// -------------------------------------------------------------------------

async function runCheck(): Promise<void> {
  const editor = window.activeTextEditor;
  if (!editor) return;
  const file = editor.document.fileName;
  if (!file.endsWith(".yh")) {
    window.showWarningMessage("Yuho: active file is not a .yh file.");
    return;
  }
  await editor.document.save();
  const cmd = workspace.getConfiguration("yuho").get<string>("lsp.command", "yuho");
  cp.exec(`"${cmd}" check "${file}"`, (err, stdout, stderr) => {
    const out = (stdout || "") + (stderr || "");
    if (err) {
      window.showErrorMessage(`yuho check failed:\n${out.trim().split("\n")[0]}`);
    } else {
      window.showInformationMessage(`yuho check: ${out.trim().split("\n")[0]}`);
    }
  });
}

// -------------------------------------------------------------------------
// Command: transpile + preview (mermaid/english)
// -------------------------------------------------------------------------

async function runTranspile(target: string): Promise<void> {
  const editor = window.activeTextEditor;
  if (!editor) return;
  const file = editor.document.fileName;
  if (!file.endsWith(".yh")) return;
  await editor.document.save();
  const cmd = workspace.getConfiguration("yuho").get<string>("lsp.command", "yuho");
  cp.exec(`"${cmd}" transpile -t ${target} "${file}"`, async (err, stdout) => {
    if (err) {
      window.showErrorMessage(`yuho transpile ${target} failed.`);
      return;
    }
    const doc = await workspace.openTextDocument({
      content: stdout,
      language: target === "mermaid" ? "mermaid" : "plaintext",
    });
    await window.showTextDocument(doc, { preview: true, preserveFocus: false });
  });
}

// -------------------------------------------------------------------------
// Command: show coverage dashboard
// -------------------------------------------------------------------------

async function showCoverage(): Promise<void> {
  const coverage = loadCoverage();
  if (!coverage) {
    window.showWarningMessage("Yuho: coverage.json not found.");
    return;
  }
  const dashPath = path.join(
    coverage.rootDir,
    "library",
    "penal_code",
    "_coverage",
    "COVERAGE.md",
  );
  if (fs.existsSync(dashPath)) {
    const doc = await workspace.openTextDocument(dashPath);
    await window.showTextDocument(doc, { preview: true });
  } else {
    window.showInformationMessage(
      `Yuho coverage: raw=${coverage.totals.raw_sections}, ` +
        `L1=${coverage.totals.L1_pass}, L2=${coverage.totals.L2_pass}, ` +
        `L3=${coverage.totals.L3_pass}.`,
    );
  }
}

// -------------------------------------------------------------------------
// Status bar helpers
// -------------------------------------------------------------------------

type CoverageSnapshot = {
  rootDir: string;
  totals: { raw_sections: number; L1_pass: number; L2_pass: number; L3_pass: number };
};

function loadCoverage(): CoverageSnapshot | undefined {
  for (const folder of workspace.workspaceFolders ?? []) {
    const root = folder.uri.fsPath;
    const covPath = path.join(root, "library", "penal_code", "_coverage", "coverage.json");
    if (fs.existsSync(covPath)) {
      try {
        const parsed = JSON.parse(fs.readFileSync(covPath, "utf-8"));
        return { rootDir: root, totals: parsed.totals };
      } catch {
        // fall through
      }
    }
  }
  return undefined;
}

function refreshStatusBar(): void {
  if (!statusBar) return;
  const cov = loadCoverage();
  if (!cov) {
    statusBar.hide();
    return;
  }
  const { L1_pass, L2_pass, L3_pass, raw_sections } = cov.totals;
  statusBar.text = `$(book) Yuho L1 ${L1_pass}/${raw_sections} · L2 ${L2_pass}/${raw_sections} · L3 ${L3_pass}/${raw_sections}`;
  statusBar.tooltip = "Click to open the coverage dashboard";
  statusBar.show();
}

// -------------------------------------------------------------------------
// Tree view: library browser
// -------------------------------------------------------------------------

type SectionRow = {
  number: string;
  title: string;
  L1: boolean;
  L2: boolean;
  L3: string; // "stamped" | "flagged" | "unstamped"
  yhPath: string;
};

class YuhoLibraryTreeProvider implements TreeDataProvider<SectionRow> {
  private _onDidChangeTreeData: EventEmitter<SectionRow | undefined | void> =
    new EventEmitter<SectionRow | undefined | void>();
  readonly onDidChangeTreeData: Event<SectionRow | undefined | void> =
    this._onDidChangeTreeData.event;

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(row: SectionRow): TreeItem {
    const item = new TreeItem(`s${row.number}`, TreeItemCollapsibleState.None);
    item.description = row.title;
    item.tooltip = `s${row.number} — ${row.title}\nL1=${row.L1 ? "✓" : "✗"} L2=${row.L2 ? "✓" : "✗"} L3=${row.L3}`;
    item.command = {
      title: "Open",
      command: "yuho.openLibrarySection",
      arguments: [row.yhPath],
    };
    if (row.L3 === "stamped") item.iconPath = new ThemeIcon("pass", new ThemeColor("testing.iconPassed"));
    else if (row.L3 === "flagged") item.iconPath = new ThemeIcon("warning", new ThemeColor("testing.iconFailed"));
    else item.iconPath = new ThemeIcon("circle-outline");
    return item;
  }

  getChildren(): SectionRow[] {
    return loadIndexRows();
  }
}

function loadIndexRows(): SectionRow[] {
  const folder = (workspace.workspaceFolders ?? [])[0];
  if (!folder) return [];
  const root = folder.uri.fsPath;
  const indexPath = path.join(root, "library", "penal_code", "_corpus", "index.json");
  if (!fs.existsSync(indexPath)) return [];
  try {
    const j = JSON.parse(fs.readFileSync(indexPath, "utf-8"));
    return (j.sections || []).map((r: any): SectionRow => {
      // Resolve yh path by guessing the section dir naming convention.
      const dirs = fs.readdirSync(path.join(root, "library", "penal_code"))
        .filter((n) => n.startsWith(`s${r.number}_`) || n === `s${r.number}`);
      const yhPath = dirs.length
        ? path.join(root, "library", "penal_code", dirs[0], "statute.yh")
        : "";
      return {
        number: String(r.number),
        title: r.title || "",
        L1: !!r.L1,
        L2: !!r.L2,
        L3: r.L3 || "unstamped",
        yhPath,
      };
    });
  } catch {
    return [];
  }
}

async function openLibrarySection(yhPath: string): Promise<void> {
  if (!yhPath || !fs.existsSync(yhPath)) {
    window.showWarningMessage(`Yuho: section file not found.`);
    return;
  }
  const doc = await workspace.openTextDocument(yhPath);
  await window.showTextDocument(doc, { preview: false });
}
