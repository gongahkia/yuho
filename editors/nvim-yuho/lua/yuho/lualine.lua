-- Lualine integration for Yuho
-- Shows current statute section in statusline

local M = {}

-- Cache for section info
local cache = {
  section = nil,
  bufnr = nil,
  tick = nil,
}

-- Get current statute section from LSP
local function get_current_section()
  local bufnr = vim.api.nvim_get_current_buf()
  
  -- Check cache
  local tick = vim.api.nvim_buf_get_changedtick(bufnr)
  if cache.bufnr == bufnr and cache.tick == tick then
    return cache.section
  end
  
  -- Only for yuho files
  local ft = vim.bo[bufnr].filetype
  if ft ~= "yuho" then
    return nil
  end
  
  -- Get clients
  local clients = vim.lsp.get_active_clients({ bufnr = bufnr, name = "yuho" })
  if #clients == 0 then
    return nil
  end
  
  -- Get document symbols
  local params = vim.lsp.util.make_position_params()
  local results = vim.lsp.buf_request_sync(bufnr, "textDocument/documentSymbol", params, 500)
  
  if not results then
    return nil
  end
  
  -- Find enclosing statute
  local cursor = vim.api.nvim_win_get_cursor(0)
  local line = cursor[1] - 1
  local col = cursor[2]
  
  local section = nil
  
  for _, result in pairs(results) do
    if result.result then
      for _, symbol in ipairs(result.result) do
        -- Check if this is a statute and cursor is within
        if symbol.kind == 5 then -- Class kind (statute)
          local range = symbol.range
          if line >= range.start.line and line <= range["end"].line then
            -- Found enclosing statute
            section = symbol.name
            -- Check for statute section in detail
            if symbol.detail then
              local sec = symbol.detail:match("section:%s*(.+)")
              if sec then
                section = sec
              end
            end
          end
        end
      end
    end
  end
  
  -- Update cache
  cache.bufnr = bufnr
  cache.tick = tick
  cache.section = section
  
  return section
end

-- Component for lualine
function M.section()
  local section = get_current_section()
  if section then
    return "§" .. section
  end
  return ""
end

-- Icon component
function M.icon()
  local ft = vim.bo.filetype
  if ft == "yuho" then
    return "⚖"
  end
  return ""
end

-- Full component with icon and section
function M.full()
  local section = get_current_section()
  if section then
    return "⚖ §" .. section
  end
  local ft = vim.bo.filetype
  if ft == "yuho" then
    return "⚖ Yuho"
  end
  return ""
end

-- Color function for component
function M.color()
  return { fg = "#61afef", gui = "bold" }
end

-- Condition function - only show for yuho files
function M.condition()
  return vim.bo.filetype == "yuho"
end

-- Setup lualine component
function M.setup(opts)
  opts = opts or {}
  
  local ok, lualine = pcall(require, "lualine")
  if not ok then
    vim.notify("lualine not found, skipping integration", vim.log.levels.DEBUG)
    return
  end
  
  -- Return component configuration for user to use
  return {
    M.full,
    icon = "⚖",
    color = M.color,
    cond = M.condition,
  }
end

return M
