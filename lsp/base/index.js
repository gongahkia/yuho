const { createConnection, TextDocuments, ProposedFeatures } = require('vscode-languageserver');

const connection = createConnection(ProposedFeatures.all);
const documents = new TextDocuments();

connection.onInitialize(() => {
    return {
        capabilities: {
            textDocumentSync: documents.syncKind,
            hoverProvider: true,
            completionProvider: { resolveProvider: true },
            definitionProvider: true,
            documentSymbolProvider: true,
            diagnosticProvider: true
        }
    };
});

documents.onDidChangeContent(change => {
    validateTextDocument(change.document);
});

function validateTextDocument(textDocument) {
    const diagnostics = [];

    // add lsp validation logic here
    //
    connection.sendDiagnostics({ uri: textDocument.uri, diagnostics });
}

connection.listen();
