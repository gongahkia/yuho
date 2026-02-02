# nvim-yuho

Neovim plugin for [Yuho](https://github.com/gongahkia/yuho) - a domain-specific language for encoding legal statutes.

## Features

- 🚀 **LSP Integration**: Full Language Server Protocol support via `yuho lsp`
- 🎨 **Syntax Highlighting**: Tree-sitter based highlighting for `.yh` files
- 📐 **Automatic Indentation**: Smart indentation for Yuho constructs
- 📁 **Code Folding**: Fold statute blocks, functions, and match expressions
- ⌨️ **Keybindings**: Convenient mappings for common Yuho operations
- 📊 **Statusline Integration**: Show current statute section in lualine

## Installation

### Using [lazy.nvim](https://github.com/folke/lazy.nvim)

```lua
{
  "gongahkia/yuho",
  lazy = true,
  ft = { "yuho" },
  cmd = { "YuhoExplain", "YuhoTranspile", "YuhoCheck" },
  config = function()
    require("yuho").setup({
      lsp = {
        enabled = true,
      },
      format = {
        on_save = true,
      },
    })
  end,
}
```

### Using [packer.nvim](https://github.com/wbthomason/packer.nvim)

```lua
use {
  "gongahkia/yuho",
  ft = { "yuho" },
  config = function()
    require("yuho").setup()
  end,
}
```

## Configuration

```lua
require("yuho").setup({
  -- LSP settings
  lsp = {
    enabled = true,               -- Enable LSP
    cmd = { "yuho", "lsp" },      -- Command to start LSP server
    filetypes = { "yuho" },       -- Filetypes to attach
    root_dir = nil,               -- Root directory (auto-detected if nil)
    settings = {},                -- LSP settings
  },

  -- Formatting
  format = {
    enabled = true,               -- Enable formatting
    on_save = false,              -- Format on save
  },

  -- Diagnostics
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
    prefix = "<leader>y",         -- Prefix for Yuho keybindings
  },
})
```

## Keybindings

All keybindings use the configured prefix (default: `<leader>y`):

| Key | Action |
|-----|--------|
| `<leader>ye` | Explain statute with LLM |
| `<leader>yt` | Transpile to JSON |
| `<leader>yc` | Check file for errors |
| `<leader>yv` | Verify with Alloy (if available) |

Standard LSP keybindings are also available:

| Key | Action |
|-----|--------|
| `gd` | Go to definition |
| `gD` | Go to declaration |
| `gr` | Find references |
| `K` | Hover documentation |
| `<leader>rn` | Rename symbol |
| `<leader>ca` | Code action |
| `<leader>f` | Format document |
| `[d` / `]d` | Navigate diagnostics |

## Lualine Integration

Add Yuho section info to your statusline:

```lua
require("lualine").setup({
  sections = {
    lualine_c = {
      "filename",
      { require("yuho").lualine.section },
    },
  },
})
```

## Which-Key Integration

The plugin automatically registers with which-key if available:

```lua
local wk = require("which-key")
wk.register({
  y = {
    name = "Yuho",
    e = "Explain statute",
    t = "Transpile",
    c = "Check",
    v = "Verify",
  },
}, { prefix = "<leader>" })
```

## Telescope Integration

Search statute symbols with Telescope:

```lua
-- Add to your Telescope extensions
require("telescope").load_extension("yuho")

-- Usage
:Telescope yuho symbols
```

## Requirements

- Neovim >= 0.9.0
- [yuho](https://github.com/gongahkia/yuho) installed and in PATH
- [nvim-lspconfig](https://github.com/neovim/nvim-lspconfig) for LSP support
- [nvim-treesitter](https://github.com/nvim-treesitter/nvim-treesitter) for syntax highlighting

## Tree-sitter Grammar

The plugin includes tree-sitter queries. To use syntax highlighting, you need the
Yuho tree-sitter grammar. Add to your nvim-treesitter config:

```lua
local parser_config = require("nvim-treesitter.parsers").get_parser_configs()
parser_config.yuho = {
  install_info = {
    url = "https://github.com/gongahkia/tree-sitter-yuho",
    files = { "src/parser.c" },
    branch = "main",
  },
  filetype = "yuho",
}
```

## License

MIT
