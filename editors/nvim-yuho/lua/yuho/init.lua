-- nvim-yuho: Neovim plugin for Yuho language support
-- Provides LSP integration, tree-sitter highlighting, and formatting

local M = {}

-- Default configuration
M.config = {
  -- LSP settings
  lsp = {
    enabled = true,
    cmd = { "yuho", "lsp" },
    filetypes = { "yuho" },
    root_dir = nil, -- Will be set to current directory if nil
    settings = {},
  },
  -- Formatting settings
  format = {
    enabled = true,
    on_save = false,
  },
  -- Diagnostics settings
  diagnostics = {
    enabled = true,
    severity = {
      error = true,
      warning = true,
      info = true,
      hint = true,
    },
  },
  -- Keybindings
  keybindings = {
    enabled = true,
    prefix = "<leader>y",
  },
}

-- Setup function
function M.setup(opts)
  M.config = vim.tbl_deep_extend("force", M.config, opts or {})

  -- Register filetype
  vim.filetype.add({
    extension = {
      yh = "yuho",
    },
    filename = {
      ["statute.yh"] = "yuho",
    },
  })

  -- Setup LSP if enabled
  if M.config.lsp.enabled then
    M.setup_lsp()
  end

  -- Setup keybindings if enabled
  if M.config.keybindings.enabled then
    M.setup_keybindings()
  end

  -- Setup format on save if enabled
  if M.config.format.on_save then
    M.setup_format_on_save()
  end

  -- Setup diff module
  require("yuho.diff").setup()
end

-- Setup LSP client
function M.setup_lsp()
  local lspconfig = require("lspconfig")
  local configs = require("lspconfig.configs")

  -- Check if yuho config already exists
  if not configs.yuho then
    configs.yuho = {
      default_config = {
        cmd = M.config.lsp.cmd,
        filetypes = M.config.lsp.filetypes,
        root_dir = function(fname)
          return M.config.lsp.root_dir
            or lspconfig.util.root_pattern(".yuhorc", ".git")(fname)
            or lspconfig.util.path.dirname(fname)
        end,
        settings = M.config.lsp.settings,
      },
    }
  end

  -- Setup the LSP with on_attach
  lspconfig.yuho.setup({
    on_attach = M.on_attach,
    capabilities = M.get_capabilities(),
    settings = M.config.lsp.settings,
  })
end

-- On attach callback
function M.on_attach(client, bufnr)
  local bufopts = { noremap = true, silent = true, buffer = bufnr }

  -- Enable completion
  vim.bo[bufnr].omnifunc = "v:lua.vim.lsp.omnifunc"

  -- Standard LSP keybindings
  vim.keymap.set("n", "gD", vim.lsp.buf.declaration, bufopts)
  vim.keymap.set("n", "gd", vim.lsp.buf.definition, bufopts)
  vim.keymap.set("n", "K", vim.lsp.buf.hover, bufopts)
  vim.keymap.set("n", "gi", vim.lsp.buf.implementation, bufopts)
  vim.keymap.set("n", "<C-k>", vim.lsp.buf.signature_help, bufopts)
  vim.keymap.set("n", "gr", vim.lsp.buf.references, bufopts)
  vim.keymap.set("n", "<leader>rn", vim.lsp.buf.rename, bufopts)
  vim.keymap.set("n", "<leader>ca", vim.lsp.buf.code_action, bufopts)

  -- Formatting
  if M.config.format.enabled then
    vim.keymap.set("n", "<leader>f", function()
      vim.lsp.buf.format({ async = true })
    end, bufopts)
  end

  -- Diagnostics
  vim.keymap.set("n", "[d", vim.diagnostic.goto_prev, bufopts)
  vim.keymap.set("n", "]d", vim.diagnostic.goto_next, bufopts)
  vim.keymap.set("n", "<leader>e", vim.diagnostic.open_float, bufopts)
  vim.keymap.set("n", "<leader>q", vim.diagnostic.setloclist, bufopts)
end

-- Get LSP capabilities
function M.get_capabilities()
  local capabilities = vim.lsp.protocol.make_client_capabilities()

  -- Add cmp capabilities if available
  local ok, cmp_lsp = pcall(require, "cmp_nvim_lsp")
  if ok then
    capabilities = cmp_lsp.default_capabilities(capabilities)
  end

  return capabilities
