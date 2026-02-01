/**
 * @license
 * Copyright 2023 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export const toolbox = {
    kind: 'categoryToolbox',
    contents: [
        {
            kind: 'category',
            name: 'Variables',
            categorystyle: 'variable_category',
            contents: [
                { kind: 'block', type: 'variables_set' }, // For variable declaration
                { kind: 'block', type: 'variables_get' }, // For accessing variables
            ],
        },
        {
            kind: 'category',
            name: 'Data Types',
            categorystyle: 'data_type_category',
            contents: [
                { kind: 'block', type: 'data_integer' },
                { kind: 'block', type: 'data_float' },
                { kind: 'block', type: 'data_string' },
                { kind: 'block', type: 'data_boolean' },
                { kind: 'block', type: 'data_money' },
                { kind: 'block', type: 'data_date' },
                { kind: 'block', type: 'data_duration' },
            ],
        },
        {
            kind: 'category',
            name: 'Structs',
            categorystyle: 'struct_category',
            contents: [
                { kind: 'block', type: 'struct_define' },
                { kind: 'block', type: 'struct_access' },
            ],
        },
        {
            kind: 'category',
            name: 'Functions',
            categorystyle: 'function_category',
            contents: [
                { kind: 'block', type: 'function_define' },
                { kind: 'block', type: 'function_call' },
            ],
        },
        {
            kind: 'category',
            name: 'Control Structures',
            categorystyle: 'control_category',
            contents: [
                { kind: 'block', type: 'match_case' },
                { kind: 'block', type: 'assert_block' },
            ],
        },
    ],
};
