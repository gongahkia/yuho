-- Telescope integration for Yuho
-- Provides fuzzy finders for statute symbols, elements, and illustrations

local M = {}

local has_telescope, telescope = pcall(require, "telescope")
if not has_telescope then
  return M
end

local pickers = require("telescope.pickers")
local finders = require("telescope.finders")
local conf = require("telescope.config").values
local actions = require("telescope.actions")
local action_state = require("telescope.actions.state")
local entry_display = require("telescope.pickers.entry_display")

-- Get symbols from LSP
local function get_lsp_symbols()
  local params = vim.lsp.util.make_position_params()
  local results = vim.lsp.buf_request_sync(0, "textDocument/documentSymbol", params, 1000)
  
  if not results then
    return {}
  end
  
  local symbols = {}
  for _, result in pairs(results) do
    if result.result then
      for _, symbol in ipairs(result.result) do
        table.insert(symbols, {
          name = symbol.name,
          kind = vim.lsp.protocol.SymbolKind[symbol.kind] or "Unknown",
          range = symbol.range,
          detail = symbol.detail or "",
        })
        
        -- Also add children
        if symbol.children then
          for _, child in ipairs(symbol.children) do
            table.insert(symbols, {
              name = symbol.name .. "." .. child.name,
              kind = vim.lsp.protocol.SymbolKind[child.kind] or "Unknown",
              range = child.range,
              detail = child.detail or "",
            })
          end
        end
      end
    end
  end
  
  return symbols
end

-- Create entry display
local function make_display(entry)
  local displayer = entry_display.create({
    separator = " ",
    items = {
      { width = 30 },
      { width = 15 },
      { remaining = true },
    },
  })
  
  return displayer({
    { entry.name, "TelescopeResultsIdentifier" },
    { entry.kind, "TelescopeResultsComment" },
    { entry.detail, "TelescopeResultsComment" },
  })
end

-- Yuho symbols picker
M.symbols = function(opts)
  opts = opts or {}
  
  local symbols = get_lsp_symbols()
  
  if #symbols == 0 then
    vim.notify("No symbols found", vim.log.levels.WARN)
    return
  end
  
  pickers.new(opts, {
    prompt_title = "Yuho Symbols",
    finder = finders.new_table({
      results = symbols,
      entry_maker = function(entry)
        return {
          value = entry,
          display = make_display,
          ordinal = entry.name .. " " .. entry.kind,
          name = entry.name,
          kind = entry.kind,
          detail = entry.detail,
          lnum = entry.range.start.line + 1,
          col = entry.range.start.character + 1,
        }
      end,
    }),
    sorter = conf.generic_sorter(opts),
    previewer = conf.grep_previewer(opts),
    attach_mappings = function(prompt_bufnr, map)
      actions.select_default:replace(function()
        actions.close(prompt_bufnr)
        local selection = action_state.get_selected_entry()
        vim.api.nvim_win_set_cursor(0, { selection.lnum, selection.col - 1 })
      end)
      return true
    end,
  }):find()
end

-- Filter symbols by type
M.elements = function(opts)
  opts = opts or {}
  
  local symbols = get_lsp_symbols()
  local elements = vim.tbl_filter(function(s)
    return s.kind == "Field" or s.name:match("element")
  end, symbols)
  
  if #elements == 0 then
    vim.notify("No elements found", vim.log.levels.WARN)
    return
  end
  
  opts.prompt_title = "Yuho Elements"
  M._symbol_picker(opts, elements)
end

-- Filter for illustrations
M.illustrations = function(opts)
  opts = opts or {}
  
  local symbols = get_lsp_symbols()
  local illustrations = vim.tbl_filter(function(s)
    return s.name:match("illustration") or s.name:match("Illustration")
  end, symbols)
  
  if #illustrations == 0 then
    vim.notify("No illustrations found", vim.log.levels.WARN)
    return
  end
  
  opts.prompt_title = "Yuho Illustrations"
  M._symbol_picker(opts, illustrations)
end

-- Filter for statutes
M.statutes = function(opts)
  opts = opts or {}
  
  local symbols = get_lsp_symbols()
  local statutes = vim.tbl_filter(function(s)
    return s.kind == "Class" or s.name:match("^S%d") or s.name:match("statute")
  end, symbols)
  
  if #statutes == 0 then
    vim.notify("No statutes found", vim.log.levels.WARN)
    return
  end
  
  opts.prompt_title = "Yuho Statutes"
  M._symbol_picker(opts, statutes)
end

-- Internal symbol picker helper
M._symbol_picker = function(opts, symbols)
  pickers.new(opts, {
    prompt_title = opts.prompt_title or "Yuho Symbols",
    finder = finders.new_table({
      results = symbols,
      entry_maker = function(entry)
        return {
          value = entry,
          display = make_display,
          ordinal = entry.name .. " " .. entry.kind,
          name = entry.name,
          kind = entry.kind,
          detail = entry.detail,
          lnum = entry.range.start.line + 1,
          col = entry.range.start.character + 1,
        }
      end,
    }),
    sorter = conf.generic_sorter(opts),
    attach_mappings = function(prompt_bufnr, map)
      actions.select_default:replace(function()
        actions.close(prompt_bufnr)
        local selection = action_state.get_selected_entry()
        vim.api.nvim_win_set_cursor(0, { selection.lnum, selection.col - 1 })
      end)
      return true
    end,
  }):find()
end

-- Register as telescope extension
return telescope.register_extension({
  exports = {
    symbols = M.symbols,
    elements = M.elements,
    illustrations = M.illustrations,
    statutes = M.statutes,
  },
})
