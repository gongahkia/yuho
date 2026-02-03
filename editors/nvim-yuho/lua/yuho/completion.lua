-- lua/yuho/completion.lua
-- Smart Statute Completion module
-- Provides nvim-cmp source for Yuho files

local M = {}

local legal_terms = require("yuho.legal_terms")

-- Element types with documentation
M.element_types = {
  {
    label = "actus_reus",
    kind = "Keyword",
    documentation = "The physical/external element of a crime - the guilty act or conduct",
    detail = "Element Type",
  },
  {
    label = "mens_rea",
    kind = "Keyword",
    documentation = "The mental element of a crime - the guilty mind or intent",
    detail = "Element Type",
  },
  {
    label = "circumstance",
    kind = "Keyword",
    documentation = "Surrounding conditions that must exist for offense to occur",
    detail = "Element Type",
  },
  {
    label = "result",
    kind = "Keyword",
    documentation = "The consequence or outcome required by the offense",
    detail = "Element Type",
  },
  {
    label = "causation",
    kind = "Keyword",
    documentation = "The link between conduct and result",
    detail = "Element Type",
  },
  {
    label = "defense",
    kind = "Keyword",
    documentation = "Justification or excuse that negates liability",
    detail = "Element Type",
  },
}

-- Block keywords with documentation
M.block_keywords = {
  {
    label = "statute",
    kind = "Keyword",
    documentation = "Defines a legal statute with section, title, elements, and penalties",
    detail = "Block Type",
    insertText = "statute ${1:Name} {\n\tsection: \"${2:000}\"\n\ttitle: \"${3:Title}\"\n\t\n\telements {\n\t\t$0\n\t}\n}",
    insertTextFormat = 2, -- Snippet
  },
  {
    label = "definitions",
    kind = "Keyword",
    documentation = "Block containing defined terms used in the statute",
    detail = "Block Type",
    insertText = "definitions {\n\t${1:term}: \"${2:definition}\"\n\t$0\n}",
    insertTextFormat = 2,
  },
  {
    label = "elements",
    kind = "Keyword",
    documentation = "Block containing the elements required for the offense",
    detail = "Block Type",
    insertText = "elements {\n\t${1:element_name}: \"${2:description}\"\n\t$0\n}",
    insertTextFormat = 2,
  },
  {
    label = "penalty",
    kind = "Keyword",
    documentation = "Block specifying punishments for the offense",
    detail = "Block Type",
    insertText = "penalty {\n\timprisonment(Y: ${1:min}, ${2:max})\n\tfine(SGD: ${3:amount})\n\t$0\n}",
    insertTextFormat = 2,
  },
  {
    label = "illustrations",
    kind = "Keyword",
    documentation = "Examples showing how the statute applies in specific scenarios",
    detail = "Block Type",
    insertText = "illustrations {\n\t(a) ${1:scenario} => ${2:outcome}\n\t$0\n}",
    insertTextFormat = 2,
  },
  {
    label = "exceptions",
    kind = "Keyword",
    documentation = "Circumstances where the offense does not apply",
    detail = "Block Type",
    insertText = "exceptions {\n\t${1:exception_name}: \"${2:description}\"\n\t$0\n}",
    insertTextFormat = 2,
  },
  {
    label = "fn",
    kind = "Function",
    documentation = "Defines a function for legal tests or computations",
    detail = "Function",
    insertText = "fn ${1:name}(${2:params}) -> ${3:bool} {\n\t$0\n}",
    insertTextFormat = 2,
  },
  {
    label = "struct",
    kind = "Struct",
    documentation = "Defines a structured data type",
    detail = "Type Definition",
    insertText = "struct ${1:Name} {\n\t${2:field}: ${3:type},\n\t$0\n}",
    insertTextFormat = 2,
  },
  {
    label = "enum",
    kind = "Enum",
    documentation = "Defines an enumeration of possible values",
    detail = "Type Definition",
    insertText = "enum ${1:Name} {\n\t${2:Variant1},\n\t${3:Variant2},\n\t$0\n}",
    insertTextFormat = 2,
  },
}

-- Control flow keywords
M.control_keywords = {
  {
    label = "match",
    kind = "Keyword",
    documentation = "Pattern matching expression",
    detail = "Control Flow",
    insertText = "match ${1:expr} {\n\tcase ${2:pattern} => {\n\t\t$0\n\t}\n}",
    insertTextFormat = 2,
  },
  {
    label = "case",
    kind = "Keyword",
    documentation = "Case clause in match expression",
    detail = "Control Flow",
    insertText = "case ${1:pattern} => {\n\t$0\n}",
    insertTextFormat = 2,
  },
  {
    label = "if",
    kind = "Keyword",
    documentation = "Conditional expression",
    detail = "Control Flow",
    insertText = "if ${1:condition} {\n\t$0\n}",
    insertTextFormat = 2,
  },
  {
    label = "else",
    kind = "Keyword",
    documentation = "Alternative branch",
    detail = "Control Flow",
  },
  {
    label = "return",
    kind = "Keyword",
    documentation = "Return value from function",
    detail = "Control Flow",
    insertText = "return ${1:value}",
    insertTextFormat = 2,
  },
  {
    label = "let",
    kind = "Keyword",
    documentation = "Variable binding",
    detail = "Control Flow",
    insertText = "let ${1:name} := ${2:value}",
    insertTextFormat = 2,
  },
}

