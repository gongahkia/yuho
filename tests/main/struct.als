module struct

open util/ordering[Time]
open util/boolean
open grammarCore

assert structs_have_unique_names {
  all disj s1, s2: Struct | s1.name != s2.name
}

assert struct_fields_have_unique_names {
  all s: Struct | all disj f1, f2: s.fields | f1.field_name != f2.field_name
}

assert struct_fields_have_valid_types {
  all s: Struct | all f: s.fields | f.field_type in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

assert struct_fields_have_values {
  all sl: StructLiteral | all fv: sl.field_values | some fv.value
}

assert struct_field_type_compatibility {
  all sl: StructLiteral | let s = lookup_struct(sl.struct_name) in all fv: sl.field_values | let field = s.fields[fv.field_name] in field != null and field.field_type = fv.value.type
}

assert struct_mutability {
  all s: Struct | check_struct_mutability(s)
}

assert struct_nesting {
  all s: Struct | check_struct_nesting(s)
}

assert struct_inheritance {
  all s: Struct | check_struct_inheritance(s)
}

assert struct_polymorphism {
  all e: Expression | check_struct_polymorphism(e)
}

check structs_have_unique_names for 25
check struct_fields_have_unique_names for 25
check struct_fields_have_valid_types for 25
check struct_fields_have_values for 25
check struct_field_type_compatibility for 50
check struct_mutability for 25
check struct_nesting for 25
check struct_inheritance for 25
check struct_polymorphism for 25

run {} for 200
