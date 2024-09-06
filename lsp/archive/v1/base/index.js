// ----- IMPORTS -----

const { createConnection, TextDocuments, ProposedFeatures } = require('vscode-languageserver');
const { DiagnosticSeverity } = require('vscode-languageserver');
const connection = createConnection(ProposedFeatures.all);
const documents = new TextDocuments();

// ----- SPECIFICATION OF CHECKS -----
    // struct braces
    // scope definition
    // section number
    // period of imprisonment
    // valid keywords
    // variable names
    // punishment format
    // unclosed scope
    // validate string literals

function checkStructBraces(line, i) {
    const diagnostics = [];
    if (line.trim().startsWith('struct')) {
        const openBraces = (line.match(/{/g) || []).length;
        const closeBraces = (line.match(/}/g) || []).length;
        if (openBraces !== closeBraces) {
            diagnostics.push({
                severity: DiagnosticSeverity.Error,
                range: {
                    start: { line: i, character: 0 },
                    end: { line: i, character: line.length }
                },
                message: 'Mismatched braces in struct definition.',
                source: 'yuho'
            });
        }
    }
    return diagnostics;
}

function checkScopeDefinition(line, i) {
    const diagnostics = [];
    if (line.includes('scope') && !line.trim().endsWith('{')) {
        diagnostics.push({
            severity: DiagnosticSeverity.Error,
            range: {
                start: { line: i, character: 0 },
                end: { line: i, character: line.length }
            },
            message: 'Scope definition must end with an opening brace `{`.',
            source: 'yuho'
        });
    }
    return diagnostics;
}

function validateSectionNumber(line, i) {
    const diagnostics = [];
    if (line.includes('sectionNumber')) {
        const match = line.match(/sectionNumber\s*:=\s*(\d+)/);
        if (match) {
            const value = parseInt(match[1], 10);
            if (value <= 0) {
                diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: {
                        start: { line: i, character: 0 },
                        end: { line: i, character: line.length }
                    },
                    message: 'sectionNumber must be a positive integer.',
                    source: 'yuho'
                });
            }
        }
    }
    return diagnostics;
}

function validateImprisonmentDuration(line, i) {
    const diagnostics = [];
    if (line.includes('imprisonmentDuration')) {
        const match = line.match(/imprisonmentDuration\s*:=\s*([0-9]+(?:\s*year|month|day)?)/);
        if (match) {
            const duration = match[1];
            if (!/^\d+\s*(year|month|day)?$/.test(duration)) {
                diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: {
                        start: { line: i, character: 0 },
                        end: { line: i, character: line.length }
                    },
                    message: 'imprisonmentDuration must be a valid duration format.',
                    source: 'yuho'
                });
            }
        }
    }
    return diagnostics;
}

function checkForValidKeywords(line, i) {
    const validKeywords = ['struct', 'scope', 'punishment', 'int', 'string', 'duration', 'pass', 'fine'];
    const diagnostics = [];
    validKeywords.forEach(keyword => {
        if (line.includes(keyword)) {
            // Optional: Add additional checks for keyword usage
        }
    });
    return diagnostics;
}

function checkVariableNaming(line, i) {
    const diagnostics = [];
    const match = line.match(/(\w+)\s*:=\s*(.*)/);
    if (match) {
        const variableName = match[1];
        if (!/^[a-z][a-zA-Z0-9]*$/.test(variableName)) {
            diagnostics.push({
                severity: DiagnosticSeverity.Warning,
                range: {
                    start: { line: i, character: 0 },
                    end: { line: i, character: line.length }
                },
                message: 'Variable names should be in camelCase.',
                source: 'yuho'
            });
        }
    }
    return diagnostics;
}

function validatePunishmentFormat(line, i) {
    const diagnostics = [];
    if (line.includes('punishment')) {
        const match = line.match(/punishment\s*{\s*(.*?)(?:\s*}\s*)/s);
        if (match) {
            const content = match[1];
            if (!/duration\s+imprisonmentDuration\s*,\s*pass\s*\|\s*money\s+fine\s*,\s*pass\s*\|\s*string\s+supplementaryPunishment\s*/.test(content)) {
                diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: {
                        start: { line: i, character: 0 },
                        end: { line: i, character: line.length }
                    },
                    message: 'Punishment format is invalid.',
                    source: 'yuho'
                });
            }
        }
    }
    return diagnostics;
}

function checkForUnclosedScopes(text) {
    const diagnostics = [];
    const lines = text.split(/\r?\n/);
    let scopeDepth = 0;

    lines.forEach((line, i) => {
        if (line.includes('{')) {
            scopeDepth++;
        }
        if (line.includes('}')) {
            scopeDepth--;
        }
        if (scopeDepth < 0) {
            diagnostics.push({
                severity: DiagnosticSeverity.Error,
                range: {
                    start: { line: i, character: 0 },
                    end: { line: i, character: line.length }
                },
                message: 'Unmatched closing brace `}`.',
                source: 'yuho'
            });
        }
    });

    if (scopeDepth > 0) {
        diagnostics.push({
            severity: DiagnosticSeverity.Error,
            range: {
                start: { line: lines.length - 1, character: 0 },
                end: { line: lines.length - 1, character: lines[lines.length - 1].length }
            },
            message: 'Unclosed scope `{`.',
            source: 'yuho'
        });
    }

    return diagnostics;
}

function validateStringLiterals(line, i) {
    const diagnostics = [];
    if (/["']/.test(line)) {
        const match = line.match(/(["'])(.*)\1/);
        if (match) {
            const content = match[2];
            if (/[\n\r]/.test(content)) {
                diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: {
                        start: { line: i, character: 0 },
                        end: { line: i, character: line.length }
                    },
                    message: 'String literals should not contain newline characters.',
                    source: 'yuho'
                });
            }
        }
    }
    return diagnostics;
}

function validateTextDocument(textDocument) {

    const diagnostics = [];
    const lines = textDocument.getText().split(/\r?\n/);

    lines.forEach((line, i) => {
        diagnostics.push(...checkStructBraces(line, i));
        diagnostics.push(...checkScopeDefinition(line, i));
        diagnostics.push(...validateSectionNumber(line, i));
        diagnostics.push(...validateImprisonmentDuration(line, i));
        diagnostics.push(...checkForValidKeywords(line, i));
        diagnostics.push(...checkVariableNaming(line, i));
        diagnostics.push(...validatePunishmentFormat(line, i));
        diagnostics.push(...checkForUnclosedScopes(line, i));
        diagnostics.push(...validateStringLiterals(line, i));
    });

    connection.sendDiagnostics({ uri: textDocument.uri, diagnostics });

}

// ----- ACTUAL EXECUTION CODE -----

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

connection.listen();
