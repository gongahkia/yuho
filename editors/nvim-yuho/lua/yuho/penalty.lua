-- lua/yuho/penalty.lua
-- Inline Penalty Calculator module
-- Displays penalty ranges as virtual text in .yh files

local M = {}

-- Namespace for penalty virtual text
M.ns_id = vim.api.nvim_create_namespace("yuho_penalty")

-- Penalty patterns to match
M.patterns = {
  -- imprisonment patterns
  imprisonment = {
    -- imprisonment (Y: min, max)
    pattern = "imprisonment%s*%(%s*Y%s*:%s*(%d+)%s*,%s*(%d+)%s*%)",
    format = function(min, max)
      return string.format("imprisonment %sY-%sY", min, max)
    end,
  },
  -- imprisonment with life option
  imprisonment_life = {
    pattern = "imprisonment_life%s*%(%s*Y%s*:%s*(%d+)%s*%)",
    format = function(min)
      return string.format("imprisonment %sY-LIFE", min)
    end,
  },
  -- fine patterns
  fine = {
    pattern = "fine%s*%(%s*SGD%s*:%s*(%d+)%s*%)",
    format = function(amount)
      return string.format("fine SGD %s", M.format_currency(amount))
    end,
  },
  -- fine with range
  fine_range = {
    pattern = "fine%s*%(%s*SGD%s*:%s*(%d+)%s*,%s*(%d+)%s*%)",
    format = function(min, max)
      return string.format("fine SGD %s-%s", M.format_currency(min), M.format_currency(max))
    end,
  },
  -- caning
  caning = {
    pattern = "caning%s*%(%s*strokes%s*:%s*(%d+)%s*%)",
    format = function(strokes)
      return string.format("caning %s strokes", strokes)
    end,
  },
  caning_range = {
    pattern = "caning%s*%(%s*strokes%s*:%s*(%d+)%s*,%s*(%d+)%s*%)",
    format = function(min, max)
      return string.format("caning %s-%s strokes", min, max)
    end,
  },
  -- death penalty
  death = {
    pattern = "death%s*%(%s*%)",
    format = function()
      return "DEATH PENALTY"
    end,
  },
}

--- Format currency with thousands separator
--- @param amount string|number
--- @return string
function M.format_currency(amount)
  local num = tonumber(amount)
  if not num then return tostring(amount) end
  
  local formatted = tostring(num)
  local k
  while true do
    formatted, k = formatted:gsub("^(-?%d+)(%d%d%d)", "%1,%2")
    if k == 0 then break end
  end
  return formatted
end

--- Parse penalty block from buffer content
--- @param lines string[]
--- @return table[] Array of {lnum, penalty_text}
function M.parse_penalties(lines)
  local penalties = {}
  local in_penalty_block = false
  local penalty_start = nil
  local current_penalties = {}
  
  for lnum, line in ipairs(lines) do
    -- Check for penalty block start
    if line:match("^%s*penalty%s*{") or line:match("^%s*penalty%s*$") then
      in_penalty_block = true
      penalty_start = lnum
      current_penalties = {}
    elseif in_penalty_block then
      -- Check for block end
      if line:match("^%s*}%s*$") and penalty_start then
        in_penalty_block = false
        if #current_penalties > 0 then
          table.insert(penalties, {
            lnum = penalty_start,
            text = table.concat(current_penalties, " | "),
          })
        end
        penalty_start = nil
        current_penalties = {}
      else
        -- Parse penalty patterns
        for name, pat in pairs(M.patterns) do
          local match1, match2 = line:match(pat.pattern)
          if match1 then
            local penalty_text
            if match2 then
              penalty_text = pat.format(match1, match2)
            else
              penalty_text = pat.format(match1)
            end
            table.insert(current_penalties, penalty_text)
            -- Also add inline virtual text for this specific line
            table.insert(penalties, {
              lnum = lnum,
              text = penalty_text,
              inline = true,
            })
          end
        end
      end
    end
    
    -- Also parse standalone penalty statements (outside blocks)
    if not in_penalty_block then
      for name, pat in pairs(M.patterns) do
        local match1, match2 = line:match(pat.pattern)
        if match1 then
          local penalty_text
          if match2 then
            penalty_text = pat.format(match1, match2)
          else
            penalty_text = pat.format(match1)
          end
          table.insert(penalties, {
            lnum = lnum,
            text = penalty_text,
            inline = true,
          })
        end
      end
    end
  end
  
  return penalties
end

