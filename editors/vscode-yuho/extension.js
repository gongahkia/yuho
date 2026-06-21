const fs = require("node:fs");
const path = require("node:path");
const vscode = require("vscode");
const { LanguageClient } = require("vscode-languageclient/node");

let client;

const tokenTypes = [
  "keyword",
  "type",
  "parameter",
  "variable",
  "property",
  "function",
  "method",
  "string",
  "number",
  "comment",
  "operator",
];
const tokenModifiers = [
  "declaration",
  "definition",
  "documentation",
  "readonly",
  "defaultLibrary",
];
const semanticLegend = new vscode.SemanticTokensLegend(tokenTypes, tokenModifiers);

async function activate(context) {
  const config = vscode.workspace.getConfiguration("yuho");
  registerTreeSitterHighlighting(context, config);

  const command = config.get("lsp.command", "yuho-lsp");
  const configuredArgs = config.get("lsp.args", []);
  const args = Array.isArray(configuredArgs) ? configuredArgs : [];
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  const serverOptions = {
    command,
    args,
    options: workspaceFolder ? { cwd: workspaceFolder.uri.fsPath } : undefined,
  };
  const clientOptions = {
    documentSelector: [
      { scheme: "file", language: "yuho" },
      { scheme: "untitled", language: "yuho" },
    ],
    synchronize: {
      fileEvents: vscode.workspace.createFileSystemWatcher("**/*.yh"),
    },
  };

  client = new LanguageClient("yuho", "Yuho Language Server", serverOptions, clientOptions);
  context.subscriptions.push({
    dispose: () => {
      if (client) {
        void client.stop();
      }
    },
  });
  await client.start();
}

async function deactivate() {
  if (!client) {
    return;
  }
  const activeClient = client;
  client = undefined;
  await activeClient.stop();
}

function registerTreeSitterHighlighting(context, config) {
  const provider = createTreeSitterProvider(context, config);
  if (!provider) {
    return;
  }
  context.subscriptions.push(
    vscode.languages.registerDocumentSemanticTokensProvider(
      [
        { scheme: "file", language: "yuho" },
        { scheme: "untitled", language: "yuho" },
      ],
      provider,
      semanticLegend,
    ),
  );
}

function createTreeSitterProvider(context, config) {
  try {
    const Parser = require("tree-sitter");
    const Yuho = loadYuhoTreeSitterLanguage(context, config);
    if (!Yuho) {
      return undefined;
    }
    const queryPath = context.asAbsolutePath(path.join("queries", "highlights.scm"));
    const querySource = fs.readFileSync(queryPath, "utf8");
    const parser = new Parser();
    parser.setLanguage(Yuho);
    const query = new Parser.Query(Yuho, querySource);
    return new TreeSitterSemanticTokensProvider(parser, query);
  } catch (error) {
    console.warn(`Yuho tree-sitter highlighting unavailable: ${error.message}`);
    return undefined;
  }
}

function loadYuhoTreeSitterLanguage(context, config) {
  const configuredPath = config.get("treeSitter.modulePath", "");
  const candidates = [];
  if (configuredPath) {
    candidates.push(path.resolve(configuredPath));
  }
  candidates.push(context.asAbsolutePath(path.join("..", "..", "src", "tree-sitter-yuho")));
  candidates.push("tree-sitter-yuho");

  for (const candidate of candidates) {
    try {
      return require(candidate);
    } catch (_) {}
  }
  return undefined;
}

class TreeSitterSemanticTokensProvider {
  constructor(parser, query) {
    this.parser = parser;
    this.query = query;
  }

  provideDocumentSemanticTokens(document) {
    const tree = this.parser.parse(document.getText());
    const captures = this.query.captures(tree.rootNode);
    const tokens = [];
    const seen = new Set();

    for (const capture of captures) {
      const token = tokenForCapture(capture.name);
      if (!token) {
        continue;
      }
      const start = capture.node.startPosition;
      const end = capture.node.endPosition;
      if (start.row !== end.row || end.column <= start.column) {
        continue;
      }
      const key = `${start.row}:${start.column}:${end.column}`;
      if (seen.has(key)) {
        continue;
      }
      seen.add(key);
      tokens.push({
        line: start.row,
        start: start.column,
        end: end.column,
        type: token.type,
        modifiers: token.modifiers,
        priority: token.priority,
      });
    }

    tokens.sort(
      (a, b) =>
        a.line - b.line ||
        a.start - b.start ||
        b.priority - a.priority ||
        b.end - b.start - (a.end - a.start),
    );

    const builder = new vscode.SemanticTokensBuilder(semanticLegend);
    let lastLine = -1;
    let lastEnd = 0;
    for (const token of tokens) {
      if (token.line === lastLine && token.start < lastEnd) {
        continue;
      }
      const typeIndex = tokenTypes.indexOf(token.type);
      if (typeIndex < 0) {
        continue;
      }
      builder.push(
        token.line,
        token.start,
        token.end - token.start,
        typeIndex,
        modifierBits(token.modifiers),
      );
      lastLine = token.line;
      lastEnd = token.end;
    }
    return builder.build();
  }
}

function tokenForCapture(name) {
  const parts = name.split(".");
  const base = parts[0];
  const modifiers = [];
  let priority = parts.length;
  if (parts.includes("definition")) {
    modifiers.push("definition", "declaration");
    priority += 2;
  }
  if (parts.includes("documentation")) {
    modifiers.push("documentation");
  }
  if (parts.includes("builtin")) {
    modifiers.push("defaultLibrary");
  }

  if (base === "keyword" || base === "boolean") {
    return { type: "keyword", modifiers, priority };
  }
  if (base === "type") {
    return { type: "type", modifiers, priority };
  }
  if (base === "parameter") {
    return { type: "parameter", modifiers, priority };
  }
  if (base === "variable" || base === "constant") {
    return { type: "variable", modifiers, priority };
  }
  if (base === "property") {
    return { type: "property", modifiers, priority };
  }
  if (base === "function") {
    return { type: parts.includes("method") ? "method" : "function", modifiers, priority };
  }
  if (base === "string") {
    return { type: "string", modifiers, priority };
  }
  if (base === "number") {
    return { type: "number", modifiers, priority };
  }
  if (base === "comment") {
    return { type: "comment", modifiers, priority };
  }
  if (base === "operator") {
    return { type: "operator", modifiers, priority };
  }
  return undefined;
}

function modifierBits(modifiers) {
  let bits = 0;
  for (const modifier of modifiers) {
    const index = tokenModifiers.indexOf(modifier);
    if (index >= 0) {
      bits |= 1 << index;
    }
  }
  return bits;
}

module.exports = {
  activate,
  deactivate,
};
