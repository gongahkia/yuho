-- lua/yuho/mermaid_preview.lua
-- Live Mermaid Preview Window module
-- Displays mermaid diagram output from yuho transpile in floating window

local M = {}

-- State for preview management
M.state = {
  preview_buf = nil,
  preview_win = nil,
  source_buf = nil,
  autocmd_id = nil,
  timer = nil,
  enabled = false,
}

-- Namespace for mermaid syntax highlights
M.ns_id = vim.api.nvim_create_namespace("yuho_mermaid")

--- Setup highlight groups for mermaid syntax
function M.setup_highlights()
  vim.api.nvim_set_hl(0, "YuhoMermaidKeyword", { fg = "#c678dd", bold = true })
  vim.api.nvim_set_hl(0, "YuhoMermaidNode", { fg = "#61afef" })
  vim.api.nvim_set_hl(0, "YuhoMermaidEdge", { fg = "#98c379" })
  vim.api.nvim_set_hl(0, "YuhoMermaidLabel", { fg = "#e5c07b" })
  vim.api.nvim_set_hl(0, "YuhoMermaidComment", { fg = "#5c6370", italic = true })
end

--- Create floating window for mermaid preview
--- @return number buf Buffer handle
--- @return number win Window handle
local function create_float_window()
  -- Calculate window dimensions
  local width = math.floor(vim.o.columns * 0.4)
  local height = math.floor(vim.o.lines * 0.7)
  local col = vim.o.columns - width - 2
  local row = 2
  
  -- Create buffer
  local buf = vim.api.nvim_create_buf(false, true)
  vim.api.nvim_buf_set_option(buf, "buftype", "nofile")
  vim.api.nvim_buf_set_option(buf, "bufhidden", "wipe")
  vim.api.nvim_buf_set_option(buf, "swapfile", false)
  vim.api.nvim_buf_set_name(buf, "Yuho Mermaid Preview")
  
  -- Create floating window
  local win = vim.api.nvim_open_win(buf, false, {
    relative = "editor",
    width = width,
    height = height,
    col = col,
    row = row,
    style = "minimal",
    border = "rounded",
    title = " 📊 Mermaid Preview ",
    title_pos = "center",
  })
  
  -- Window options
  vim.api.nvim_win_set_option(win, "wrap", true)
  vim.api.nvim_win_set_option(win, "cursorline", false)
  vim.api.nvim_win_set_option(win, "number", false)
  vim.api.nvim_win_set_option(win, "relativenumber", false)
  vim.api.nvim_win_set_option(win, "signcolumn", "no")
  
  return buf, win
end

