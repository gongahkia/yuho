import * as Blockly from 'blockly/core';

// Define blocks for data types
Blockly.Blocks['data_integer'] = {
    init() {
        this.appendDummyInput()
            .appendField("Integer")
            .appendField(new Blockly.FieldNumber(0), "VALUE");
        this.setOutput(true, "Integer");
        this.setColour(230);
        this.setTooltip("An integer value.");
        this.setHelpUrl("");
    }
};

Blockly.Blocks['data_float'] = {
    init() {
        this.appendDummyInput()
            .appendField("Float")
            .appendField(new Blockly.FieldNumber(0.0), "VALUE");
        this.setOutput(true, "Float");
        this.setColour(230);
        this.setTooltip("A floating-point number.");
        this.setHelpUrl("");
    }
};

Blockly.Blocks['data_string'] = {
    init() {
        this.appendDummyInput()
            .appendField("String")
            .appendField(new Blockly.FieldTextInput("default"), "VALUE");
        this.setOutput(true, "String");
        this.setColour(230);
        this.setTooltip("A string value.");
        this.setHelpUrl("");
    }
};

Blockly.Blocks['data_boolean'] = {
    init() {
        this.appendDummyInput()
            .appendField("Boolean")
            .appendField(new Blockly.FieldDropdown([["TRUE", "TRUE"], ["FALSE", "FALSE"]]), "VALUE");
        this.setOutput(true, "Boolean");
        this.setColour(230);
        this.setTooltip("A boolean value.");
        this.setHelpUrl("");
    }
};

Blockly.Blocks['data_money'] = {
    init() {
        this.appendDummyInput()
            .appendField("Money")
            .appendField(new Blockly.FieldTextInput("$0.00"), "VALUE");
        this.setOutput(true, "Money");
        this.setColour(230);
        this.setTooltip("A money value.");
        this.setHelpUrl("");
    }
};

Blockly.Blocks['data_date'] = {
    init() {
        this.appendDummyInput()
            .appendField("Date")
            .appendField(new Blockly.FieldTextInput("DD-MM-YYYY"), "VALUE");
        this.setOutput(true, "Date");
        this.setColour(230);
        this.setTooltip("A date value.");
        this.setHelpUrl("");
    }
};

Blockly.Blocks['data_duration'] = {
    init() {
        this.appendDummyInput()
            .appendField("Duration")
            .appendField(new Blockly.FieldTextInput("1 day"), "VALUE");
        this.setOutput(true, "Duration");
        this.setColour(230);
        this.setTooltip("A duration value.");
        this.setHelpUrl("");
    }
};

// Define blocks for structs
Blockly.Blocks['struct_define'] = {
    init() {
        // Define a block for struct definition
        this.appendDummyInput()
            .appendField("Define Struct")
            .appendField(new Blockly.FieldTextInput("StructName"), "STRUCT_NAME");
        
        // Add fields for struct attributes (for simplicity)
        
        // Set output to void since it's a definition
        this.setPreviousStatement(true);
        this.setNextStatement(true);
        
        // Set color and tooltip
        this.setColour(290);
        this.setTooltip("Define a new struct.");
    }
};

Blockly.Blocks['struct_access'] = {
    init() {
        // Define a block for accessing struct fields
        this.appendDummyInput()
            .appendField("Access Struct")
            .appendField(new Blockly.FieldTextInput("StructName"), "STRUCT_NAME")
            .appendField(".")
            .appendField(new Blockly.FieldTextInput("fieldName"), "FIELD_NAME");
        
       // Set output to any datatype (string in general)
       this.setOutput(true);
       
       // Set color and tooltip
       this.setColour(290);
       this.setTooltip("Access a field from a struct.");
   }
};

// Define blocks for functions
Blockly.Blocks['function_define'] = {
    init() {
       // Define a block for function definition
       this.appendDummyInput()
           .appendField("Function")
           .appendField(new Blockly.FieldTextInput("funcName"), "FUNC_NAME")
           .appendField("(")
           .appendField(new Blockly.FieldTextInput("params"), "PARAMS")
           .appendField(")");
       
       // Set previous and next statements
       this.setPreviousStatement(true);
       this.setNextStatement(true);
       
       // Set color and tooltip
       this.setColour(120);
       this.setTooltip("Define a new function.");
   }
};

Blockly.Blocks['function_call'] = {
   init() {
       // Define a block for function calls
       this.appendDummyInput()
           .appendField("Call Function")
           .appendField(new Blockly.FieldTextInput("funcName"), "FUNC_NAME")
           .appendField("(")
           .appendField(new Blockly.FieldTextInput("args"), "ARGS")
           .appendField(")");
       
       // Set output to any datatype (string in general)
       this.setOutput(true);

       // Set color and tooltip
       this.setColour(120);
       this.setTooltip("Call an existing function.");
   }
};

// Define blocks for control structures (match-case)
Blockly.Blocks['match_case'] = {
   init() {
       // Define a block for match-case constructs
       this.appendDummyInput()
           .appendField("Match")
           .appendField(new Blockly.FieldTextInput("value"), "VALUE");

       // Add cases as sub-blocks or inputs

       // Set previous and next statements
       this.setPreviousStatement(true);
       this.setNextStatement(true);

       // Set color and tooltip
       this.setColour(210);
       this.setTooltip("Match-case construct for pattern matching.");
   }
};

// Define blocks for assertions
Blockly.Blocks['assert_block'] = {
   init() {
      // Define a block for assertions
      this.appendValueInput('ASSERTION')
          .setCheck('Boolean')
          .appendField('Assert');

      // Set previous and next statements
      this.setPreviousStatement(true);
      this.setNextStatement(true);

      // Set color and tooltip
      this.setColour(210);
      this.setTooltip('Assert that an expression evaluates to TRUE.');
   }
};