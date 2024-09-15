module struct

open util/ordering[Time]
open util/boolean
open grammarCore

assert StructsHaveUniqueNames {
    all disj s1, s2: Struct | s1.name != s2.name
}

assert StructFieldsHaveUniqueNames {
    all s: Struct | all disj f1, f2: s.fields | f1.fieldName != f2.fieldName
}

assert StructFieldsHaveValidTypes {
    all s: Struct | all f: s.fields | f.fieldType in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

assert StructFieldsHaveValues {
    all sl: StructLiteral | all f: sl.fieldValues | some f.value
}

fact StructsFact {
    some s: Struct | some s.fields
}

fact UniqueStructNamesFact {
    all disj s1, s2: Struct | s1.name != s2.name
}

fact UniqueStructFieldNamesFact {
    all s: Struct | all disj f1, f2: s.fields | f1.fieldName != f2.fieldName
}

fact ValidStructFieldTypesFact {
    all s: Struct | all f: s.fields | f.fieldType in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

fact StructFieldValuesFact {
    all sl: StructLiteral | all f: sl.fieldValues | some f.value
}

check StructsHaveUniqueNames for 25
check StructFieldsHaveUniqueNames for 25
check StructFieldsHaveValidTypes for 25
check StructFieldsHaveValues for 25

run {} for 25
