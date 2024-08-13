module literal

open util/ordering[Time]
open util/boolean
open grammarCore

assert valid_literal_types {
  all l: Literal | l in IntegerLiteral + FloatLiteral + StringLiteral + BooleanLiteral
}

assert integer_literal_range {
  all il: IntegerLiteral | il.value >= INT_MIN and il.value <= INT_MAX
}

assert float_literal_precision {
  all fl: FloatLiteral | check_float_precision(fl)
}

assert string_literal_escape_sequences {
  all sl: StringLiteral | check_string_literal_escape_sequences(sl)
}

assert boolean_literal_values {
  all bl: BooleanLiteral | bl in True + False
}

check valid_literal_types for 25
check integer_literal_range for 25
check float_literal_precision for 25
check string_literal_escape_sequences for 25
check boolean_literal_values for 25

run {} for 100
