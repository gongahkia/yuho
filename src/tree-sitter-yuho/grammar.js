/**
 * tree-sitter grammar for Yuho v5
 * A domain-specific language for encoding legal statutes
 */

module.exports = grammar({
  name: 'yuho',

  // External scanner for context-sensitive tokens
  externals: $ => [
    $._string_content_external,
    $.interpolation_start,
    $.interpolation_end,
    $._error_sentinel,
  ],

  extras: $ => [
    /\s/,
    $.comment,
    $.multiline_comment,
  ],

  word: $ => $.identifier,

  // Conflict handling for error recovery
  conflicts: $ => [
    // Allow recovery when statement/expression boundaries are ambiguous
    [$.variable_declaration, $.expression_statement],
    [$.assignment_statement, $.expression_statement],
    // Match arm body can be expression or pass
    [$.match_arm],
    // Return statement with optional expression
    [$.return_statement],
    // pass can be statement or expression
    [$.pass_statement, $.pass_expression],
    // struct literal vs various statement boundaries
    [$.struct_literal, $.expression_statement],
    [$.struct_literal, $.assert_statement],
    [$.struct_literal, $.return_statement],
    [$.struct_literal, $.variable_declaration],
    [$.struct_literal, $.assignment_statement],
    // duration literal with multiple parts
    [$.duration_literal],
  ],

  // Inline rules that don't need their own node types
  inline: $ => [
    $._declaration,
    $._statement,
    $._expression,
    $._literal,
    $._pattern,
    $._type,
    $._lvalue,
  ],

  rules: {
    // =========================================================================
    // Program structure
    // =========================================================================

    source_file: $ => repeat($._declaration),

    _declaration: $ => choice(
      $.struct_definition,
      $.function_definition,
      $.statute_block,
      $.import_statement,
      $.referencing_statement,
      $.variable_declaration,
    ),

    // =========================================================================
    // Comments (single-line //, multi-line /* */, doc-comments ///)
    // =========================================================================

    comment: $ => token(seq('//', /.*/)),

    multiline_comment: $ => token(seq(
      '/*',
      /[^*]*\*+([^/*][^*]*\*+)*/,
      '/'
    )),

    doc_comment: $ => token(seq('///', /.*/)),

    // =========================================================================
    // Literals: int, float, bool, string with escape sequences
    // =========================================================================

    _literal: $ => choice(
      $.integer_literal,
      $.float_literal,
      $.boolean_literal,
      $.string_literal,
      $.money_literal,
      $.percent_literal,
      $.date_literal,
      $.duration_literal,
    ),

    integer_literal: $ => token(seq(
      optional('-'),
      /[0-9]+/
    )),

    float_literal: $ => token(seq(
      optional('-'),
      /[0-9]+/,
      '.',
      /[0-9]+/
    )),

    boolean_literal: $ => choice('TRUE', 'FALSE'),

    string_literal: $ => seq(
      '"',
      repeat(choice(
        $.escape_sequence,
        $._string_content,
      )),
      '"'
    ),

    _string_content: $ => token.immediate(prec(1, /[^"\\]+/)),

    escape_sequence: $ => token.immediate(seq(
      '\\',
      choice(
        /[\\'"nbrt0]/,       // common escapes: \\ \' \" \n \b \r \t \0
        /x[0-9a-fA-F]{2}/,   // hex escape: \xNN
        /u[0-9a-fA-F]{4}/,   // unicode escape: \uNNNN
        /u\{[0-9a-fA-F]+\}/, // unicode code point: \u{N...}
      )
    )),

    // =========================================================================
    // Legal-native types: money, percent, date, duration
    // =========================================================================

    money_literal: $ => seq(
      $.currency_symbol,
      $.money_amount,
    ),

    currency_symbol: $ => choice(
      '$',      // SGD, USD, AUD, etc.
      '£',      // GBP
      '€',      // EUR
      '¥',      // JPY, CNY
      '₹',      // INR
      'SGD',
      'USD',
      'EUR',
      'GBP',
      'JPY',
      'CNY',
      'INR',
      'AUD',
    ),

    money_amount: $ => token(seq(
      /[0-9]{1,3}/,
      repeat(seq(',', /[0-9]{3}/)),
      optional(seq('.', /[0-9]{2}/))
    )),

    percent_literal: $ => prec(7, seq(
      $.integer_literal,
      token.immediate('%')
    )),

    // ISO8601 date: YYYY-MM-DD
    date_literal: $ => token(seq(
      /[0-9]{4}/,
      '-',
      /[0-9]{2}/,
      '-',
      /[0-9]{2}/
    )),

    duration_literal: $ => seq(
      $.integer_literal,
      $.duration_unit,
      repeat(seq(
        optional(','),
        $.integer_literal,
        $.duration_unit
      ))
    ),

    duration_unit: $ => choice(
      'year', 'years',
      'month', 'months',
      'day', 'days',
      'hour', 'hours',
      'minute', 'minutes',
      'second', 'seconds',
    ),

    // =========================================================================
    // Struct definitions and literals
    // =========================================================================

    struct_definition: $ => seq(
      'struct',
      field('name', $.identifier),
      optional($.type_parameters),
      '{',
      repeat($.field_definition),
      '}'
    ),

    type_parameters: $ => seq(
      '<',
      sepBy1(',', $.identifier),
      '>'
    ),

    field_definition: $ => seq(
      field('type', $._type),
      field('name', $.identifier),
      optional(','),
    ),

    struct_literal: $ => seq(
      optional(field('type_name', $.identifier)),
      '{',
      repeat($.field_assignment),
      '}'
    ),

    field_assignment: $ => seq(
      field('name', $.identifier),
      ':=',
      field('value', $._expression),
      optional(','),
    ),

    // =========================================================================
    // Match-case expressions with pattern guards and wildcards
    // =========================================================================

    match_expression: $ => seq(
      'match',
      optional(seq('(', field('scrutinee', $._expression), ')')),
      '{',
      repeat($.match_arm),
      '}'
    ),

    match_arm: $ => seq(
      'case',
      field('pattern', $._pattern),
      optional(seq('if', field('guard', $._expression))),
      ':=',
      'consequence',
      field('body', $._expression),
      optional(';'),
    ),

    _pattern: $ => choice(
      $.wildcard_pattern,
      $.literal_pattern,
      $.binding_pattern,
      $.struct_pattern,
    ),

    wildcard_pattern: $ => '_',

    literal_pattern: $ => $._literal,

    binding_pattern: $ => $.identifier,

    struct_pattern: $ => seq(
      field('type_name', $.identifier),
      '{',
      sepBy(',', $.field_pattern),
      '}'
    ),

    field_pattern: $ => seq(
      field('name', $.identifier),
      optional(seq(':', field('pattern', $._pattern)))
    ),

    // =========================================================================
    // Function definitions
    // =========================================================================

    function_definition: $ => seq(
      'fn',
      field('name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      optional(seq(':', field('return_type', $._type))),
      $.block,
    ),

    parameter_list: $ => sepBy1(',', $.parameter),

    parameter: $ => seq(
      field('type', $._type),
      field('name', $.identifier),
    ),

    block: $ => seq(
      '{',
      repeat($._statement),
      '}'
    ),

    // =========================================================================
    // Statute blocks
    // =========================================================================

    statute_block: $ => seq(
      'statute',
      field('section_number', $.section_number),
      optional(field('title', $.string_literal)),
      '{',
      repeat($._statute_member),
      '}'
    ),

    section_number: $ => token(seq(
      optional('S'),
      /[0-9]+/,
      optional(seq('.', /[0-9]+/)),
      optional(/[A-Za-z]/),
    )),

    _statute_member: $ => choice(
      $.definitions_block,
      $.elements_block,
      $.penalty_block,
      $.illustration_block,
    ),

    definitions_block: $ => seq(
      'definitions',
      '{',
      repeat($.definition_entry),
      '}'
    ),

    definition_entry: $ => seq(
      field('term', $.identifier),
      ':=',
      field('definition', $.string_literal),
      optional(';'),
    ),

    elements_block: $ => seq(
      'elements',
      '{',
      repeat($.element_entry),
      '}'
    ),

    element_entry: $ => seq(
      field('element_type', choice('actus_reus', 'mens_rea', 'circumstance')),
      field('name', $.identifier),
      ':=',
      field('description', $._expression),
      optional(';'),
    ),

    penalty_block: $ => seq(
      'penalty',
      '{',
      optional($.imprisonment_clause),
      optional($.fine_clause),
      optional($.supplementary_clause),
      '}'
    ),

    imprisonment_clause: $ => seq(
      'imprisonment',
      ':=',
      choice(
        $.duration_literal,
        $.duration_range,
      ),
      optional(';'),
    ),

    fine_clause: $ => seq(
      'fine',
      ':=',
      choice(
        $.money_literal,
        $.money_range,
      ),
      optional(';'),
    ),

    supplementary_clause: $ => seq(
      'supplementary',
      ':=',
      $.string_literal,
      optional(';'),
    ),

    duration_range: $ => seq(
      $.duration_literal,
      '..',
      $.duration_literal,
    ),

    money_range: $ => seq(
      $.money_literal,
      '..',
      $.money_literal,
    ),

    illustration_block: $ => seq(
      'illustration',
      optional(field('label', $.identifier)),
      '{',
      field('description', $.string_literal),
      '}'
    ),

    // =========================================================================
    // Import statements
    // =========================================================================

    import_statement: $ => seq(
      'import',
      choice(
        seq('{', sepBy1(',', $.identifier), '}', 'from', $.import_path),
        seq('*', 'from', $.import_path),
        $.import_path,
      ),
      optional(';'),
    ),

    // Referencing statement for test files to import statutes
    referencing_statement: $ => seq(
      'referencing',
      field('path', $.reference_path),
      optional(';'),
    ),

    reference_path: $ => /[a-zA-Z_][a-zA-Z_0-9]*(?:\/[a-zA-Z_][a-zA-Z_0-9]*)*/,

    import_path: $ => seq(
      '"',
      /[^"]+/,
      '"'
    ),

    // =========================================================================
    // Types
    // =========================================================================

    _type: $ => choice(
      $.builtin_type,
      $.identifier,
      $.generic_type,
      $.optional_type,
      $.array_type,
    ),

    builtin_type: $ => choice(
      'int',
      'float',
      'bool',
      'string',
      'money',
      'percent',
      'date',
      'duration',
      'void',
    ),

    generic_type: $ => seq(
      $.identifier,
      '<',
      sepBy1(',', $._type),
      '>'
    ),

    optional_type: $ => seq(
      $._type,
      '?'
    ),

    array_type: $ => seq(
      '[',
      $._type,
      ']'
    ),

    // =========================================================================
    // Statements
    // =========================================================================

    _statement: $ => choice(
      $.variable_declaration,
      $.assignment_statement,
      $.expression_statement,
      $.return_statement,
      $.pass_statement,
      $.assert_statement,
    ),

    assert_statement: $ => seq(
      'assert',
      field('condition', $._expression),
      optional(seq(',', field('message', $.string_literal))),
      optional(';'),
    ),

    variable_declaration: $ => seq(
      field('type', $._type),
      field('name', $.identifier),
      optional(seq(':=', field('value', $._expression))),
      optional(';'),
    ),

    assignment_statement: $ => seq(
      field('target', $._lvalue),
      ':=',
      field('value', $._expression),
      optional(';'),
    ),

    _lvalue: $ => choice(
      $.identifier,
      $.field_access,
      $.index_access,
    ),

    expression_statement: $ => seq(
      $._expression,
      optional(';'),
    ),

    return_statement: $ => seq(
      'return',
      optional($._expression),
      optional(';'),
    ),

    pass_statement: $ => seq(
      'pass',
      optional(';'),
    ),

    // =========================================================================
    // Expressions
    // =========================================================================

    _expression: $ => choice(
      $._literal,
      $.identifier,
      $.field_access,
      $.index_access,
      $.function_call,
      $.binary_expression,
      $.unary_expression,
      $.parenthesized_expression,
      $.match_expression,
      $.struct_literal,
      $.pass_expression,
    ),

    pass_expression: $ => 'pass',

    field_access: $ => prec.left(10, seq(
      field('base', $._expression),
      '.',
      field('field', $.identifier),
    )),

    index_access: $ => prec.left(10, seq(
      field('base', $._expression),
      '[',
      field('index', $._expression),
      ']',
    )),

    function_call: $ => prec.left(9, seq(
      field('callee', choice($.identifier, $.field_access)),
      '(',
      optional($.argument_list),
      ')',
    )),

    argument_list: $ => sepBy1(',', $._expression),

    binary_expression: $ => choice(
      // Logical OR (lowest precedence)
      prec.left(1, seq($._expression, '||', $._expression)),
      // Logical AND
      prec.left(2, seq($._expression, '&&', $._expression)),
      // Comparison
      prec.left(3, seq($._expression, choice('==', '!='), $._expression)),
      prec.left(4, seq($._expression, choice('<', '>', '<=', '>='), $._expression)),
      // Additive
      prec.left(5, seq($._expression, choice('+', '-'), $._expression)),
      // Multiplicative
      prec.left(6, seq($._expression, choice('*', '/', '%'), $._expression)),
    ),

    unary_expression: $ => prec.right(8, seq(
      choice('!', '-'),
      $._expression,
    )),

    parenthesized_expression: $ => seq(
      '(',
      $._expression,
      ')',
    ),

    // =========================================================================
    // Identifiers
    // =========================================================================

    identifier: $ => /[a-zA-Z_][a-zA-Z_0-9]*/,
  },
});

// Helper function for comma-separated lists
function sepBy1(sep, rule) {
  return seq(rule, repeat(seq(sep, rule)));
}

function sepBy(sep, rule) {
  return optional(sepBy1(sep, rule));
}