--- Display penalty virtual text for a buffer
--- @param bufnr number|nil
function M.display_penalties(bufnr)
  bufnr = bufnr or vim.api.nvim_get_current_buf()
  
  -- Check if this is a .yh file
  local filename = vim.api.nvim_buf_get_name(bufnr)
  if not filename:match("%.yh$") then
    return
  end
  
  -- Clear existing virtual text
  vim.api.nvim_buf_clear_namespace(bufnr, M.ns_id, 0, -1)
  
  -- Get buffer content
  local lines = vim.api.nvim_buf_get_lines(bufnr, 0, -1, false)
  
  -- Parse penalties
  local penalties = M.parse_penalties(lines)
  
  -- Display virtual text
  for _, penalty in ipairs(penalties) do
    local virt_text
    if penalty.inline then
      virt_text = { { "  ← " .. penalty.text, "YuhoPenaltyHint" } }
    else
      virt_text = { { "  📋 " .. penalty.text, "YuhoPenaltySummary" } }
    end
    
    pcall(vim.api.nvim_buf_set_extmark, bufnr, M.ns_id, penalty.lnum - 1, 0, {
      virt_text = virt_text,
      virt_text_pos = "eol",
      hl_mode = "combine",
    })
  end
end

--- Setup highlight groups for penalty display
function M.setup_highlights()
  vim.api.nvim_set_hl(0, "YuhoPenaltyHint", { fg = "#7c8f8f", italic = true })
  vim.api.nvim_set_hl(0, "YuhoPenaltySummary", { fg = "#61afef", bold = true })
end

--- Setup autocmds to update penalty virtual text on changes
function M.setup_autocmds()
  local group = vim.api.nvim_create_augroup("YuhoPenalty", { clear = true })
  
  -- Update on text change
  vim.api.nvim_create_autocmd({ "TextChanged", "TextChangedI" }, {
    group = group,
    pattern = "*.yh",
    callback = function(args)
      -- Debounce: schedule update to avoid too many calls
      vim.defer_fn(function()
        if vim.api.nvim_buf_is_valid(args.buf) then
          M.display_penalties(args.buf)
        end
      end, 100)
    end,
    desc = "Update Yuho penalty virtual text on change",
  })
  
  -- Update on buffer enter
  vim.api.nvim_create_autocmd({ "BufEnter", "BufWinEnter" }, {
    group = group,
    pattern = "*.yh",
    callback = function(args)
      M.display_penalties(args.buf)
    end,
    desc = "Update Yuho penalty virtual text on buffer enter",
  })
  
  -- Update after save
  vim.api.nvim_create_autocmd("BufWritePost", {
    group = group,
    pattern = "*.yh",
    callback = function(args)
      M.display_penalties(args.buf)
    end,
    desc = "Update Yuho penalty virtual text after save",
  })
end

--- Toggle penalty display for current buffer
function M.toggle()
  local bufnr = vim.api.nvim_get_current_buf()
  local extmarks = vim.api.nvim_buf_get_extmarks(bufnr, M.ns_id, 0, -1, {})
  
  if #extmarks > 0 then
    -- Clear if showing
    vim.api.nvim_buf_clear_namespace(bufnr, M.ns_id, 0, -1)
    vim.notify("Penalty hints hidden", vim.log.levels.INFO)
  else
    -- Show if hidden
    M.display_penalties(bufnr)
    vim.notify("Penalty hints shown", vim.log.levels.INFO)
  end
end

--- Calculate total penalty summary for current statute
--- @return string|nil
function M.get_penalty_summary()
  local bufnr = vim.api.nvim_get_current_buf()
  local lines = vim.api.nvim_buf_get_lines(bufnr, 0, -1, false)
  local penalties = M.parse_penalties(lines)
  
  if #penalties == 0 then
    return nil
  end
  
  -- Get unique penalty texts (non-inline)
  local summary = {}
  for _, p in ipairs(penalties) do
    if not p.inline then
      table.insert(summary, p.text)
    end
  end
  
  if #summary == 0 then
    -- Fall back to inline penalties
    local seen = {}
    for _, p in ipairs(penalties) do
      if p.inline and not seen[p.text] then
        table.insert(summary, p.text)
        seen[p.text] = true
      end
    end
  end
  
  return #summary > 0 and table.concat(summary, " | ") or nil
end

--- Setup penalty module
function M.setup()
  M.setup_highlights()
  M.setup_autocmds()
  
  -- Register toggle command
  vim.api.nvim_create_user_command("YuhoPenaltyToggle", function()
    M.toggle()
  end, {
    desc = "Toggle Yuho penalty virtual text display",
  })
end

return M
