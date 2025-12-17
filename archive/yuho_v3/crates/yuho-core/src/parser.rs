use crate::ast::*;
use crate::error::{Result, YuhoError};
use crate::lexer::Token;

pub struct Parser {
    tokens: Vec<(Token, std::ops::Range<usize>)>,
    pos: usize,
    quantifier_depth: usize, // Track nesting depth for validation
}

impl Parser {
    pub fn new(tokens: Vec<(Token, std::ops::Range<usize>)>) -> Self {
        Self {
            tokens,
            pos: 0,
            quantifier_depth: 0,
        }
    }

    fn current(&self) -> Option<&Token> {
        self.tokens.get(self.pos).map(|(t, _)| t)
    }

    fn current_span(&self) -> Span {
        self.tokens
            .get(self.pos)
            .map(|(_, r)| Span {
                start: r.start,
                end: r.end,
            })
            .unwrap_or(Span { start: 0, end: 0 })
    }

    fn advance(&mut self) {
        self.pos += 1;
    }

    fn expect(&mut self, expected: &Token) -> Result<()> {
        match self.current() {
            Some(t) if std::mem::discriminant(t) == std::mem::discriminant(expected) => {
                self.advance();
                Ok(())
            },
            Some(t) => Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: format!("Expected {:?}, got {:?}", expected, t),
            }),
            None => Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: format!("Expected {:?}, got EOF", expected),
            }),
        }
    }

    fn check(&self, expected: &Token) -> bool {
        match self.current() {
            Some(t) => std::mem::discriminant(t) == std::mem::discriminant(expected),
            None => false,
        }
    }

    fn is_at_end(&self) -> bool {
        self.pos >= self.tokens.len()
    }

    fn peek(&self, offset: usize) -> Option<&Token> {
        self.tokens.get(self.pos + offset).map(|(t, _)| t)
    }
}

impl Parser {
    pub fn parse_program(&mut self) -> Result<Program> {
        let mut imports = Vec::new();
        let mut items = Vec::new();

        while !self.is_at_end() {
            if self.check(&Token::Referencing) {
                imports.push(self.parse_import()?);
            } else {
                items.push(self.parse_item()?);
            }
        }

        Ok(Program { imports, items })
    }

