use tower_lsp::jsonrpc::Result;
use tower_lsp::lsp_types::*;
use tower_lsp::{Client, LanguageServer, LspService, Server};

#[derive(Debug)]
struct YuhoLanguageServer {
    client: Client,
}

#[tower_lsp::async_trait]
impl LanguageServer for YuhoLanguageServer {
    async fn initialize(&self, _: InitializeParams) -> Result<InitializeResult> {
        Ok(InitializeResult {
            capabilities: ServerCapabilities {
                text_document_sync: Some(TextDocumentSyncCapability::Kind(
                    TextDocumentSyncKind::FULL,
                )),
                diagnostic_provider: Some(DiagnosticServerCapabilities::Options(
                    DiagnosticOptions {
                        identifier: Some("yuho".to_string()),
                        inter_file_dependencies: false,
                        workspace_diagnostics: false,
                        work_done_progress_options: WorkDoneProgressOptions::default(),
                    },
                )),
                hover_provider: Some(HoverProviderCapability::Simple(true)),
                completion_provider: Some(CompletionOptions {
                    trigger_characters: Some(vec![".".to_string(), ":".to_string()]),
                    ..Default::default()
                }),
                definition_provider: Some(OneOf::Left(true)),
                document_symbol_provider: Some(OneOf::Left(true)),
                code_action_provider: Some(CodeActionProviderCapability::Simple(true)),
                semantic_tokens_provider: Some(
                    SemanticTokensServerCapabilities::SemanticTokensOptions(
                        SemanticTokensOptions {
                            work_done_progress_options: WorkDoneProgressOptions::default(),
                            legend: SemanticTokensLegend {
                                token_types: vec![
                                    SemanticTokenType::KEYWORD,
                                    SemanticTokenType::TYPE,
                                    SemanticTokenType::VARIABLE,
                                    SemanticTokenType::FUNCTION,
                                    SemanticTokenType::STRUCT,
                                    SemanticTokenType::ENUM,
                                    SemanticTokenType::PROPERTY,
                                    SemanticTokenType::OPERATOR,
                                    SemanticTokenType::NUMBER,
                                    SemanticTokenType::STRING,
                                    SemanticTokenType::COMMENT,
                                ],
                                token_modifiers: vec![
                                    SemanticTokenModifier::DECLARATION,
                                    SemanticTokenModifier::DEFINITION,
                                    SemanticTokenModifier::READONLY,
                                ],
                            },
                            range: Some(false),
                            full: Some(SemanticTokensFullOptions::Bool(true)),
                        },
                    ),
                ),
                ..Default::default()
            },
            ..Default::default()
        })
    }

    async fn initialized(&self, _: InitializedParams) {
        self.client
            .log_message(MessageType::INFO, "Yuho LSP server initialized")
            .await;
    }

    async fn shutdown(&self) -> Result<()> {
        Ok(())
    }

    async fn did_open(&self, params: DidOpenTextDocumentParams) {
        self.client
            .log_message(
                MessageType::INFO,
                format!("File opened: {}", params.text_document.uri),
            )
            .await;
        self.check_document(&params.text_document.uri, &params.text_document.text)
            .await;
    }

    async fn hover(&self, params: HoverParams) -> Result<Option<Hover>> {
        let position = params.text_document_position_params.position;
        Ok(Some(Hover {
            contents: HoverContents::Scalar(MarkedString::String(format!(
                "Yuho hover at line {}, character {}",
                position.line, position.character
            ))),
            range: None,
        }))
    }

    async fn completion(&self, _: CompletionParams) -> Result<Option<CompletionResponse>> {
        Ok(Some(CompletionResponse::Array(vec![
            CompletionItem {
                label: "struct".to_string(),
                kind: Some(CompletionItemKind::KEYWORD),
                detail: Some("Define a struct".to_string()),
                ..Default::default()
            },
            CompletionItem {
                label: "enum".to_string(),
                kind: Some(CompletionItemKind::KEYWORD),
                detail: Some("Define an enum".to_string()),
                ..Default::default()
            },
            CompletionItem {
                label: "func".to_string(),
                kind: Some(CompletionItemKind::KEYWORD),
                detail: Some("Define a function".to_string()),
                ..Default::default()
            },
            CompletionItem {
                label: "scope".to_string(),
                kind: Some(CompletionItemKind::KEYWORD),
                detail: Some("Define a scope".to_string()),
                ..Default::default()
            },
            CompletionItem {
                label: "match".to_string(),
                kind: Some(CompletionItemKind::KEYWORD),
                detail: Some("Match expression".to_string()),
                ..Default::default()
            },
        ])))
    }

    async fn goto_definition(
        &self,
        params: GotoDefinitionParams,
    ) -> Result<Option<GotoDefinitionResponse>> {
        // Basic implementation - returns the position of the identifier
        // In a full implementation, this would track symbol definitions
        let position = params.text_document_position_params.position;
        let uri = params.text_document_position_params.text_document.uri;

        Ok(Some(GotoDefinitionResponse::Scalar(Location {
            uri,
            range: Range {
                start: position,
                end: Position {
                    line: position.line,
                    character: position.character + 1,
                },
            },
        })))
    }