end

-- Setup Yuho-specific keybindings
function M.setup_keybindings()
  local prefix = M.config.keybindings.prefix

  vim.keymap.set("n", prefix .. "e", function()
    M.explain_statute()
  end, { desc = "Explain statute" })

  vim.keymap.set("n", prefix .. "t", function()
    M.transpile()
  end, { desc = "Transpile to JSON" })

  vim.keymap.set("n", prefix .. "c", function()
    M.check()
  end, { desc = "Check file" })

  vim.keymap.set("n", prefix .. "v", function()
    M.verify()
  end, { desc = "Transpile to Alloy" })

  vim.keymap.set("n", prefix .. "L", function()
    M.lint()
  end, { desc = "Lint file" })

  vim.keymap.set("n", prefix .. "a", function()
    M.show_ast()
  end, { desc = "Show AST" })

  vim.keymap.set("n", prefix .. "p", function()
    M.preview()
  end, { desc = "Live preview" })

  vim.keymap.set("n", prefix .. "D", function()
    require("yuho.diff").diff_prompt()
  end, { desc = "Diff statutes" })

  -- Visual mode
  vim.keymap.set("v", prefix .. "e", function()
    M.explain_selection()
  end, { desc = "Explain selection" })
end

-- Setup format on save
function M.setup_format_on_save()
  vim.api.nvim_create_autocmd("BufWritePre", {
    pattern = "*.yh",
    callback = function()
      vim.lsp.buf.format({ async = false })
    end,
  })
end

-- Command functions
function M.explain_statute()
  local bufname = vim.api.nvim_buf_get_name(0)
  vim.cmd("split | terminal yuho transpile -t english " .. vim.fn.shellescape(bufname))
end

function M.explain_selection()
  -- Get visual selection
  local start_pos = vim.fn.getpos("'<")
  local end_pos = vim.fn.getpos("'>")
  local lines = vim.fn.getline(start_pos[2], end_pos[2])
  
  if type(lines) == "string" then
    lines = { lines }
  end
  
  -- Create temp file with selection
  local tmpfile = vim.fn.tempname() .. ".yh"
  vim.fn.writefile(lines, tmpfile)
  
  vim.cmd("split | terminal yuho transpile -t english " .. vim.fn.shellescape(tmpfile))
end

function M.transpile()
  local bufname = vim.api.nvim_buf_get_name(0)
  vim.cmd("split | terminal yuho transpile -t json " .. vim.fn.shellescape(bufname))
end

function M.transpile_to(target)
  local bufname = vim.api.nvim_buf_get_name(0)
  vim.cmd("split | terminal yuho transpile -t " .. target .. " " .. vim.fn.shellescape(bufname))
end

function M.check()
  local bufname = vim.api.nvim_buf_get_name(0)
  vim.cmd("!yuho check " .. vim.fn.shellescape(bufname))
end

function M.lint()
  local bufname = vim.api.nvim_buf_get_name(0)
  vim.cmd("split | terminal yuho lint " .. vim.fn.shellescape(bufname))
end

function M.verify()
  local bufname = vim.api.nvim_buf_get_name(0)
  vim.cmd("split | terminal yuho transpile -t alloy " .. vim.fn.shellescape(bufname))
end

function M.show_ast()
  local bufname = vim.api.nvim_buf_get_name(0)
  vim.cmd("split | terminal yuho ast " .. vim.fn.shellescape(bufname))
end

function M.preview()
  local bufname = vim.api.nvim_buf_get_name(0)
  vim.fn.jobstart({ "yuho", "preview", bufname }, { detach = true })
  vim.notify("Started live preview server", vim.log.levels.INFO)
end

-- Get current statute section (for statusline integration)
function M.get_current_section()
  local bufnr = vim.api.nvim_get_current_buf()
  local clients = vim.lsp.get_active_clients({ bufnr = bufnr, name = "yuho" })
  
  if #clients == 0 then
    return nil
  end

  -- Would use LSP document symbols to find current section
  -- For now, return nil
  return nil
end

-- Module for lualine integration
M.lualine = {
  section = function()
    local section = M.get_current_section()
    return section and ("§" .. section) or ""
  end,
}

return M