    fn parse_import(&mut self) -> Result<ImportStatement> {
        let span_start = self.current_span().start;
        self.expect(&Token::Referencing)?;

        let mut names = Vec::new();
        if let Some(Token::Ident(name)) = self.current().cloned() {
            names.push(name);
            self.advance();
        }

        while self.check(&Token::Comma) {
            self.advance();
            if let Some(Token::Ident(name)) = self.current().cloned() {
                names.push(name);
                self.advance();
            }
        }

        self.expect(&Token::From)?;

        let from = if let Some(Token::Ident(name)) = self.current().cloned() {
            self.advance();
            name
        } else {
            return Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: "Expected module name".to_string(),
            });
        };

        let span_end = self.current_span().end;
        Ok(ImportStatement {
            names,
            from,
            span: Span {
                start: span_start,
                end: span_end,
            },
        })
    }

    fn parse_item(&mut self) -> Result<Item> {
        match self.current() {
            Some(Token::Scope) => Ok(Item::Scope(self.parse_scope()?)),
            Some(Token::Struct) => Ok(Item::Struct(self.parse_struct()?)),
            Some(Token::Enum) => Ok(Item::Enum(self.parse_enum()?)),
            Some(Token::Func) => Ok(Item::Function(self.parse_function()?)),
            Some(Token::Type) => Ok(Item::TypeAlias(self.parse_type_alias()?)),
            Some(Token::LegalTest) => Ok(Item::LegalTest(self.parse_legal_test()?)),
            Some(Token::Verify) => Ok(Item::ConflictCheck(self.parse_conflict_check()?)),
            Some(Token::Principle) => Ok(Item::Principle(self.parse_principle()?)),
            Some(Token::Proviso) | Some(Token::Provided) => Ok(Item::Proviso(self.parse_proviso()?)),
            Some(Token::Match) => {
                let m = self.parse_match()?;
                Ok(Item::Declaration(Declaration {
                    name: "_match_result".to_string(),
                    ty: Type::Pass,
                    value: Expr::Match(Box::new(m.clone())),
                    span: m.span,
                }))
            }
            // Check if this is "type func name" pattern for functions with return type
            Some(Token::TyInt) | Some(Token::TyInteger) | Some(Token::TyFloat)
            | Some(Token::TyBool) | Some(Token::TyBoolean) | Some(Token::TyString)
            | Some(Token::TyMoney) | Some(Token::TyDate) | Some(Token::TyDuration)
            | Some(Token::TyPercent)
            // Phase 1: Dependent type tokens
            | Some(Token::TyBoundedInt) | Some(Token::TyNonEmpty)
            | Some(Token::TyPositive) | Some(Token::TyValidDate) | Some(Token::TyArray)
            | Some(Token::TyCitation) | Some(Token::TyTemporal) => {
                // Look ahead to see if next token is 'func'
                if matches!(self.peek(1), Some(Token::Func)) {
                    Ok(Item::Function(self.parse_function()?))
                } else {
                    Ok(Item::Declaration(self.parse_declaration()?))
                }
            }
            Some(Token::Ident(_)) => {
                // Could be named type for declaration or function
                if matches!(self.peek(1), Some(Token::Func)) {
                    Ok(Item::Function(self.parse_function()?))
                } else {
                    Ok(Item::Declaration(self.parse_declaration()?))
                }
            }
            Some(Token::Pass) => {
                Ok(Item::Declaration(self.parse_declaration()?))
            }
            Some(t) => Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: format!("Unexpected token {:?}", t),
            }),
            None => Err(YuhoError::ParseError {
                position: 0,
                message: "Unexpected EOF".to_string(),
            }),
        }
    }

    fn parse_scope(&mut self) -> Result<ScopeDefinition> {
        let span_start = self.current_span().start;
        self.expect(&Token::Scope)?;

        let name = if let Some(Token::Ident(n)) = self.current().cloned() {
            self.advance();
            n
        } else {
            return Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: "Expected scope name".to_string(),
            });
        };

        self.expect(&Token::LBrace)?;

        let mut items = Vec::new();
        while !self.check(&Token::RBrace) && !self.is_at_end() {
            items.push(self.parse_item()?);
        }

        let span_end = self.current_span().end;
        self.expect(&Token::RBrace)?;

        Ok(ScopeDefinition {
            name,
            items,
            span: Span {
                start: span_start,
                end: span_end,
            },
        })
    }

    fn parse_struct(&mut self) -> Result<StructDefinition> {
        let span_start = self.current_span().start;
        self.expect(&Token::Struct)?;

        let name = if let Some(Token::Ident(n)) = self.current().cloned() {
            self.advance();
            n
        } else {
            return Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: "Expected struct name".to_string(),
            });
        };

        // Parse optional type parameters: <T, U>
        let type_params = if self.check(&Token::Lt) {
            self.advance();
            let mut params = Vec::new();

            while !self.check(&Token::Gt) && !self.is_at_end() {
                if let Some(Token::Ident(param)) = self.current().cloned() {
                    self.advance();
                    params.push(param);

                    if self.check(&Token::Comma) {
                        self.advance();
                    }
                } else {
                    return Err(YuhoError::ParseError {
                        position: self.current_span().start,
                        message: "Expected type parameter name".to_string(),
                    });
                }
            }

            self.expect(&Token::Gt)?;
            params
        } else {
            Vec::new()
        };

        // Parse optional extends clause
        let extends_from = if self.check(&Token::Extends) {
            self.advance();
            if let Some(Token::Ident(parent)) = self.current().cloned() {
                self.advance();
                Some(parent)
            } else {
                return Err(YuhoError::ParseError {
                    position: self.current_span().start,
                    message: "Expected parent struct name after extends".to_string(),
                });
            }
        } else {
            None
        };

        self.expect(&Token::LBrace)?;

        let mut fields = Vec::new();
        while !self.check(&Token::RBrace) && !self.is_at_end() {
            // Parse annotations before field type
            let mut annotations = Vec::new();
            while self.check(&Token::At) {
                annotations.push(self.parse_annotation()?);
            }

            let ty = self.parse_type()?;
            let field_name = if let Some(Token::Ident(n)) = self.current().cloned() {
                self.advance();
                n
            } else {
                return Err(YuhoError::ParseError {
                    position: self.current_span().start,
                    message: "Expected field name".to_string(),
                });
            };
            // Parse optional where clause
            let constraints = if self.check(&Token::Where) {
                self.advance();
                self.parse_constraints()?
            } else {
                vec![]
            };

            fields.push(Field {
                name: field_name,
                ty,
                constraints,
                annotations,
            });

            if self.check(&Token::Comma) {
                self.advance();
            }
        }

        let span_end = self.current_span().end;
        self.expect(&Token::RBrace)?;

        Ok(StructDefinition {
            name,
            type_params,
            fields,
            extends_from,
            span: Span {
                start: span_start,
                end: span_end,
            },
        })
    }

    /// Parse constraints in where clauses
    /// Grammar: constraint ('&&' constraint | '||' constraint)*
    fn parse_constraints(&mut self) -> Result<Vec<Constraint>> {
        let mut constraints = vec![self.parse_single_constraint()?];

        // For now, we collect multiple constraints separated by && or ||
        // In the future, we could build a tree structure
        while self.check(&Token::And) || self.check(&Token::Or) {
            self.advance(); // Skip && or ||
            constraints.push(self.parse_single_constraint()?);
        }

        Ok(constraints)
    }

    /// Parse a single constraint (comparison)
    /// Grammar: expr ('<' | '>' | '<=' | '>=' | '==' | '!=') expr
    fn parse_single_constraint(&mut self) -> Result<Constraint> {
        let _left = self.parse_expr()?; // Left side (field name) - reserved for future use

        let constraint = match self.current() {
            Some(Token::Gt) => {
                self.advance();
                let right = self.parse_expr()?;
                // left > right means the field must be GreaterThan right
                Constraint::GreaterThan(right)
            },
            Some(Token::Lt) => {
                self.advance();
                let right = self.parse_expr()?;
                Constraint::LessThan(right)
            },
            Some(Token::Gte) => {
                self.advance();
                let right = self.parse_expr()?;
                Constraint::GreaterThanOrEqual(right)
            },
            Some(Token::Lte) => {
                self.advance();
                let right = self.parse_expr()?;
                Constraint::LessThanOrEqual(right)
            },
            Some(Token::Eq) => {
                self.advance();
                let right = self.parse_expr()?;
                Constraint::Equal(right)
            },
            Some(Token::Neq) => {
                self.advance();
                let right = self.parse_expr()?;
                Constraint::NotEqual(right)
            },
            _ => {
                return Err(YuhoError::ParseError {
                    position: self.current_span().start,
                    message: "Expected comparison operator (>, <, >=, <=, ==, !=) in constraint"
                        .to_string(),
                });
            },
        };

        Ok(constraint)
    }

    fn parse_enum(&mut self) -> Result<EnumDefinition> {
        let span_start = self.current_span().start;

        // Check for mutually_exclusive annotation before enum keyword
        let mutually_exclusive = if self.check(&Token::MutuallyExclusive) {
            self.advance();
            true
        } else {
            false
        };

        self.expect(&Token::Enum)?;

        let name = if let Some(Token::Ident(n)) = self.current().cloned() {
            self.advance();
            n
        } else {
            return Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: "Expected enum name".to_string(),
            });
        };

        self.expect(&Token::LBrace)?;

        let mut variants = Vec::new();
        while !self.check(&Token::RBrace) && !self.is_at_end() {
            if let Some(Token::Ident(v)) = self.current().cloned() {
                variants.push(v);
                self.advance();
            }
            if self.check(&Token::Comma) {
                self.advance();
            }
        }

        let span_end = self.current_span().end;
        self.expect(&Token::RBrace)?;

        Ok(EnumDefinition {
            name,
            variants,
            mutually_exclusive,
            span: Span {
                start: span_start,
                end: span_end,
            },
        })
    }

    fn parse_legal_test(&mut self) -> Result<LegalTestDefinition> {
        let span_start = self.current_span().start;
        self.expect(&Token::LegalTest)?;

        let name = if let Some(Token::Ident(n)) = self.current().cloned() {
            self.advance();
            n
        } else {
            return Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: "Expected legal test name".to_string(),
            });
        };

        self.expect(&Token::LBrace)?;

        let mut requirements = Vec::new();
        while !self.check(&Token::RBrace) && !self.is_at_end() {
            // Expect "requires"
            self.expect(&Token::Requires)?;

            // Parse requirement name
            let req_name = if let Some(Token::Ident(n)) = self.current().cloned() {
                self.advance();
                n
            } else {
                return Err(YuhoError::ParseError {
                    position: self.current_span().start,
                    message: "Expected requirement name".to_string(),
                });
            };

            // Expect ":"
            self.expect(&Token::Colon)?;

            // Parse type
            let req_span_start = self.current_span().start;
            let ty = self.parse_type()?;
            let req_span_end = self.current_span().end;

            requirements.push(LegalRequirement {
                name: req_name,
                ty,
                span: Span {
                    start: req_span_start,
                    end: req_span_end,
                },
            });

            // Optional comma
            if self.check(&Token::Comma) {
                self.advance();
            }
        }

        let span_end = self.current_span().end;
        self.expect(&Token::RBrace)?;

        Ok(LegalTestDefinition {
            name,
            requirements,
            span: Span {
                start: span_start,
                end: span_end,
            },
        })
    }

    fn parse_conflict_check(&mut self) -> Result<ConflictCheckDefinition> {
        let span_start = self.current_span().start;
        self.expect(&Token::Verify)?;
        self.expect(&Token::NoConflict)?;
        self.expect(&Token::Between)?;

        // Parse first file name (as string or identifier)
        let file1 = if let Some(Token::String(s)) = self.current().cloned() {
            self.advance();
            s
        } else if let Some(Token::Ident(s)) = self.current().cloned() {
            self.advance();
            s
        } else {
            return Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: "Expected file name for conflict check".to_string(),
            });
        };

        // Expect "and" (using identifier)
        if let Some(Token::Ident(s)) = self.current() {
            if s == "and" {
                self.advance();
            } else {
                return Err(YuhoError::ParseError {
                    position: self.current_span().start,
                    message: "Expected 'and' between file names".to_string(),
                });
            }
        } else {
            return Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: "Expected 'and' between file names".to_string(),
            });
        }

        // Parse second file name
        let file2 = if let Some(Token::String(s)) = self.current().cloned() {
            self.advance();
            s
        } else if let Some(Token::Ident(s)) = self.current().cloned() {
            self.advance();
            s
        } else {
            return Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: "Expected second file name for conflict check".to_string(),
            });
        };

        let span_end = self.current_span().end;

        Ok(ConflictCheckDefinition {
            file1,
            file2,
            span: Span {
                start: span_start,
                end: span_end,
            },
        })
    }

    fn parse_principle(&mut self) -> Result<PrincipleDefinition> {
        let span_start = self.current_span().start;
        self.expect(&Token::Principle)?;

        let name = if let Some(Token::Ident(n)) = self.current().cloned() {
            self.advance();
            n
        } else {
            return Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: "Expected principle name".to_string(),
            });
        };

        self.expect(&Token::LBrace)?;

        // Parse the principle body (which is an expression with quantifiers)
        let body = self.parse_expr()?;

        self.expect(&Token::RBrace)?;

        let span_end = self.current_span().end;

        Ok(PrincipleDefinition {
            name,
            body,
            span: Span {
                start: span_start,
                end: span_end,
            },
        })
    }

    fn parse_type_alias(&mut self) -> Result<TypeAliasDefinition> {
        let span_start = self.current_span().start;
        self.expect(&Token::Type)?;

        let name = if let Some(Token::Ident(n)) = self.current().cloned() {
            self.advance();
            n
        } else {
            return Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: "Expected type alias name".to_string(),
            });
        };

        // Parse optional type parameters: <T, U>
        let type_params = if self.check(&Token::Lt) {
            self.advance();
            let mut params = Vec::new();

            while !self.check(&Token::Gt) && !self.is_at_end() {
                if let Some(Token::Ident(param)) = self.current().cloned() {
                    self.advance();
                    params.push(param);

                    if self.check(&Token::Comma) {
                        self.advance();
                    }
                } else {
                    return Err(YuhoError::ParseError {
                        position: self.current_span().start,
                        message: "Expected type parameter name".to_string(),
                    });
                }
            }

            self.expect(&Token::Gt)?;
            params
        } else {
            Vec::new()
        };

        self.expect(&Token::Assign)?;

        let target = self.parse_type()?;
        let span_end = self.current_span().end;

        Ok(TypeAliasDefinition {
            name,
            type_params,
            target,
            span: Span {
                start: span_start,
                end: span_end,
            },
        })
    }

    fn parse_function(&mut self) -> Result<FunctionDefinition> {
        let span_start = self.current_span().start;

        // Parse return type first if present (e.g., "int func foo()")
        let return_type = if !self.check(&Token::Func) {
            let ty = self.parse_type()?;
            self.expect(&Token::Func)?;
            ty
        } else {
            self.expect(&Token::Func)?;
            Type::Pass
        };

        let name = if let Some(Token::Ident(n)) = self.current().cloned() {
            self.advance();
            n
        } else {
            return Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: "Expected function name".to_string(),
            });
        };

        // Parse optional type parameters: <T, U>
        let type_params = if self.check(&Token::Lt) {
            self.advance();
            let mut params = Vec::new();

            while !self.check(&Token::Gt) && !self.is_at_end() {
                if let Some(Token::Ident(param)) = self.current().cloned() {
                    self.advance();
                    params.push(param);

                    if self.check(&Token::Comma) {
                        self.advance();
                    }
                } else {
                    return Err(YuhoError::ParseError {
                        position: self.current_span().start,
                        message: "Expected type parameter name".to_string(),
                    });
                }
            }

            self.expect(&Token::Gt)?;
            params
        } else {
            Vec::new()
        };

        self.expect(&Token::LParen)?;
        let params = self.parse_parameters()?;
        self.expect(&Token::RParen)?;

        self.expect(&Token::LBrace)?;
        let body = self.parse_statements()?;
        let span_end = self.current_span().end;
        self.expect(&Token::RBrace)?;

        Ok(FunctionDefinition {
            name,
            type_params,
            params,
            return_type,
            body,
            requires_clause: None, // TODO: Parse requires clause
            span: Span {
                start: span_start,
                end: span_end,
            },
        })
    }

    fn parse_parameters(&mut self) -> Result<Vec<Parameter>> {
        let mut params = Vec::new();

        while !self.check(&Token::RParen) && !self.is_at_end() {
            let ty = self.parse_type()?;
            let name = if let Some(Token::Ident(n)) = self.current().cloned() {
                self.advance();
                n
            } else {
                return Err(YuhoError::ParseError {
                    position: self.current_span().start,
                    message: "Expected parameter name".to_string(),
                });
            };
            params.push(Parameter { name, ty });

            if self.check(&Token::Comma) {
                self.advance();
            } else {
                break;
            }
        }

        Ok(params)
    }

    fn parse_type(&mut self) -> Result<Type> {
        let base = match self.current() {
            Some(Token::TyInt) | Some(Token::TyInteger) => {
                self.advance();
                Type::Int
            },
            Some(Token::TyFloat) => {
                self.advance();
                Type::Float
            },
            Some(Token::TyBool) | Some(Token::TyBoolean) => {
                self.advance();
                Type::Bool
            },
            Some(Token::TyString) => {
                self.advance();
                Type::String
            },
            Some(Token::TyMoney) => {
                self.advance();
                // Check for parametric money type: money<Currency>
                if self.check(&Token::Lt) {
                    self.advance();
                    let currency = if let Some(Token::Ident(c)) = self.current().cloned() {
                        self.advance();
                        c
                    } else {
                        return Err(YuhoError::ParseError {
                            position: self.current_span().start,
                            message: "Expected currency code after money<".to_string(),
                        });
                    };
                    self.expect(&Token::Gt)?;
                    Type::MoneyWithCurrency(currency)
                } else {
                    Type::Money
                }
            },
            Some(Token::TyDate) => {
                self.advance();
                Type::Date
            },
            Some(Token::TyDuration) => {
                self.advance();
                Type::Duration
            },
            Some(Token::TyPercent) => {
                self.advance();
                Type::Percent
            },
            Some(Token::Pass) => {
                self.advance();
                Type::Pass
            },

            // Dependent types (Phase 1)
            Some(Token::TyBoundedInt) => {
                self.advance();
                self.expect(&Token::Lt)?;
                let min = if let Some(Token::Int(n)) = self.current() {
                    let val = *n;
                    self.advance();
                    val
                } else {
                    return Err(YuhoError::ParseError {
                        position: self.current_span().start,
                        message: "Expected integer literal for BoundedInt min".to_string(),
                    });
                };
                self.expect(&Token::Comma)?;
                let max = if let Some(Token::Int(n)) = self.current() {
                    let val = *n;
                    self.advance();
                    val
                } else {
                    return Err(YuhoError::ParseError {
                        position: self.current_span().start,
                        message: "Expected integer literal for BoundedInt max".to_string(),
                    });
                };
                self.expect(&Token::Gt)?;
                Type::BoundedInt { min, max }
            },
            Some(Token::TyNonEmpty) => {
                self.advance();
                self.expect(&Token::Lt)?;
                let inner = self.parse_type()?;
                self.expect(&Token::Gt)?;
                Type::NonEmpty(Box::new(inner))
            },
            Some(Token::TyPositive) => {
                self.advance();
                self.expect(&Token::Lt)?;
                let inner = self.parse_type()?;
                self.expect(&Token::Gt)?;
                Type::Positive(Box::new(inner))
            },
            Some(Token::TyValidDate) => {
                self.advance();

                // Parse optional after/before date constraints
                // Syntax: ValidDate or ValidDate<after="DD-MM-YYYY", before="DD-MM-YYYY">
                let (after, before) = if self.check(&Token::Lt) {
                    self.advance();
                    let mut after_date = None;
                    let mut before_date = None;

                    // Parse named parameters
                    loop {
                        if self.check(&Token::Gt) {
                            break;
                        }

                        // Expect identifier (after or before)
                        if let Some(Token::Ident(param_name)) = self.current().cloned() {
                            self.advance();

                            // Expect '='
                            self.expect(&Token::Equals)?;

                            // Expect date string
                            if let Some(Token::String(date_str)) = self.current().cloned() {
                                self.advance();

                                match param_name.as_str() {
                                    "after" => after_date = Some(date_str),
                                    "before" => before_date = Some(date_str),
                                    _ => {
                                        return Err(YuhoError::ParseError {
                                            position: self.current_span().start,
                                            message: format!("Unknown ValidDate parameter '{}'. Expected 'after' or 'before'", param_name),
                                        });
                                    },
                                }
                            } else {
                                return Err(YuhoError::ParseError {
                                    position: self.current_span().start,
                                    message:
                                        "Expected date string after '=' in ValidDate parameter"
                                            .to_string(),
                                });
                            }

                            // Optional comma
                            if self.check(&Token::Comma) {
                                self.advance();
                            }
                        } else {
                            return Err(YuhoError::ParseError {
                                position: self.current_span().start,
                                message: "Expected 'after' or 'before' parameter name in ValidDate"
                                    .to_string(),
                            });
                        }
                    }

                    self.expect(&Token::Gt)?;
                    (after_date, before_date)
                } else {
                    (None, None)
                };

                Type::ValidDate { after, before }
            },
            Some(Token::TyArray) => {
                self.advance();
                self.expect(&Token::Lt)?;
                let inner = self.parse_type()?;
                self.expect(&Token::Gt)?;
                Type::Array(Box::new(inner))
            },
            Some(Token::TyCitation) => {
                self.advance();
                self.expect(&Token::Lt)?;

                // Parse section
                let section = if let Some(Token::String(s)) = self.current().cloned() {
                    self.advance();
                    s
                } else {
                    return Err(YuhoError::ParseError {
                        position: self.current_span().start,
                        message: "Expected section string in Citation".to_string(),
                    });
                };

                self.expect(&Token::Comma)?;

                // Parse subsection
                let subsection = if let Some(Token::String(s)) = self.current().cloned() {
                    self.advance();
                    s
                } else {
                    return Err(YuhoError::ParseError {
                        position: self.current_span().start,
                        message: "Expected subsection string in Citation".to_string(),
                    });
                };

                self.expect(&Token::Comma)?;

                // Parse act
                let act = if let Some(Token::String(s)) = self.current().cloned() {
                    self.advance();
                    s
                } else {
                    return Err(YuhoError::ParseError {
                        position: self.current_span().start,
                        message: "Expected act string in Citation".to_string(),
                    });
                };

                self.expect(&Token::Gt)?;
                Type::Citation {
                    section,
                    subsection,
                    act,
                }
            },
            Some(Token::TyTemporal) => {
                self.advance();
                self.expect(&Token::Lt)?;

                // Parse inner type
                let inner = self.parse_type()?;

                let mut valid_from = None;
                let mut valid_until = None;

                // Parse optional temporal parameters
                if self.check(&Token::Comma) {
                    self.advance();

                    // Parse named parameters: valid_from="...", valid_until="..."
                    loop {
                        if self.check(&Token::Gt) {
                            break;
                        }

                        if let Some(Token::Ident(param_name)) = self.current().cloned() {
                            self.advance();
                            self.expect(&Token::Equals)?;

                            if let Some(Token::String(date_str)) = self.current().cloned() {
                                self.advance();

                                match param_name.as_str() {
                                    "valid_from" => valid_from = Some(date_str),
                                    "valid_until" => valid_until = Some(date_str),
                                    _ => {
                                        return Err(YuhoError::ParseError {
                                            position: self.current_span().start,
                                            message: format!("Unknown Temporal parameter '{}'. Expected 'valid_from' or 'valid_until'", param_name),
                                        });
                                    },
                                }
                            } else {
                                return Err(YuhoError::ParseError {
                                    position: self.current_span().start,
                                    message: "Expected date string after '=' in Temporal parameter"
                                        .to_string(),
                                });
                            }

                            if self.check(&Token::Comma) {
                                self.advance();
                            }
                        } else {
                            break;
                        }
                    }
                }

                self.expect(&Token::Gt)?;
                Type::TemporalValue {
                    inner: Box::new(inner),
                    valid_from,
                    valid_until,
                }
            },

            Some(Token::Ident(name)) => {
                let n = name.clone();
                self.advance();

                // Check for generic type instantiation: Container<T>
                if self.check(&Token::Lt) {
                    self.advance();
                    let mut args = Vec::new();

                    while !self.check(&Token::Gt) && !self.is_at_end() {
                        args.push(self.parse_type()?);

                        if self.check(&Token::Comma) {
                            self.advance();
                        }
                    }

                    self.expect(&Token::Gt)?;
                    Type::Generic { name: n, args }
                } else {
                    // Could be a type variable (T, U) or a named type (Person)
                    // We'll treat single uppercase identifiers as type variables
                    if n.chars().all(|c| c.is_uppercase() || c == '_') && n.len() <= 2 {
                        Type::TypeVariable(n)
                    } else {
                        Type::Named(n)
                    }
                }
            },
            _ => {
                return Err(YuhoError::ParseError {
                    position: self.current_span().start,
                    message: "Expected type".to_string(),
                });
            },
        };

        // Check for union type
        if self.check(&Token::Or) {
            self.advance();
            let right = self.parse_type()?;
            Ok(Type::Union(Box::new(base), Box::new(right)))
        } else {
            Ok(base)
        }
    }

    fn parse_declaration(&mut self) -> Result<Declaration> {
        let span_start = self.current_span().start;
        let ty = self.parse_type()?;

        let name = if let Some(Token::Ident(n)) = self.current().cloned() {
            self.advance();
            n
        } else {
            return Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: "Expected variable name".to_string(),
            });
        };

        self.expect(&Token::Assign)?;
        let value = self.parse_expr()?;
        let span_end = self.current_span().end;

        Ok(Declaration {
            name,
            ty,
            value,
            span: Span {
                start: span_start,
                end: span_end,
            },
        })
    }

    fn parse_statements(&mut self) -> Result<Vec<Statement>> {
        let mut stmts = Vec::new();

        while !self.check(&Token::RBrace) && !self.is_at_end() {
            stmts.push(self.parse_statement()?);
        }

        Ok(stmts)
    }

    fn parse_statement(&mut self) -> Result<Statement> {
        match self.current() {
            Some(Token::Match) => Ok(Statement::Match(self.parse_match()?)),
            Some(Token::Pass) => {
                self.advance();
                Ok(Statement::Pass)
            },
            Some(Token::Assign) => {
                self.advance();
                let expr = self.parse_expr()?;
                Ok(Statement::Return(expr))
            },
            _ => {
                let decl = self.parse_declaration()?;
                Ok(Statement::Declaration(decl))
            },
        }
    }

    fn parse_match(&mut self) -> Result<MatchExpr> {
        let span_start = self.current_span().start;
        self.expect(&Token::Match)?;

        let scrutinee = Box::new(self.parse_expr()?);

        self.expect(&Token::LBrace)?;

        let mut cases = Vec::new();
        while !self.check(&Token::RBrace) && !self.is_at_end() {
            cases.push(self.parse_case()?);
        }

        let span_end = self.current_span().end;
        self.expect(&Token::RBrace)?;

        Ok(MatchExpr {
            scrutinee,
            cases,
            span: Span {
                start: span_start,
                end: span_end,
            },
        })
    }

    fn parse_case(&mut self) -> Result<MatchCase> {
        self.expect(&Token::Case)?;

        let pattern = self.parse_pattern()?;

        // Parse optional guard clause: where <expr>
        let guard = if self.check(&Token::Where) {
            self.advance();
            Some(self.parse_expr()?)
        } else {
            None
        };

        self.expect(&Token::Assign)?;

        if self.check(&Token::Consequence) {
            self.advance();
        }

        let consequence = self.parse_expr()?;

        Ok(MatchCase {
            pattern,
            guard,
            consequence,
        })
    }

    fn parse_pattern(&mut self) -> Result<Pattern> {
        match self.current() {
            Some(Token::Underscore) => {
                self.advance();
                Ok(Pattern::Wildcard)
            },
            Some(Token::Satisfies) => {
                self.advance();
                // Expect legal test name
                if let Some(Token::Ident(name)) = self.current().cloned() {
                    self.advance();
                    Ok(Pattern::Satisfies(name))
                } else {
                    Err(YuhoError::ParseError {
                        position: self.current_span().start,
                        message: "Expected legal test name after 'satisfies'".to_string(),
                    })
                }
            },
            Some(Token::True) => {
                self.advance();
                Ok(Pattern::Literal(Literal::Bool(true)))
            },
            Some(Token::False) => {
                self.advance();
                Ok(Pattern::Literal(Literal::Bool(false)))
            },
            Some(Token::Int(n)) => {
                let n = *n;
                self.advance();
                Ok(Pattern::Literal(Literal::Int(n)))
            },
            Some(Token::Float(n)) => {
                let n = *n;
                self.advance();
                Ok(Pattern::Literal(Literal::Float(n)))
            },
            Some(Token::String(s)) => {
                let s = s.clone();
                self.advance();
                Ok(Pattern::Literal(Literal::String(s)))
            },
            Some(Token::Ident(name)) => {
                let n = name.clone();
                self.advance();
                Ok(Pattern::Identifier(n))
            },
            _ => Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: "Expected pattern".to_string(),
            }),
        }
    }

    fn parse_expr(&mut self) -> Result<Expr> {
        self.parse_or_expr()
    }

    fn parse_or_expr(&mut self) -> Result<Expr> {
        let mut left = self.parse_and_expr()?;

        while self.check(&Token::Or) {
            self.advance();
            let right = self.parse_and_expr()?;
            left = Expr::Binary(Box::new(left), BinaryOp::Or, Box::new(right));
        }

        Ok(left)
    }

    fn parse_and_expr(&mut self) -> Result<Expr> {
        let mut left = self.parse_equality_expr()?;

        while self.check(&Token::And) {
            self.advance();
            let right = self.parse_equality_expr()?;
            left = Expr::Binary(Box::new(left), BinaryOp::And, Box::new(right));
        }

        Ok(left)
    }

    fn parse_equality_expr(&mut self) -> Result<Expr> {
        let mut left = self.parse_comparison_expr()?;

        loop {
            let op = match self.current() {
                Some(Token::Eq) => BinaryOp::Eq,
                Some(Token::Neq) => BinaryOp::Neq,
                _ => break,
            };
            self.advance();
            let right = self.parse_comparison_expr()?;
            left = Expr::Binary(Box::new(left), op, Box::new(right));
        }

        Ok(left)
    }

    fn parse_comparison_expr(&mut self) -> Result<Expr> {
        let mut left = self.parse_additive_expr()?;

        loop {
            let op = match self.current() {
                Some(Token::Lt) => BinaryOp::Lt,
                Some(Token::Gt) => BinaryOp::Gt,
                Some(Token::Lte) => BinaryOp::Lte,
                Some(Token::Gte) => BinaryOp::Gte,
                _ => break,
            };
            self.advance();
            let right = self.parse_additive_expr()?;
            left = Expr::Binary(Box::new(left), op, Box::new(right));
        }

        Ok(left)
    }

    fn parse_additive_expr(&mut self) -> Result<Expr> {
        let mut left = self.parse_multiplicative_expr()?;

        loop {
            let op = match self.current() {
                Some(Token::Plus) => BinaryOp::Add,
                Some(Token::Minus) => BinaryOp::Sub,
                _ => break,
            };
            self.advance();
            let right = self.parse_multiplicative_expr()?;
            left = Expr::Binary(Box::new(left), op, Box::new(right));
        }

        Ok(left)
    }

    fn parse_multiplicative_expr(&mut self) -> Result<Expr> {
        let mut left = self.parse_unary_expr()?;

        loop {
            let op = match self.current() {
                Some(Token::Star) => BinaryOp::Mul,
                Some(Token::Slash) => BinaryOp::Div,
                Some(Token::Percent_) => BinaryOp::Mod,
                _ => break,
            };
            self.advance();
            let right = self.parse_unary_expr()?;
            left = Expr::Binary(Box::new(left), op, Box::new(right));
        }

        Ok(left)
    }

    fn parse_unary_expr(&mut self) -> Result<Expr> {
        match self.current() {
            Some(Token::Not) => {
                self.advance();
                let expr = self.parse_unary_expr()?;
                Ok(Expr::Unary(UnaryOp::Not, Box::new(expr)))
            },
            Some(Token::Minus) => {
                self.advance();
                let expr = self.parse_unary_expr()?;
                Ok(Expr::Unary(UnaryOp::Neg, Box::new(expr)))
            },
            _ => self.parse_postfix_expr(),
        }
    }

    fn parse_postfix_expr(&mut self) -> Result<Expr> {
        let mut expr = self.parse_primary_expr()?;

        loop {
            if self.check(&Token::Dot) {
                self.advance();
                if let Some(Token::Ident(field)) = self.current().cloned() {
                    self.advance();
                    expr = Expr::FieldAccess(Box::new(expr), field);
                } else {
                    return Err(YuhoError::ParseError {
                        position: self.current_span().start,
                        message: "Expected field name after '.'".to_string(),
                    });
                }
            } else if self.check(&Token::LParen) {
                if let Expr::Identifier(name) = expr {
                    self.advance();
                    let args = self.parse_arguments()?;
                    self.expect(&Token::RParen)?;
                    expr = Expr::Call(name, args);
                } else {
                    break;
                }
            } else {
                break;
            }
        }

        Ok(expr)
    }

    fn parse_arguments(&mut self) -> Result<Vec<Expr>> {
        let mut args = Vec::new();

        while !self.check(&Token::RParen) && !self.is_at_end() {
            args.push(self.parse_expr()?);
            if self.check(&Token::Comma) {
                self.advance();
            } else {
                break;
            }
        }

        Ok(args)
    }

    fn parse_primary_expr(&mut self) -> Result<Expr> {
        match self.current().cloned() {
            Some(Token::Forall) => {
                self.advance();
                self.parse_quantifier_expr(true)
            },
            Some(Token::Exists) => {
                self.advance();
                self.parse_quantifier_expr(false)
            },
            Some(Token::Int(n)) => {
                self.advance();
                Ok(Expr::Literal(Literal::Int(n)))
            },
            Some(Token::Float(n)) => {
                self.advance();
                Ok(Expr::Literal(Literal::Float(n)))
            },
            Some(Token::True) => {
                self.advance();
                Ok(Expr::Literal(Literal::Bool(true)))
            },
            Some(Token::False) => {
                self.advance();
                Ok(Expr::Literal(Literal::Bool(false)))
            },
            Some(Token::String(s)) => {
                self.advance();
                Ok(Expr::Literal(Literal::String(s)))
            },
            Some(Token::Money(n)) => {
                self.advance();
                Ok(Expr::Literal(Literal::Money(n)))
            },
            Some(Token::Date(d)) => {
                self.advance();
                Ok(Expr::Literal(Literal::Date(d)))
            },
            Some(Token::Percent(p)) => {
                self.advance();
                Ok(Expr::Literal(Literal::Percent(p)))
            },
            Some(Token::Pass) => {
                self.advance();
                Ok(Expr::Literal(Literal::Pass))
            },
            Some(Token::Ident(name)) => {
                self.advance();
                // Only parse struct init if we see { followed by identifier :=
                // This prevents matching expressions like "match x {" as struct init
                if self.check(&Token::LBrace) {
                    if let Some(Token::Ident(_)) = self.peek(1) {
                        if matches!(self.peek(2), Some(Token::Assign)) {
                            return self.parse_struct_init(name);
                        }
                    }
                }
                Ok(Expr::Identifier(name))
            },
            Some(Token::LBrace) => {
                // Anonymous struct init
                if let Some(Token::Ident(_)) = self.peek(1) {
                    if matches!(self.peek(2), Some(Token::Assign)) {
                        return self.parse_struct_init("".to_string());
                    }
                }
                Err(YuhoError::ParseError {
                    position: self.current_span().start,
                    message: "Unexpected '{' in expression".to_string(),
                })
            },
            Some(Token::LParen) => {
                self.advance();
                let expr = self.parse_expr()?;
                self.expect(&Token::RParen)?;
                Ok(expr)
            },
            Some(Token::Match) => {
                let m = self.parse_match()?;
                Ok(Expr::Match(Box::new(m)))
            },
            Some(t) => Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: format!("Unexpected token in expression: {:?}", t),
            }),
            None => Err(YuhoError::ParseError {
                position: 0,
                message: "Unexpected EOF in expression".to_string(),
            }),
        }
    }

    fn parse_struct_init(&mut self, name: String) -> Result<Expr> {
        self.expect(&Token::LBrace)?;

        let mut fields = Vec::new();
        while !self.check(&Token::RBrace) && !self.is_at_end() {
            let field_name = if let Some(Token::Ident(n)) = self.current().cloned() {
                self.advance();
                n
            } else {
                return Err(YuhoError::ParseError {
                    position: self.current_span().start,
                    message: "Expected field name in struct init".to_string(),
                });
            };

            self.expect(&Token::Assign)?;
            let value = self.parse_expr()?;
            fields.push((field_name, value));

            if self.check(&Token::Comma) {
                self.advance();
            }
        }

        self.expect(&Token::RBrace)?;

        Ok(Expr::StructInit(StructInit { name, fields }))
    }

    fn parse_quantifier_expr(&mut self, is_forall: bool) -> Result<Expr> {
        // Parse: forall var: Type, body
        // Parse: exists var: Type, body
        // Now supports nested quantifiers:
        // forall x: Type1, forall y: Type2, body
        // forall x: Type1, exists y: Type2, body

        // Track nesting depth - warn if too deep (>10 levels)
        self.quantifier_depth += 1;
        if self.quantifier_depth > 10 {
            self.quantifier_depth -= 1;
            return Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: "Quantifier nesting too deep (max 10 levels)".to_string(),
            });
        }

        let var = if let Some(Token::Ident(v)) = self.current().cloned() {
            self.advance();
            v
        } else {
            self.quantifier_depth -= 1;
            return Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: format!(
                    "Expected variable name after {}, got {:?}",
                    if is_forall { "forall" } else { "exists" },
                    self.current()
                ),
            });
        };

        // Expect colon with helpful error message
        if !self.check(&Token::Colon) {
            self.quantifier_depth -= 1;
            return Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: format!(
                    "Expected ':' after variable '{}' in quantifier, got {:?}",
                    var,
                    self.current()
                ),
            });
        }
        self.advance();

        let ty = self.parse_type().map_err(|e| {
            self.quantifier_depth -= 1;
            e
        })?;

        // Expect comma with helpful error message
        if !self.check(&Token::Comma) {
            self.quantifier_depth -= 1;
            return Err(YuhoError::ParseError {
                position: self.current_span().start,
                message: format!(
                    "Expected ',' after type in quantifier, got {:?}. Quantifiers require: {} var: Type, body",
                    self.current(),
                    if is_forall { "forall" } else { "exists" }
                ),
            });
        }
        self.advance();

        // Support nested quantifiers by checking for forall/exists keywords
        let body = if self.check(&Token::Forall) || self.check(&Token::Exists) {
            // Parse nested quantifier directly
            let is_nested_forall = self.check(&Token::Forall);
            self.advance();
            Box::new(self.parse_quantifier_expr(is_nested_forall)?)
        } else {
            Box::new(self.parse_expr().map_err(|e| {
                self.quantifier_depth -= 1;
                e
            })?)
        };

        self.quantifier_depth -= 1;

        if is_forall {
            Ok(Expr::Forall { var, ty, body })
        } else {
            Ok(Expr::Exists { var, ty, body })
        }
    }

    /// Parse a proviso clause: proviso that <condition> { <exceptions> }
    fn parse_proviso(&mut self) -> Result<ProvisoClause> {
        let span_start = self.current_span().start;

        // Accept either 'proviso' or 'provided'
        if self.check(&Token::Proviso) {
            self.advance();
        } else if self.check(&Token::Provided) {
            self.advance();
        }

        // Optional 'that'
        if self.check(&Token::That) {
            self.advance();
        }

        // Parse condition expression
        let condition = self.parse_expr()?;

        // Optional 'applies to' clause
        let applies_to = if let Some(Token::Ident(name)) = self.current() {
            if name == "applies" {
                self.advance();
                if let Some(Token::Ident(to)) = self.current() {
                    if to == "to" {
                        self.advance();
                        if let Some(Token::Ident(target)) = self.current().cloned() {
                            self.advance();
                            Some(target)
                        } else {
                            None
                        }
                    } else {
                        None
                    }
                } else {
                    None
                }
            } else {
                None
            }
        } else {
            None
        };

        self.expect(&Token::LBrace)?;
        let exception = self.parse_statements()?;
        let span_end = self.current_span().end;
        self.expect(&Token::RBrace)?;

        Ok(ProvisoClause {
            condition,
            exception,
            applies_to,
            span: Span {
                start: span_start,
                end: span_end,
            },
        })
    }

    /// Parse an annotation: @precedent("citation"), @presumed(Value), etc.
    fn parse_annotation(&mut self) -> Result<Annotation> {
        self.expect(&Token::At)?;

        match self.current() {
            Some(Token::Precedent) => {
                self.advance();
                self.expect(&Token::LParen)?;

                let citation = if let Some(Token::String(s)) = self.current().cloned() {
                    self.advance();
                    s
                } else {
                    return Err(YuhoError::ParseError {
                        position: self.current_span().start,
                        message: "Expected citation string in @precedent()".to_string(),
                    });
                };

                self.expect(&Token::RParen)?;
                Ok(Annotation::Precedent { citation })
            }
            Some(Token::Presumed) => {
                self.advance();
                self.expect(&Token::LParen)?;

                let value = if let Some(Token::Ident(s)) = self.current().cloned() {
                    self.advance();
                    s
                } else {
                    return Err(YuhoError::ParseError {
                        position: self.current_span().start,
                        message: "Expected value in @presumed()".to_string(),
                    });
                };

                self.expect(&Token::RParen)?;
                Ok(Annotation::Presumed(value))
            }
            Some(Token::Ident(name)) if name == "hierarchy" => {
                self.advance();
                self.expect(&Token::LParen)?;

                // Parse level=Value
                if let Some(Token::Ident(key)) = self.current() {
                    if key != "level" {
                        return Err(YuhoError::ParseError {
                            position: self.current_span().start,
                            message: "Expected 'level' parameter in @hierarchy()".to_string(),
                        });
                    }
                    self.advance();
                }

                self.expect(&Token::Equals)?;

                let level = if let Some(Token::Ident(lv)) = self.current().cloned() {
                    self.advance();
                    lv
                } else {
                    return Err(YuhoError::ParseError {
                        position: self.current_span().start,
                        message: "Expected level value in @hierarchy()".to_string(),
                    });
                };

                let mut subordinate_to = None;
                if self.check(&Token::Comma) {
                    self.advance();
                    if let Some(Token::Ident(key)) = self.current() {
                        if key == "subordinate_to" {
                            self.advance();
                            self.expect(&Token::Equals)?;
                            if let Some(Token::Ident(parent)) = self.current().cloned() {
                                self.advance();
                                subordinate_to = Some(parent);
                            }
                        }
                    }
                }

                self.expect(&Token::RParen)?;
                Ok(Annotation::Hierarchy { level, subordinate_to })
            }
            Some(Token::Ident(name)) if name == "amended" => {
                self.advance();
                self.expect(&Token::LParen)?;

                // Parse date=Value, act=Value (date might be TyDate token)
                match self.current() {
                    Some(Token::Ident(key)) if key == "date" => {
                        self.advance();
                    }
                    Some(Token::TyDate) => {
                        self.advance();
                    }
                    _ => {
                        return Err(YuhoError::ParseError {
                            position: self.current_span().start,
                            message: "Expected 'date' parameter in @amended()".to_string(),
                        });
                    }
                }

                self.expect(&Token::Equals)?;

                let date = if let Some(Token::String(d)) = self.current().cloned() {
                    self.advance();
                    d
                } else {
                    return Err(YuhoError::ParseError {
                        position: self.current_span().start,
                        message: "Expected date string in @amended()".to_string(),
                    });
                };

                self.expect(&Token::Comma)?;

                if let Some(Token::Ident(key)) = self.current() {
                    if key != "act" {
                        return Err(YuhoError::ParseError {
                            position: self.current_span().start,
                            message: "Expected 'act' parameter in @amended()".to_string(),
                        });
                    }
                    self.advance();
                }

                self.expect(&Token::Equals)?;

                let act = if let Some(Token::String(a)) = self.current().cloned() {
                    self.advance();
                    a
                } else {
                    return Err(YuhoError::ParseError {
                        position: self.current_span().start,
                        message: "Expected act string in @amended()".to_string(),
                    });
                };

                self.expect(&Token::RParen)?;
                Ok(Annotation::Amended { date, act })
            }
            _ => {
                Err(YuhoError::ParseError {
                    position: self.current_span().start,
                    message: "Unknown annotation type. Expected @precedent, @presumed, @hierarchy, or @amended".to_string(),
                })
            }
        }
    }
}

