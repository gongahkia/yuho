/**
 * tree-sitter external scanner for Yuho v5
 * Handles context-sensitive tokens like string interpolation
 */

#include "tree_sitter/parser.h"
#include <wctype.h>
#include <string.h>
#include <stdlib.h>

enum TokenType {
    STRING_CONTENT,
    INTERPOLATION_START,
    INTERPOLATION_END,
    ERROR_SENTINEL,
    TYPED_STRUCT_LITERAL_TYPE_NAME,
};

typedef struct {
    bool in_string;
    bool in_interpolation;
    uint8_t interpolation_depth;
} Scanner;

void *tree_sitter_yuho_external_scanner_create() {
    Scanner *scanner = (Scanner *)malloc(sizeof(Scanner));
    scanner->in_string = false;
    scanner->in_interpolation = false;
    scanner->interpolation_depth = 0;
    return scanner;
}

void tree_sitter_yuho_external_scanner_destroy(void *payload) {
    Scanner *scanner = (Scanner *)payload;
    free(scanner);
}

unsigned tree_sitter_yuho_external_scanner_serialize(void *payload, char *buffer) {
    Scanner *scanner = (Scanner *)payload;
    buffer[0] = (char)scanner->in_string;
    buffer[1] = (char)scanner->in_interpolation;
    buffer[2] = (char)scanner->interpolation_depth;
    return 3;
}

void tree_sitter_yuho_external_scanner_deserialize(void *payload, const char *buffer, unsigned length) {
    Scanner *scanner = (Scanner *)payload;
    if (length >= 3) {
        scanner->in_string = buffer[0];
        scanner->in_interpolation = buffer[1];
        scanner->interpolation_depth = buffer[2];
    } else {
        scanner->in_string = false;
        scanner->in_interpolation = false;
        scanner->interpolation_depth = 0;
    }
}

static void advance(TSLexer *lexer) {
    lexer->advance(lexer, false);
}

static void skip(TSLexer *lexer) {
    lexer->advance(lexer, true);
}

static bool is_identifier_start(int32_t c) {
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '_';
}

static bool is_identifier_continue(int32_t c) {
    return is_identifier_start(c) || (c >= '0' && c <= '9');
}

/*
 * Return an identifier token only when the next non-trivia token is `{`.
 * `mark_end` keeps the token itself limited to the identifier; the regular
 * extras rules still own whitespace and comments before the brace.
 */
static bool scan_typed_struct_literal_type_name(TSLexer *lexer) {
    if (!is_identifier_start(lexer->lookahead)) {
        return false;
    }

    do {
        advance(lexer);
    } while (is_identifier_continue(lexer->lookahead));
    lexer->mark_end(lexer);

    while (iswspace(lexer->lookahead)) {
        advance(lexer);
    }

    if (lexer->lookahead == '{') {
        lexer->result_symbol = TYPED_STRUCT_LITERAL_TYPE_NAME;
        return true;
    }

    return false;
}

/**
 * Scan string content, handling escape sequences and interpolation
 * String interpolation uses ${...} syntax
 */
static bool scan_string_content(TSLexer *lexer, Scanner *scanner) {
    bool has_content = false;

    while (true) {
        if (lexer->lookahead == '\0' || lexer->eof(lexer)) {
            // Unterminated string
            break;
        }

        if (lexer->lookahead == '"') {
            // End of string - don't consume
            break;
        }

        if (lexer->lookahead == '\\') {
            // Escape sequence - consume backslash and next char
            advance(lexer);
            if (lexer->lookahead != '\0' && !lexer->eof(lexer)) {
                advance(lexer);
                has_content = true;
            }
            continue;
        }

        if (lexer->lookahead == '$') {
            advance(lexer);
            if (lexer->lookahead == '{') {
                // Start of interpolation - backup by marking result
                lexer->result_symbol = INTERPOLATION_START;
                advance(lexer);
                scanner->in_interpolation = true;
                scanner->interpolation_depth = 1;
                return true;
            }
            // Just a dollar sign in string
            has_content = true;
            continue;
        }

        // Regular string content
        advance(lexer);
        has_content = true;
    }

    if (has_content) {
        lexer->result_symbol = STRING_CONTENT;
        return true;
    }

    return false;
}

/**
 * Scan for interpolation end (closing brace that matches opening)
 */
static bool scan_interpolation_end(TSLexer *lexer, Scanner *scanner) {
    if (scanner->in_interpolation && lexer->lookahead == '}') {
        scanner->interpolation_depth--;
        if (scanner->interpolation_depth == 0) {
            advance(lexer);
            scanner->in_interpolation = false;
            lexer->result_symbol = INTERPOLATION_END;
            return true;
        }
    }
    return false;
}

bool tree_sitter_yuho_external_scanner_scan(
    void *payload,
    TSLexer *lexer,
    const bool *valid_symbols
) {
    Scanner *scanner = (Scanner *)payload;

    // Skip whitespace
    while (iswspace(lexer->lookahead)) {
        skip(lexer);
    }

    // Check for interpolation end
    if (valid_symbols[INTERPOLATION_END] && scanner->in_interpolation) {
        if (scan_interpolation_end(lexer, scanner)) {
            return true;
        }
    }

    // Track brace depth inside interpolation
    if (scanner->in_interpolation) {
        if (lexer->lookahead == '{') {
            scanner->interpolation_depth++;
        }
    }

    // Check for string content
    if (valid_symbols[STRING_CONTENT] && scanner->in_string) {
        return scan_string_content(lexer, scanner);
    }

    if (valid_symbols[TYPED_STRUCT_LITERAL_TYPE_NAME]) {
        return scan_typed_struct_literal_type_name(lexer);
    }

    return false;
}