--- Apply basic mermaid syntax highlighting
--- @param buf number
local function apply_mermaid_highlights(buf)
  local lines = vim.api.nvim_buf_get_lines(buf, 0, -1, false)
  
  vim.api.nvim_buf_clear_namespace(buf, M.ns_id, 0, -1)
  
  for lnum, line in ipairs(lines) do
    -- Keywords (graph, flowchart, subgraph, end)
    local keywords = { "graph", "flowchart", "subgraph", "end", "direction" }
    for _, kw in ipairs(keywords) do
      local start = line:find(kw, 1, true)
      if start then
        vim.api.nvim_buf_add_highlight(buf, M.ns_id, "YuhoMermaidKeyword", lnum - 1, start - 1, start - 1 + #kw)
      end
    end
    
    -- Node IDs (alphanumeric at start of edges)
    local node_pattern = "^%s*([%w_]+)"
    local node_start, node_end, node = line:find(node_pattern)
    if node then
      vim.api.nvim_buf_add_highlight(buf, M.ns_id, "YuhoMermaidNode", lnum - 1, node_start - 1, node_end)
    end
    
    -- Edge arrows
    local arrow_patterns = { "-->", "---", "==>", "-.->", "-->" }
    for _, arrow in ipairs(arrow_patterns) do
      local astart = line:find(arrow, 1, true)
      if astart then
        vim.api.nvim_buf_add_highlight(buf, M.ns_id, "YuhoMermaidEdge", lnum - 1, astart - 1, astart - 1 + #arrow)
      end
    end
    
    -- Labels in brackets
    local label_start, label_end = line:find("%[.-%]")
    if label_start then
      vim.api.nvim_buf_add_highlight(buf, M.ns_id, "YuhoMermaidLabel", lnum - 1, label_start - 1, label_end)
    end
    
    -- Labels in braces
    local brace_start, brace_end = line:find("{.-}")
    if brace_start then
      vim.api.nvim_buf_add_highlight(buf, M.ns_id, "YuhoMermaidLabel", lnum - 1, brace_start - 1, brace_end)
    end
    
    -- Comments
    if line:match("^%s*%%") then
      vim.api.nvim_buf_add_highlight(buf, M.ns_id, "YuhoMermaidComment", lnum - 1, 0, -1)
    end
  end
end

--- Run yuho transpile -t mermaid and update preview
--- @param source_buf number
function M.update_preview(source_buf)
  if not M.state.preview_buf or not vim.api.nvim_buf_is_valid(M.state.preview_buf) then
    return
  end
  
  local filepath = vim.api.nvim_buf_get_name(source_buf)
  if filepath == "" or not filepath:match("%.yh$") then
    return
  end
  
  -- Create temp file with current buffer content (in case unsaved)
  local lines = vim.api.nvim_buf_get_lines(source_buf, 0, -1, false)
  local tmpfile = vim.fn.tempname() .. ".yh"
  vim.fn.writefile(lines, tmpfile)
  
  -- Run yuho transpile
  vim.fn.jobstart({ "yuho", "transpile", "-t", "mermaid", tmpfile }, {
    stdout_buffered = true,
    on_stdout = function(_, data)
      if data and #data > 0 then
        -- Filter empty lines at end
        while #data > 0 and data[#data] == "" do
          table.remove(data)
        end
        
        vim.schedule(function()
          if M.state.preview_buf and vim.api.nvim_buf_is_valid(M.state.preview_buf) then
            vim.api.nvim_buf_set_option(M.state.preview_buf, "modifiable", true)
            vim.api.nvim_buf_set_lines(M.state.preview_buf, 0, -1, false, data)
            vim.api.nvim_buf_set_option(M.state.preview_buf, "modifiable", false)
            apply_mermaid_highlights(M.state.preview_buf)
          end
        end)
      end
    end,
    on_stderr = function(_, data)
      if data and #data > 0 and data[1] ~= "" then
        vim.schedule(function()
          if M.state.preview_buf and vim.api.nvim_buf_is_valid(M.state.preview_buf) then
            vim.api.nvim_buf_set_option(M.state.preview_buf, "modifiable", true)
            vim.api.nvim_buf_set_lines(M.state.preview_buf, 0, -1, false, {
              "-- Error transpiling to mermaid --",
              "",
              unpack(data),
            })
            vim.api.nvim_buf_set_option(M.state.preview_buf, "modifiable", false)
          end
        end)
      end
    end,
    on_exit = function()
      -- Clean up temp file
      vim.fn.delete(tmpfile)
    end,
  })
end

--- Setup buffer watcher for auto-update
--- @param source_buf number
local function setup_buffer_watcher(source_buf)
  -- Clear existing autocmd
  if M.state.autocmd_id then
    pcall(vim.api.nvim_del_autocmd, M.state.autocmd_id)
  end
  
  local group = vim.api.nvim_create_augroup("YuhoMermaidPreview", { clear = true })
  
  -- Update on text change (debounced)
  M.state.autocmd_id = vim.api.nvim_create_autocmd({ "TextChanged", "TextChangedI" }, {
    group = group,
    buffer = source_buf,
    callback = function()
      -- Debounce: cancel pending timer and schedule new one
      if M.state.timer then
        vim.fn.timer_stop(M.state.timer)
      end
      M.state.timer = vim.fn.timer_start(500, function()
        vim.schedule(function()
          M.update_preview(source_buf)
        end)
      end)
    end,
    desc = "Update mermaid preview on text change",
  })
  
  -- Close preview when source buffer closes
  vim.api.nvim_create_autocmd("BufUnload", {
    group = group,
    buffer = source_buf,
    callback = function()
      M.close()
    end,
    desc = "Close mermaid preview when source closes",
  })
  
  -- Update on save
  vim.api.nvim_create_autocmd("BufWritePost", {
    group = group,
    buffer = source_buf,
    callback = function()
      M.update_preview(source_buf)
    end,
    desc = "Update mermaid preview on save",
  })
end

--- Open mermaid preview window
function M.open()
  local source_buf = vim.api.nvim_get_current_buf()
  local filepath = vim.api.nvim_buf_get_name(source_buf)
  
  -- Validate file
  if not filepath:match("%.yh$") then
    vim.notify("Mermaid preview only works with .yh files", vim.log.levels.ERROR)
    return
  end
  
  -- Close existing preview if open
  if M.state.preview_win and vim.api.nvim_win_is_valid(M.state.preview_win) then
    vim.api.nvim_win_close(M.state.preview_win, true)
  end
  
  -- Create new preview window
  M.state.preview_buf, M.state.preview_win = create_float_window()
  M.state.source_buf = source_buf
  M.state.enabled = true
  
  -- Setup buffer watcher
  setup_buffer_watcher(source_buf)
  
  -- Initial render
  M.update_preview(source_buf)
  
  -- Setup keybinding to close preview
  vim.api.nvim_buf_set_keymap(M.state.preview_buf, "n", "q", "", {
    callback = function()
      M.close()
    end,
    noremap = true,
    silent = true,
    desc = "Close mermaid preview",
  })
  
  vim.notify("Mermaid preview opened (press 'q' in preview to close)", vim.log.levels.INFO)
end

--- Close mermaid preview window
function M.close()
  -- Stop timer
  if M.state.timer then
    vim.fn.timer_stop(M.state.timer)
    M.state.timer = nil
  end
  
  -- Clear autocmds
  if M.state.autocmd_id then
    pcall(vim.api.nvim_del_autocmd, M.state.autocmd_id)
    M.state.autocmd_id = nil
  end
  
  pcall(vim.api.nvim_del_augroup_by_name, "YuhoMermaidPreview")
  
  -- Close window
  if M.state.preview_win and vim.api.nvim_win_is_valid(M.state.preview_win) then
    vim.api.nvim_win_close(M.state.preview_win, true)
  end
  
  M.state = {
    preview_buf = nil,
    preview_win = nil,
    source_buf = nil,
    autocmd_id = nil,
    timer = nil,
    enabled = false,
  }
end

--- Toggle mermaid preview window
function M.toggle()
  if M.state.enabled and M.state.preview_win and vim.api.nvim_win_is_valid(M.state.preview_win) then
    M.close()
    vim.notify("Mermaid preview closed", vim.log.levels.INFO)
  else
    M.open()
  end
end

--- Setup mermaid preview module
function M.setup()
  M.setup_highlights()
  
  -- Register commands
  vim.api.nvim_create_user_command("YuhoMermaid", function()
    M.toggle()
  end, {
    desc = "Toggle Yuho mermaid preview window",
  })
  
  vim.api.nvim_create_user_command("YuhoMermaidOpen", function()
    M.open()
  end, {
    desc = "Open Yuho mermaid preview window",
  })
  
  vim.api.nvim_create_user_command("YuhoMermaidClose", function()
    M.close()
  end, {
    desc = "Close Yuho mermaid preview window",
  })
end

return M