pub fn parse(source: &str) -> Result<Program> {
    let tokens = crate::lex(source);
    let mut parser = Parser::new(tokens);
    parser.parse_program()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_struct() {
        let source = r#"struct Foo { int x, string y, }"#;
        let program = parse(source).unwrap();
        assert_eq!(program.items.len(), 1);
        if let Item::Struct(s) = &program.items[0] {
            assert_eq!(s.name, "Foo");
            assert_eq!(s.fields.len(), 2);
        } else {
            panic!("Expected struct");
        }
    }

    #[test]
    fn test_parse_enum() {
        let source = r#"enum Color { Red, Green, Blue, }"#;
        let program = parse(source).unwrap();
        assert_eq!(program.items.len(), 1);
        if let Item::Enum(e) = &program.items[0] {
            assert_eq!(e.name, "Color");
            assert_eq!(e.variants.len(), 3);
        } else {
            panic!("Expected enum");
        }
    }

    #[test]
    fn test_parse_declaration() {
        let source = r#"int x := 42"#;
        let program = parse(source).unwrap();
        assert_eq!(program.items.len(), 1);
    }

    #[test]
    fn test_parse_money() {
        let source = r#"money amt := $100.50"#;
        let program = parse(source).unwrap();
        assert_eq!(program.items.len(), 1);
    }

    #[test]
    fn test_parse_scope() {
        let source = r#"scope test { int x := 1 }"#;
        let program = parse(source).unwrap();
        assert_eq!(program.items.len(), 1);
        if let Item::Scope(s) = &program.items[0] {
            assert_eq!(s.name, "test");
            assert_eq!(s.items.len(), 1);
        } else {
            panic!("Expected scope");
        }
    }

    #[test]
    fn test_parse_match() {
        let source = r#"match x { case 1 := "one" case _ := "other" }"#;
        let program = parse(source).unwrap();
        assert_eq!(program.items.len(), 1);
    }

    #[test]
    fn test_parse_binary_expr() {
        let source = r#"int result := 1 + 2 * 3"#;
        let program = parse(source).unwrap();
        if let Item::Declaration(d) = &program.items[0] {
            // Should be 1 + (2 * 3) due to precedence
            if let Expr::Binary(_, BinaryOp::Add, _) = &d.value {
                // correct
            } else {
                panic!("Expected addition at top level");
            }
        }
    }

    #[test]
    fn test_parse_function() {
        let source = r#"int func add(int a, int b) { := a + b }"#;
        let program = parse(source).unwrap();
        if let Item::Function(f) = &program.items[0] {
            assert_eq!(f.name, "add");
            assert_eq!(f.params.len(), 2);
        } else {
            panic!("Expected function");
        }
    }

    #[test]
    fn test_parse_struct_init() {
        let source = r#"Person p := { name := "John", age := 30, }"#;
        let program = parse(source).unwrap();
        if let Item::Declaration(d) = &program.items[0] {
            if let Expr::StructInit(init) = &d.value {
                assert_eq!(init.fields.len(), 2);
            } else {
                panic!("Expected struct init");
            }
        }
    }

    #[test]
    fn test_parse_import() {
        let source = r#"referencing Foo, Bar from module"#;
        let program = parse(source).unwrap();
        assert_eq!(program.imports.len(), 1);
        assert_eq!(program.imports[0].names, vec!["Foo", "Bar"]);
        assert_eq!(program.imports[0].from, "module");
    }

    #[test]
    fn test_parse_union_type() {
        let source = r#"int || pass x := 42"#;
        let program = parse(source).unwrap();
        if let Item::Declaration(d) = &program.items[0] {
            if let Type::Union(_, _) = &d.ty {
                // correct
            } else {
                panic!("Expected union type");
            }
        }
    }

    // Phase 1 tests for dependent types
    #[test]
    fn test_parse_bounded_int() {
        let source = r#"BoundedInt<0, 100> age := 25"#;
        let program = parse(source).unwrap();
        if let Item::Declaration(d) = &program.items[0] {
            if let Type::BoundedInt { min, max } = &d.ty {
                assert_eq!(*min, 0);
                assert_eq!(*max, 100);
            } else {
                panic!("Expected BoundedInt type");
            }
        }
    }

    #[test]
    fn test_parse_nonempty_array() {
        let source = r#"NonEmpty<string> names := "test""#;
        let program = parse(source).unwrap();
        if let Item::Declaration(d) = &program.items[0] {
            if let Type::NonEmpty(inner) = &d.ty {
                assert_eq!(**inner, Type::String);
            } else {
                panic!("Expected NonEmpty type");
            }
        }
    }

    #[test]
    fn test_parse_positive_type() {
        let source = r#"Positive<int> count := 5"#;
        let program = parse(source).unwrap();
        if let Item::Declaration(d) = &program.items[0] {
            if let Type::Positive(inner) = &d.ty {
                assert_eq!(**inner, Type::Int);
            } else {
                panic!("Expected Positive type");
            }
        }
    }

    #[test]
    fn test_parse_array_type() {
        let source = r#"Array<string> items := "item""#;
        let program = parse(source).unwrap();
        if let Item::Declaration(d) = &program.items[0] {
            if let Type::Array(inner) = &d.ty {
                assert_eq!(**inner, Type::String);
            } else {
                panic!("Expected Array type");
            }
        }
    }

    #[test]
    fn test_parse_money_with_currency() {
        let source = r#"money<SGD> amount := $50.00"#;
        let program = parse(source).unwrap();
        if let Item::Declaration(d) = &program.items[0] {
            if let Type::MoneyWithCurrency(currency) = &d.ty {
                assert_eq!(currency, "SGD");
            } else {
                panic!("Expected MoneyWithCurrency type");
            }
        }
    }

    // Error handling tests
    #[test]
    fn test_parse_error_missing_brace() {
        let source = "struct Foo { int x";
        assert!(parse(source).is_err());
    }

    #[test]
    fn test_parse_error_invalid_token() {
        let source = "struct @ invalid";
        assert!(parse(source).is_err());
    }

    #[test]
    fn test_parse_nested_match() {
        let source = r#"
            match x {
                case 1 := match y {
                    case true := "nested"
                    case _ := "other"
                }
                case _ := "default"
            }
        "#;
        let program = parse(source).unwrap();
        assert_eq!(program.items.len(), 1);
    }

    #[test]
    fn test_parse_complex_expression() {
        let source = r#"int result := (1 + 2) * 3 - 4 / 2"#;
        let program = parse(source).unwrap();
        assert_eq!(program.items.len(), 1);
    }

    #[test]
    fn test_parse_field_access_chain() {
        let source = r#"string name := person.address.city"#;
        let program = parse(source).unwrap();
        if let Item::Declaration(d) = &program.items[0] {
            assert!(matches!(d.value, Expr::FieldAccess(_, _)));
        }
    }

    #[test]
    fn test_parse_function_call_with_args() {
        let source = r#"int result := add(1, 2, 3)"#;
        let program = parse(source).unwrap();
        if let Item::Declaration(d) = &program.items[0] {
            if let Expr::Call(name, args) = &d.value {
                assert_eq!(name, "add");
                assert_eq!(args.len(), 3);
            } else {
                panic!("Expected function call");
            }
        }
    }

    #[test]
    fn test_parse_empty_struct() {
        let source = "struct Empty {}";
        let program = parse(source).unwrap();
        if let Item::Struct(s) = &program.items[0] {
            assert_eq!(s.fields.len(), 0);
        }
    }

    #[test]
    fn test_parse_empty_enum() {
        let source = "enum Empty {}";
        let program = parse(source).unwrap();
        if let Item::Enum(e) = &program.items[0] {
            assert_eq!(e.variants.len(), 0);
        }
    }

    #[test]
    fn test_parse_unary_operators() {
        let source = r#"bool result := !true int neg := -42"#;
        let program = parse(source).unwrap();
        assert_eq!(program.items.len(), 2);
        if let Item::Declaration(d) = &program.items[0] {
            assert!(matches!(d.value, Expr::Unary(UnaryOp::Not, _)));
        }
        if let Item::Declaration(d) = &program.items[1] {
            assert!(matches!(d.value, Expr::Unary(UnaryOp::Neg, _)));
        }
    }

    // Note: Where clause tests in integration tests - see examples/where_clauses.yh

    // ValidDate constraint tests
    #[test]
    fn test_parse_valid_date_simple() {
        let source = r#"ValidDate event_date := 01-01-2024"#;
        let program = parse(source).unwrap();
        if let Item::Declaration(d) = &program.items[0] {
            assert!(matches!(
                d.ty,
                Type::ValidDate {
                    after: None,
                    before: None
                }
            ));
        } else {
            panic!("Expected declaration");
        }
    }

    // Note: ValidDate with after/before parameters tested in integration tests
    // Parser requires specific syntax that's better tested end-to-end
}
