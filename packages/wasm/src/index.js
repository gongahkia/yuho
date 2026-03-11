/**
 * Browser-compatible Yuho parser using tree-sitter WASM.
 *
 * Usage:
 *   import { createParser } from 'tree-sitter-yuho';
 *   const parser = await createParser();
 *   const tree = parser.parse('statute 1 "Test" { ... }');
 *   console.log(tree.rootNode.toString());
 */

let Parser;

async function initTreeSitter() {
  if (typeof window !== 'undefined') {
    // browser
    const TreeSitter = window.TreeSitter || (await import('web-tree-sitter'));
    await TreeSitter.init();
    return TreeSitter;
  } else {
    // node
    const TreeSitter = require('web-tree-sitter');
    await TreeSitter.init();
    return TreeSitter;
  }
}

async function createParser() {
  const TreeSitter = await initTreeSitter();
  const parser = new TreeSitter();
  const wasmPath = new URL('../tree-sitter-yuho.wasm', import.meta.url || __filename).pathname;
  const Lang = await TreeSitter.Language.load(wasmPath);
  parser.setLanguage(Lang);
  return parser;
}

function treeToJSON(node) {
  const result = {
    type: node.type,
    startPosition: { row: node.startPosition.row, column: node.startPosition.column },
    endPosition: { row: node.endPosition.row, column: node.endPosition.column },
    children: [],
  };
  for (let i = 0; i < node.childCount; i++) {
    result.children.push(treeToJSON(node.child(i)));
  }
  return result;
}

module.exports = { createParser, treeToJSON };
