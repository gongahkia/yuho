/**
 * @license
 * Copyright 2023 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * @license
 * Copyright 2023 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import * as Blockly from 'blockly/core';

// Define code generation for blocks
export const forBlock = Object.create(null);

// Code generation for data types
forBlock['data_integer'] = function (block) {
    const value = block.getFieldValue('VALUE');
    return [`${value}`, Blockly.JavaScript.ORDER_ATOMIC];
};

forBlock['data_float'] = function (block) {
    const value = block.getFieldValue('VALUE');
    return [`${value}`, Blockly.JavaScript.ORDER_ATOMIC];
};

forBlock['data_string'] = function (block) {
    const value = block.getFieldValue('VALUE');
    return [`"${value}"`, Blockly.JavaScript.ORDER_ATOMIC];
};

forBlock['data_boolean'] = function (block) {
    const dropdownValue = block.getFieldValue('VALUE');
    return [dropdownValue === "TRUE" ? "true" : "false", Blockly.JavaScript.ORDER_ATOMIC];
};

forBlock['data_money'] = function (block) {
    const value = block.getFieldValue('VALUE');
    return [`${value}`, Blockly.JavaScript.ORDER_ATOMIC];
};

forBlock['data_date'] = function (block) {
    const value = block.getFieldValue('VALUE');
    return [`"${value}"`, Blockly.JavaScript.ORDER_ATOMIC];
};

forBlock['data_duration'] = function (block) {
    const value = block.getFieldValue('VALUE');
    return [`"${value}"`, Blockly.JavaScript.ORDER_ATOMIC];
};

// Code generation for structs
forBlock['struct_define'] = function (block) {
   const structName = block.getFieldValue('STRUCT_NAME');
   return `struct ${structName} {\n  /* define fields here */\n}\n`;
};

forBlock['struct_access'] = function (block) {
   const structName = block.getFieldValue('STRUCT_NAME');
   const fieldName = block.getFieldValue('FIELD_NAME');
   return `${structName}.${fieldName}`;
};

// Code generation for functions
forBlock['function_define'] = function (block) {
   const funcName = block.getFieldValue('FUNC_NAME');
   const params = block.getFieldValue('PARAMS');
   return `func ${funcName}(${params}) {\n  /* function body */\n}\n`;
};

forBlock['function_call'] = function (block) {
   const funcName = block.getFieldValue('FUNC_NAME');
   const args = block.getFieldValue('ARGS');
   return `${funcName}(${args});\n`;
};

// Code generation for match-case constructs
forBlock['match_case'] = function (block) {
   const valueToMatch = block.getFieldValue('VALUE');
   return `match ${valueToMatch} {\n  /* cases go here */\n}\n`;
};

// Code generation for assertions
forBlock['assert_block'] = function (block) {
   const assertionCode = Blockly.JavaScript.valueToCode(block, 'ASSERTION', Blockly.JavaScript.ORDER_NONE) || '';
   return `assert ${assertionCode};\n`;
};
