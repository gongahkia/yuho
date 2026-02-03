-- Which-key integration for Yuho
-- Provides organized keybinding hints

local M = {}

-- Default which-key mappings
M.mappings = {
  y = {
    name = "+Yuho",
    e = { "<cmd>lua require('yuho').explain_statute()<cr>", "Explain statute (English)" },
    t = { "<cmd>lua require('yuho').transpile()<cr>", "Transpile to JSON" },
    c = { "<cmd>lua require('yuho').check()<cr>", "Check file" },
    v = { "<cmd>lua require('yuho').verify()<cr>", "Transpile to Alloy" },
    L = { "<cmd>lua require('yuho').lint()<cr>", "Lint file" },
    a = { "<cmd>lua require('yuho').show_ast()<cr>", "Show AST tree" },
    p = { "<cmd>lua require('yuho').preview()<cr>", "Live preview in browser" },
    l = {
      name = "+LSP",
      r = { "<cmd>lua vim.lsp.buf.references()<cr>", "References" },
      d = { "<cmd>lua vim.lsp.buf.definition()<cr>", "Definition" },
      h = { "<cmd>lua vim.lsp.buf.hover()<cr>", "Hover docs" },
      n = { "<cmd>lua vim.lsp.buf.rename()<cr>", "Rename" },
      a = { "<cmd>lua vim.lsp.buf.code_action()<cr>", "Code action" },
      f = { "<cmd>lua vim.lsp.buf.format({ async = true })<cr>", "Format" },
    },
    s = {
      name = "+Statute",
      s = { "<cmd>Telescope yuho symbols<cr>", "Search symbols" },
      e = { "<cmd>Telescope yuho elements<cr>", "Search elements" },
      i = { "<cmd>Telescope yuho illustrations<cr>", "Search illustrations" },
      S = { "<cmd>Telescope yuho statutes<cr>", "Search statutes" },
    },
    d = {
      name = "+Diagnostics",
      n = { "<cmd>lua vim.diagnostic.goto_next()<cr>", "Next diagnostic" },
      p = { "<cmd>lua vim.diagnostic.goto_prev()<cr>", "Prev diagnostic" },
      l = { "<cmd>lua vim.diagnostic.setloclist()<cr>", "List all" },
      f = { "<cmd>lua vim.diagnostic.open_float()<cr>", "Show float" },
    },
    T = {
      name = "+Transpile to",
      j = { "<cmd>lua require('yuho').transpile_to('json')<cr>", "JSON" },
      J = { "<cmd>lua require('yuho').transpile_to('jsonld')<cr>", "JSON-LD" },
      e = { "<cmd>lua require('yuho').transpile_to('english')<cr>", "English" },
      l = { "<cmd>lua require('yuho').transpile_to('latex')<cr>", "LaTeX" },
      m = { "<cmd>lua require('yuho').transpile_to('mermaid')<cr>", "Mermaid" },
      a = { "<cmd>lua require('yuho').transpile_to('alloy')<cr>", "Alloy" },
      g = { "<cmd>lua require('yuho').transpile_to('graphql')<cr>", "GraphQL" },
      b = { "<cmd>lua require('yuho').transpile_to('blocks')<cr>", "Blocks" },
    },
  },
}

-- Setup which-key integration
function M.setup(opts)
  opts = opts or {}
  local prefix = opts.prefix or "<leader>"
  
  local ok, wk = pcall(require, "which-key")
  if not ok then
    vim.notify("which-key not found, skipping integration", vim.log.levels.DEBUG)
    return
  end
  
  -- Register mappings
  wk.register(M.mappings, { prefix = prefix })
  
  -- Visual mode mappings
  wk.register({
    y = {
      name = "+Yuho",
      e = { "<cmd>lua require('yuho').explain_selection()<cr>", "Explain selection" },
    },
  }, { prefix = prefix, mode = "v" })
end

return M
