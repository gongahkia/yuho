-- lua/yuho/hints.lua
-- Diagnostic Inline Hints module
-- Provides custom virtual text for warnings and missing elements

local M = {}

-- Namespace for hints
M.ns_id = vim.api.nvim_create_namespace("yuho_hints")

--- Setup highlight groups for hints
function M.setup_highlights()
  vim.api.nvim_set_hl(0, "YuhoHint", { fg = "#5c6370", italic = true })
  vim.api.nvim_set_hl(0, "YuhoHintWarn", { fg = "#e5c07b", italic = true })
  vim.api.nvim_set_hl(0, "YuhoHintError", { fg = "#e06c75", italic = true })
  vim.api.nvim_set_hl(0, "YuhoHintInfo", { fg = "#61afef", italic = true })
end

-- Checks to run on statute files
M.checks = {
  -- Check for missing elements block
  missing_elements = {
    pattern = "^%s*statute%s+",
    check = function(lines, lnum)
      -- Find if there's an elements block after this statute
      local in_statute = true
      local has_elements = false
      local depth = 0
      
      for i = lnum, math.min(lnum + 100, #lines) do
        local line = lines[i]
        
        -- Track braces
        for _ in line:gmatch("{") do depth = depth + 1 end
        for _ in line:gmatch("}") do depth = depth - 1 end
        
        if depth <= 0 and i > lnum then
          in_statute = false
          break
        end
        
        if line:match("^%s*elements%s*{") or line:match("^%s*elements%s*$") then
          has_elements = true
          break
        end
      end
      
      if not has_elements then
        return {
          text = "⚠ Missing elements block",
          hl = "YuhoHintWarn",
        }
      end
      return nil
    end,
  },
  
  -- Check for missing penalty block
  missing_penalty = {
    pattern = "^%s*statute%s+",
    check = function(lines, lnum)
      local has_penalty = false
      local depth = 0
      
      for i = lnum, math.min(lnum + 150, #lines) do
        local line = lines[i]
        
        for _ in line:gmatch("{") do depth = depth + 1 end
        for _ in line:gmatch("}") do depth = depth - 1 end
        
        if depth <= 0 and i > lnum then
          break
        end
        
        if line:match("^%s*penalty%s*{") or line:match("^%s*penalty%s*$") then
          has_penalty = true
          break
        end
      end
      
      if not has_penalty then
        return {
          text = "⚠ Missing penalty block",
          hl = "YuhoHintWarn",
        }
      end
      return nil
    end,
  },
  
  -- Check for missing actus_reus in elements
  missing_actus_reus = {
    pattern = "^%s*elements%s*{",
    check = function(lines, lnum)
      local depth = 1
      local has_actus_reus = false
      
      for i = lnum + 1, math.min(lnum + 50, #lines) do
        local line = lines[i]
        
        for _ in line:gmatch("{") do depth = depth + 1 end
        for _ in line:gmatch("}") do depth = depth - 1 end
        
        if depth <= 0 then break end
        
        if line:match("actus_reus") then
          has_actus_reus = true
          break
        end
      end
      
      if not has_actus_reus then
        return {
          text = "💡 Consider adding actus_reus element",
          hl = "YuhoHintInfo",
        }
      end
      return nil
    end,
  },
  
  -- Check for missing mens_rea in elements
  missing_mens_rea = {
    pattern = "^%s*elements%s*{",
    check = function(lines, lnum)
      local depth = 1
      local has_mens_rea = false
      
      for i = lnum + 1, math.min(lnum + 50, #lines) do
        local line = lines[i]
        
        for _ in line:gmatch("{") do depth = depth + 1 end
        for _ in line:gmatch("}") do depth = depth - 1 end
        
        if depth <= 0 then break end
        
        if line:match("mens_rea") then
          has_mens_rea = true
          break
        end
      end
      
      if not has_mens_rea then
        return {
          text = "💡 Consider adding mens_rea element",
          hl = "YuhoHintInfo",
        }
      end
      return nil
    end,
  },
  
  -- Check for empty penalty block
  empty_penalty = {
    pattern = "^%s*penalty%s*{%s*}",
    check = function(lines, lnum)
      return {
        text = "⚠ Empty penalty block",
        hl = "YuhoHintWarn",
      }
    end,
  },
  
  -- Check for section without title
  missing_title = {
    pattern = 'section:%s*"[^"]*"',
    check = function(lines, lnum)
      -- Look for title in nearby lines
      for i = math.max(1, lnum - 5), math.min(#lines, lnum + 5) do
        if lines[i]:match('title:%s*"[^"]+"') then
          return nil
        end
      end
      return {
        text = "💡 Consider adding title property",
        hl = "YuhoHintInfo",
      }
    end,
  },
  
  -- Warn about very long imprisonment range
  long_imprisonment = {
    pattern = "imprisonment%s*%(%s*Y%s*:%s*(%d+)%s*,%s*(%d+)",
    check = function(lines, lnum, matches)
      local min_val = tonumber(matches[1])
      local max_val = tonumber(matches[2])
      
      if max_val and max_val > 20 then
        return {
          text = "⚠ Long imprisonment (>" .. max_val .. "Y)",
          hl = "YuhoHintWarn",
        }
      end
      return nil
    end,
  },
  
  -- Check for TODO comments
  todo_comment = {
    pattern = "//%s*TODO",
    check = function(lines, lnum)
      return {
        text = "📝 TODO",
        hl = "YuhoHint",
      }
    end,
  },
  
  -- Check for FIXME comments
  fixme_comment = {
    pattern = "//%s*FIXME",
    check = function(lines, lnum)
      return {
        text = "🔧 FIXME",
        hl = "YuhoHintError",
      }
    end,
  },
}

--- Run all checks on buffer and return hints
--- @param bufnr number
--- @return table[] Array of {lnum, text, hl}
function M.analyze_buffer(bufnr)
  local lines = vim.api.nvim_buf_get_lines(bufnr, 0, -1, false)
  local hints = {}
  
  for lnum, line in ipairs(lines) do
    for name, check_def in pairs(M.checks) do
      -- Check if pattern matches
      local matches = { line:match(check_def.pattern) }
      if #matches > 0 or (matches[1] == nil and line:match(check_def.pattern)) then
        local hint = check_def.check(lines, lnum, matches)
        if hint then
          table.insert(hints, {
            lnum = lnum,
            text = hint.text,
            hl = hint.hl,
          })
        end
      end
    end
  end
  
  return hints
end

--- Display hints as virtual text
--- @param bufnr number|nil
function M.display_hints(bufnr)
  bufnr = bufnr or vim.api.nvim_get_current_buf()
  
  -- Check if this is a .yh file
  local filename = vim.api.nvim_buf_get_name(bufnr)
  if not filename:match("%.yh$") then
    return
  end
  
  -- Clear existing hints
  vim.api.nvim_buf_clear_namespace(bufnr, M.ns_id, 0, -1)
  
  -- Analyze and display
  local hints = M.analyze_buffer(bufnr)
  
  for _, hint in ipairs(hints) do
    pcall(vim.api.nvim_buf_set_extmark, bufnr, M.ns_id, hint.lnum - 1, 0, {
      virt_text = { { "  " .. hint.text, hint.hl } },
      virt_text_pos = "eol",
      hl_mode = "combine",
    })
  end
end

--- Configure vim.diagnostic for Yuho
function M.configure_diagnostics()
  vim.diagnostic.config({
    virtual_text = {
      prefix = "●",
      source = "if_many",
      format = function(diagnostic)
        -- Shorten message for inline display
        local msg = diagnostic.message
        if #msg > 50 then
          msg = msg:sub(1, 47) .. "..."
        end
        return msg
      end,
    },
    float = {
      source = "always",
      border = "rounded",
      header = "Yuho Diagnostic",
    },
    signs = true,
    underline = true,
    update_in_insert = false,
    severity_sort = true,
  }, M.ns_id)
  
  -- Define diagnostic signs
  local signs = {
    { name = "DiagnosticSignError", text = "✘" },
    { name = "DiagnosticSignWarn", text = "⚠" },
    { name = "DiagnosticSignInfo", text = "ℹ" },
    { name = "DiagnosticSignHint", text = "💡" },
  }
  
  for _, sign in ipairs(signs) do
    vim.fn.sign_define(sign.name, {
      texthl = sign.name,
      text = sign.text,
      numhl = "",
    })
  end
end

--- Toggle hints display
function M.toggle()
  local bufnr = vim.api.nvim_get_current_buf()
  local extmarks = vim.api.nvim_buf_get_extmarks(bufnr, M.ns_id, 0, -1, {})
  
  if #extmarks > 0 then
    vim.api.nvim_buf_clear_namespace(bufnr, M.ns_id, 0, -1)
    vim.notify("Hints hidden", vim.log.levels.INFO)
  else
    M.display_hints(bufnr)
    vim.notify("Hints shown", vim.log.levels.INFO)
  end
end

--- Setup autocmds for hint updates
function M.setup_autocmds()
  local group = vim.api.nvim_create_augroup("YuhoHints", { clear = true })
  
  -- Update on buffer enter
  vim.api.nvim_create_autocmd({ "BufEnter", "BufWinEnter" }, {
    group = group,
    pattern = "*.yh",
    callback = function(args)
      M.display_hints(args.buf)
    end,
    desc = "Display Yuho hints on buffer enter",
  })
  
  -- Update on save
  vim.api.nvim_create_autocmd("BufWritePost", {
    group = group,
    pattern = "*.yh",
    callback = function(args)
      M.display_hints(args.buf)
    end,
    desc = "Update Yuho hints on save",
  })
  
  -- Debounced update on text change
  vim.api.nvim_create_autocmd({ "TextChanged", "TextChangedI" }, {
    group = group,
    pattern = "*.yh",
    callback = function(args)
      vim.defer_fn(function()
        if vim.api.nvim_buf_is_valid(args.buf) then
          M.display_hints(args.buf)
        end
      end, 500)
    end,
    desc = "Update Yuho hints on change",
  })
end

--- Setup hints module
function M.setup()
  M.setup_highlights()
  M.configure_diagnostics()
  M.setup_autocmds()
  
  -- Register commands
  vim.api.nvim_create_user_command("YuhoHints", function()
    M.toggle()
  end, {
    desc = "Toggle Yuho inline hints",
  })
  
  vim.api.nvim_create_user_command("YuhoAnalyze", function()
    local hints = M.analyze_buffer(vim.api.nvim_get_current_buf())
    if #hints == 0 then
      vim.notify("No hints found", vim.log.levels.INFO)
    else
      local lines = { "Yuho Analysis:" }
      for _, h in ipairs(hints) do
        table.insert(lines, string.format("  Line %d: %s", h.lnum, h.text))
      end
      vim.notify(table.concat(lines, "\n"), vim.log.levels.INFO)
    end
  end, {
    desc = "Show Yuho analysis results",
  })
end

return M
