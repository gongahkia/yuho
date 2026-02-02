-- Which-key integration for Yuho
-- Provides organized keybinding hints

local M = {}

-- Default which-key mappings
M.mappings = {
  y = {
    name = "+Yuho",
    e = { "<cmd>lua require('yuho').explain_statute()<cr>", "Explain statute" },
    t = { "<cmd>lua require('yuho').transpile()<cr>", "Transpile to JSON" },
    c = { "<cmd>lua require('yuho').check()<cr>", "Check file" },
    v = { "<cmd>lua require('yuho').verify()<cr>", "Verify with Alloy" },
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
    },
    d = {
      name = "+Diagnostics",
      n = { "<cmd>lua vim.diagnostic.goto_next()<cr>", "Next diagnostic" },
      p = { "<cmd>lua vim.diagnostic.goto_prev()<cr>", "Prev diagnostic" },
      l = { "<cmd>lua vim.diagnostic.setloclist()<cr>", "List all" },
      f = { "<cmd>lua vim.diagnostic.open_float()<cr>", "Show float" },
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