-- Types
M.types = {
  { label = "bool", kind = "Type", documentation = "Boolean type (true/false)" },
  { label = "string", kind = "Type", documentation = "Text string type" },
  { label = "int", kind = "Type", documentation = "Integer number type" },
  { label = "float", kind = "Type", documentation = "Floating-point number type" },
  { label = "date", kind = "Type", documentation = "Date type" },
  { label = "duration", kind = "Type", documentation = "Time duration type" },
  { label = "money", kind = "Type", documentation = "Monetary value type" },
  { label = "list", kind = "Type", documentation = "List/array type" },
  { label = "option", kind = "Type", documentation = "Optional value type" },
}

-- nvim-cmp source definition
M.source = {}

M.source.new = function()
  return setmetatable({}, { __index = M.source })
end

function M.source:get_trigger_characters()
  return { ".", ":", "@", "<" }
end

function M.source:is_available()
  local ft = vim.bo.filetype
  return ft == "yuho" or vim.fn.expand("%:e") == "yh"
end

function M.source:get_debug_name()
  return "yuho"
end

-- Convert items to cmp format
local function to_cmp_item(item, kind_map)
  local kind = kind_map[item.kind] or 1 -- Default to Text
  return {
    label = item.label,
    kind = kind,
    documentation = {
      kind = "markdown",
      value = string.format("**%s**\n\n%s", item.detail or item.kind, item.documentation or ""),
    },
    insertText = item.insertText,
    insertTextFormat = item.insertTextFormat or 1,
  }
end

function M.source:complete(params, callback)
  local cmp = require("cmp")
  local kind_map = {
    Text = cmp.lsp.CompletionItemKind.Text,
    Keyword = cmp.lsp.CompletionItemKind.Keyword,
    Function = cmp.lsp.CompletionItemKind.Function,
    Struct = cmp.lsp.CompletionItemKind.Struct,
    Enum = cmp.lsp.CompletionItemKind.Enum,
    Type = cmp.lsp.CompletionItemKind.TypeParameter,
    Variable = cmp.lsp.CompletionItemKind.Variable,
  }
  
  local items = {}
  
  -- Get cursor context
  local line = params.context.cursor_before_line or ""
  local col = params.context.cursor.col
  
  -- Determine context and provide appropriate completions
  local in_elements_block = line:match("elements%s*{") or M.is_in_block("elements")
  local in_penalty_block = line:match("penalty%s*{") or M.is_in_block("penalty")
  local at_top_level = not line:match("^%s+")
  
  -- Add element types in elements block
  for _, item in ipairs(M.element_types) do
    table.insert(items, to_cmp_item(item, kind_map))
  end
  
  -- Add block keywords at top level
  for _, item in ipairs(M.block_keywords) do
    table.insert(items, to_cmp_item(item, kind_map))
  end
  
  -- Add control flow keywords
  for _, item in ipairs(M.control_keywords) do
    table.insert(items, to_cmp_item(item, kind_map))
  end
  
  -- Add types
  for _, item in ipairs(M.types) do
    table.insert(items, to_cmp_item(item, kind_map))
  end
  
  -- Add legal terms
  for _, term in ipairs(legal_terms.get_all_terms()) do
    table.insert(items, {
      label = term.word,
      kind = cmp.lsp.CompletionItemKind.Text,
      documentation = {
        kind = "markdown",
        value = string.format("**%s** (%s)\n\n%s", term.word, term.category, term.info),
      },
    })
  end
  
  callback({ items = items, isIncomplete = false })
end

--- Check if cursor is inside a specific block type
--- @param block_type string
--- @return boolean
function M.is_in_block(block_type)
  local bufnr = vim.api.nvim_get_current_buf()
  local cursor = vim.api.nvim_win_get_cursor(0)
  local current_line = cursor[1]
  
  local lines = vim.api.nvim_buf_get_lines(bufnr, 0, current_line, false)
  local depth = 0
  local in_target_block = false
  
  for i = #lines, 1, -1 do
    local line = lines[i]
    
    -- Count braces
    for _ in line:gmatch("}") do
      depth = depth - 1
      if depth < 0 then
        in_target_block = false
      end
    end
    
    for _ in line:gmatch("{") do
      depth = depth + 1
    end
    
    -- Check for block start
    if depth > 0 and line:match(block_type .. "%s*{") then
      in_target_block = true
      break
    end
  end
  
  return in_target_block
end

--- Register the cmp source
function M.setup()
  local ok, cmp = pcall(require, "cmp")
  if not ok then
    vim.notify("nvim-cmp not found, Yuho completion disabled", vim.log.levels.WARN)
    return
  end
  
  cmp.register_source("yuho", M.source.new())
  
  -- Add to cmp sources for yuho filetype
  cmp.setup.filetype("yuho", {
    sources = cmp.config.sources({
      { name = "yuho", priority = 100 },
      { name = "nvim_lsp", priority = 90 },
      { name = "luasnip", priority = 80 },
      { name = "buffer", priority = 50 },
      { name = "path", priority = 40 },
    }),
  })
end

return M
