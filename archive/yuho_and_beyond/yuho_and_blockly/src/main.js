import * as Blockly from "blockly/core";
import { toolbox } from "./toolbox.js"; // Import your toolbox definition
import "./blocks/yuho_blocks.js"; // Import the block definitions
import "./generators/javascript.js"; // Import code generators

// Initialize Blockly workspace
const workspace = Blockly.inject('blocklyDiv', {
    toolbox,
});

// Optional - Add functionality to generate code or handle events.
document.getElementById('generateCode').addEventListener('click', () => {
    const code = Blockly.JavaScript.workspaceToCode(workspace);
    console.log(code); // Output generated code to console or display it in your application.
});