    async fn document_symbol(
        &self,
        params: DocumentSymbolParams,
    ) -> Result<Option<DocumentSymbolResponse>> {
        // Parse the document and extract symbols
        // For now, return empty - full implementation would parse and extract structs/enums/funcs
        let _ = params;

        Ok(Some(DocumentSymbolResponse::Flat(vec![
            SymbolInformation {
                name: "Example Symbol".to_string(),
                kind: SymbolKind::STRUCT,
                tags: None,
                #[allow(deprecated)]
                deprecated: None,
                location: Location {
                    uri: params.text_document.uri,
                    range: Range {
                        start: Position {
                            line: 0,
                            character: 0,
                        },
                        end: Position {
                            line: 0,
                            character: 1,
                        },
                    },
                },
                container_name: None,
            },
        ])))
    }

    async fn did_change(&self, params: DidChangeTextDocumentParams) {
        if let Some(change) = params.content_changes.first() {
            self.check_document(&params.text_document.uri, &change.text)
                .await;
        }
    }

    async fn did_save(&self, params: DidSaveTextDocumentParams) {
        if let Some(text) = params.text {
            self.check_document(&params.text_document.uri, &text).await;
        }
    }

    async fn code_action(&self, params: CodeActionParams) -> Result<Option<CodeActionResponse>> {
        let mut actions = Vec::new();

        // Iterate through diagnostics and provide quick fixes
        for diagnostic in &params.context.diagnostics {
            if diagnostic.message.contains("Undefined variable") {
                // Quick fix: Suggest declaring the variable
                let action = CodeActionOrCommand::CodeAction(CodeAction {
                    title: "Declare variable".to_string(),
                    kind: Some(CodeActionKind::QUICKFIX),
                    diagnostics: Some(vec![diagnostic.clone()]),
                    edit: None, // Would need actual text edit
                    command: None,
                    is_preferred: Some(true),
                    disabled: None,
                    data: None,
                });
                actions.push(action);
            }

            if diagnostic.message.contains("Type mismatch") {
                // Quick fix: Suggest type annotation
                let action = CodeActionOrCommand::CodeAction(CodeAction {
                    title: "Add type annotation".to_string(),
                    kind: Some(CodeActionKind::QUICKFIX),
                    diagnostics: Some(vec![diagnostic.clone()]),
                    edit: None,
                    command: None,
                    is_preferred: Some(false),
                    disabled: None,
                    data: None,
                });
                actions.push(action);
            }

            if diagnostic.message.contains("Invalid BoundedInt range") {
                // Quick fix: Swap min and max
                let action = CodeActionOrCommand::CodeAction(CodeAction {
                    title: "Swap min and max values".to_string(),
                    kind: Some(CodeActionKind::QUICKFIX),
                    diagnostics: Some(vec![diagnostic.clone()]),
                    edit: None,
                    command: None,
                    is_preferred: Some(true),
                    disabled: None,
                    data: None,
                });
                actions.push(action);
            }
        }

        // Add refactoring actions
        let refactor_action = CodeActionOrCommand::CodeAction(CodeAction {
            title: "Extract to function".to_string(),
            kind: Some(CodeActionKind::REFACTOR),
            diagnostics: None,
            edit: None,
            command: None,
            is_preferred: Some(false),
            disabled: None,
            data: None,
        });
        actions.push(refactor_action);

        if actions.is_empty() {
            Ok(None)
        } else {
            Ok(Some(actions))
        }
    }

    async fn semantic_tokens_full(
        &self,
        params: SemanticTokensParams,
    ) -> Result<Option<SemanticTokensResult>> {
        let uri = &params.text_document.uri;

        // For a basic implementation, we return an empty token list
        // A full implementation would parse the document and generate tokens
        // based on the AST
        let _ = uri;

        Ok(Some(SemanticTokensResult::Tokens(SemanticTokens {
            result_id: None,
            data: vec![
                // Example: keyword "struct" at line 0, column 0, length 6
                // Format: [delta_line, delta_start, length, token_type, token_modifiers]
                // Would need actual parsing to generate real tokens
            ],
        })))
    }
}

impl YuhoLanguageServer {
    fn new(client: Client) -> Self {
        Self { client }
    }

    async fn check_document(&self, uri: &Url, text: &str) {
        let diagnostics = match yuho_core::parse(text) {
            Ok(program) => {
                let mut checker = yuho_check::Checker::new();
                let errors = checker.check_program(&program);

                errors
                    .iter()
                    .map(|err| Diagnostic {
                        range: Range {
                            start: Position {
                                line: 0,
                                character: 0,
                            },
                            end: Position {
                                line: 0,
                                character: 1,
                            },
                        },
                        severity: Some(DiagnosticSeverity::ERROR),
                        code: None,
                        code_description: None,
                        source: Some("yuho".to_string()),
                        message: err.to_string(),
                        related_information: None,
                        tags: None,
                        data: None,
                    })
                    .collect()
            },
            Err(err) => {
                vec![Diagnostic {
                    range: Range {
                        start: Position {
                            line: 0,
                            character: 0,
                        },
                        end: Position {
                            line: 0,
                            character: 1,
                        },
                    },
                    severity: Some(DiagnosticSeverity::ERROR),
                    code: None,
                    code_description: None,
                    source: Some("yuho".to_string()),
                    message: format!("Parse error: {}", err),
                    related_information: None,
                    tags: None,
                    data: None,
                }]
            },
        };

        self.client
            .publish_diagnostics(uri.clone(), diagnostics, None)
            .await;
    }
}

#[tokio::main]
async fn main() {
    let stdin = tokio::io::stdin();
    let stdout = tokio::io::stdout();

    let (service, socket) = LspService::new(|client| YuhoLanguageServer::new(client));

    Server::new(stdin, stdout, socket).serve(service).await;
}
