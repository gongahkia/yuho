-- lua/yuho/diff.lua
-- Statute Diff Split View module for comparing .yh files
-- Provides semantic diff coloring and navigation

local M = {}

-- Namespace for diff highlights
M.ns_id = vim.api.nvim_create_namespace("yuho_diff")

-- Setup highlight groups for semantic diff coloring
function M.setup_highlights()
  vim.api.nvim_set_hl(0, "YuhoDiffAdd", { fg = "#98c379", bg = "#2d3c2d", bold = true })
  vim.api.nvim_set_hl(0, "YuhoDiffDelete", { fg = "#e06c75", bg = "#3c2d2d", bold = true })
  vim.api.nvim_set_hl(0, "YuhoDiffChange", { fg = "#e5c07b", bg = "#3c3c2d", bold = true })
end

-- Internal state for diff tracking
M.state = {
  left_buf = nil,
  right_buf = nil,
  diff_lines = {}, -- { lnum, type: "add"|"delete"|"change" }
  current_diff_idx = 0,
}

--- Parse diff lines between two buffers
--- @param left_lines string[]
--- @param right_lines string[]
--- @return table[] Array of {left_lnum, right_lnum, type}
local function compute_diff(left_lines, right_lines)
  local diffs = {}
  local left_len = #left_lines
  local right_len = #right_lines
  
  -- Simple line-by-line diff (LCS-based would be better but this is functional)
  local i, j = 1, 1
  while i <= left_len or j <= right_len do
    if i > left_len then
      -- Right has extra lines (additions)
      table.insert(diffs, { left_lnum = nil, right_lnum = j, type = "add" })
      j = j + 1
    elseif j > right_len then
      -- Left has extra lines (deletions)
      table.insert(diffs, { left_lnum = i, right_lnum = nil, type = "delete" })
      i = i + 1
    elseif left_lines[i] == right_lines[j] then
      -- Lines match
      i = i + 1
      j = j + 1
    else
      -- Lines differ
      -- Look ahead to find if this is a change or insert/delete
      local found_in_right = false
      for k = j + 1, math.min(j + 3, right_len) do
        if left_lines[i] == right_lines[k] then
          -- Left line found later in right, so right has additions
          for m = j, k - 1 do
            table.insert(diffs, { left_lnum = nil, right_lnum = m, type = "add" })
          end
          j = k
          found_in_right = true
          break
        end
      end
      
      if not found_in_right then
        local found_in_left = false
        for k = i + 1, math.min(i + 3, left_len) do
          if left_lines[k] == right_lines[j] then
            -- Right line found later in left, so left has deletions
            for m = i, k - 1 do
              table.insert(diffs, { left_lnum = m, right_lnum = nil, type = "delete" })
            end
            i = k
            found_in_left = true
            break
          end
        end
        
        if not found_in_left then
          -- Lines are changed
          table.insert(diffs, { left_lnum = i, right_lnum = j, type = "change" })
          i = i + 1
          j = j + 1
        end
      end
    end
  end
  
  return diffs
end

--- Apply diff highlights to buffers
--- @param left_buf number
--- @param right_buf number
--- @param diffs table[]
local function apply_highlights(left_buf, right_buf, diffs)
  -- Clear existing highlights
  vim.api.nvim_buf_clear_namespace(left_buf, M.ns_id, 0, -1)
  vim.api.nvim_buf_clear_namespace(right_buf, M.ns_id, 0, -1)
  
  for _, diff in ipairs(diffs) do
    if diff.type == "add" and diff.right_lnum then
      vim.api.nvim_buf_add_highlight(right_buf, M.ns_id, "YuhoDiffAdd", diff.right_lnum - 1, 0, -1)
    elseif diff.type == "delete" and diff.left_lnum then
      vim.api.nvim_buf_add_highlight(left_buf, M.ns_id, "YuhoDiffDelete", diff.left_lnum - 1, 0, -1)
    elseif diff.type == "change" then
      if diff.left_lnum then
        vim.api.nvim_buf_add_highlight(left_buf, M.ns_id, "YuhoDiffChange", diff.left_lnum - 1, 0, -1)
      end
      if diff.right_lnum then
        vim.api.nvim_buf_add_highlight(right_buf, M.ns_id, "YuhoDiffChange", diff.right_lnum - 1, 0, -1)
      end
    end
  end
end

--- Open two .yh files in vertical split with diff highlighting
--- @param file1 string Path to first file
--- @param file2 string Path to second file
function M.open_diff(file1, file2)
  if not file1 or not file2 then
    vim.notify("Usage: :YuhoDiff <file1> <file2>", vim.log.levels.ERROR)
    return
  end
  
  -- Validate files exist and are .yh files
  if vim.fn.filereadable(file1) ~= 1 then
    vim.notify("File not found: " .. file1, vim.log.levels.ERROR)
    return
  end
  if vim.fn.filereadable(file2) ~= 1 then
    vim.notify("File not found: " .. file2, vim.log.levels.ERROR)
    return
  end
  
  -- Setup highlights
  M.setup_highlights()
  
  -- Open files in vertical split
  vim.cmd("vsplit " .. vim.fn.fnameescape(file1))
  local left_win = vim.api.nvim_get_current_win()
  local left_buf = vim.api.nvim_get_current_buf()
  
  vim.cmd("vsplit " .. vim.fn.fnameescape(file2))
  local right_win = vim.api.nvim_get_current_win()
  local right_buf = vim.api.nvim_get_current_buf()
  
  -- Get buffer contents
  local left_lines = vim.api.nvim_buf_get_lines(left_buf, 0, -1, false)
  local right_lines = vim.api.nvim_buf_get_lines(right_buf, 0, -1, false)
  
  -- Compute and store diffs
  local diffs = compute_diff(left_lines, right_lines)
  M.state = {
    left_buf = left_buf,
    right_buf = right_buf,
    left_win = left_win,
    right_win = right_win,
    diff_lines = diffs,
    current_diff_idx = 0,
  }
  
  -- Apply highlights
  apply_highlights(left_buf, right_buf, diffs)
  
  -- Enable scroll binding for synchronized scrolling
  vim.api.nvim_win_call(left_win, function()
    vim.wo.scrollbind = true
    vim.wo.cursorbind = true
  end)
  vim.api.nvim_win_call(right_win, function()
    vim.wo.scrollbind = true
    vim.wo.cursorbind = true
  end)
  
  -- Setup diff navigation keybindings for these buffers
  M.setup_navigation_keybindings(left_buf)
  M.setup_navigation_keybindings(right_buf)
  
  vim.notify(string.format("Diff mode: %d changes found", #diffs), vim.log.levels.INFO)
end

--- Navigate to next diff change
function M.next_diff()
  if #M.state.diff_lines == 0 then
    vim.notify("No diffs to navigate", vim.log.levels.WARN)
    return
  end
  
  M.state.current_diff_idx = M.state.current_diff_idx + 1
  if M.state.current_diff_idx > #M.state.diff_lines then
    M.state.current_diff_idx = 1
  end
  
  local diff = M.state.diff_lines[M.state.current_diff_idx]
  local target_lnum = diff.left_lnum or diff.right_lnum
  
  if target_lnum then
    vim.api.nvim_win_set_cursor(0, { target_lnum, 0 })
    vim.cmd("normal! zz")
  end
end

--- Navigate to previous diff change
function M.prev_diff()
  if #M.state.diff_lines == 0 then
    vim.notify("No diffs to navigate", vim.log.levels.WARN)
    return
  end
  
  M.state.current_diff_idx = M.state.current_diff_idx - 1
  if M.state.current_diff_idx < 1 then
    M.state.current_diff_idx = #M.state.diff_lines
  end
  
  local diff = M.state.diff_lines[M.state.current_diff_idx]
  local target_lnum = diff.left_lnum or diff.right_lnum
  
  if target_lnum then
    vim.api.nvim_win_set_cursor(0, { target_lnum, 0 })
    vim.cmd("normal! zz")
  end
end

--- Setup ]c and [c keybindings for diff navigation
--- @param bufnr number
function M.setup_navigation_keybindings(bufnr)
  local opts = { noremap = true, silent = true, buffer = bufnr }
  
  vim.keymap.set("n", "]c", function()
    M.next_diff()
  end, vim.tbl_extend("force", opts, { desc = "Next diff change" }))
  
  vim.keymap.set("n", "[c", function()
    M.prev_diff()
  end, vim.tbl_extend("force", opts, { desc = "Previous diff change" }))
end

--- Close diff view and clear state
function M.close_diff()
  if M.state.left_buf then
    vim.api.nvim_buf_clear_namespace(M.state.left_buf, M.ns_id, 0, -1)
  end
  if M.state.right_buf then
    vim.api.nvim_buf_clear_namespace(M.state.right_buf, M.ns_id, 0, -1)
  end
  
  -- Disable scroll binding
  if M.state.left_win and vim.api.nvim_win_is_valid(M.state.left_win) then
    vim.api.nvim_win_call(M.state.left_win, function()
      vim.wo.scrollbind = false
      vim.wo.cursorbind = false
    end)
  end
  if M.state.right_win and vim.api.nvim_win_is_valid(M.state.right_win) then
    vim.api.nvim_win_call(M.state.right_win, function()
      vim.wo.scrollbind = false
      vim.wo.cursorbind = false
    end)
  end
  
  M.state = {
    left_buf = nil,
    right_buf = nil,
    diff_lines = {},
    current_diff_idx = 0,
  }
  
  vim.notify("Diff mode closed", vim.log.levels.INFO)
end

--- Interactive file picker for diff (prompts for second file)
function M.diff_prompt()
  local current_file = vim.api.nvim_buf_get_name(0)
  
  if current_file == "" or vim.fn.fnamemodify(current_file, ":e") ~= "yh" then
    vim.notify("Current file must be a .yh file", vim.log.levels.ERROR)
    return
  end
  
  vim.ui.input({ prompt = "Diff with file: ", completion = "file" }, function(file2)
    if file2 and file2 ~= "" then
      M.open_diff(current_file, file2)
    end
  end)
end

--- Setup commands and keybindings
function M.setup()
  M.setup_highlights()
  
  -- Register :YuhoDiff command
  vim.api.nvim_create_user_command("YuhoDiff", function(opts)
    local args = vim.split(opts.args, " ")
    if #args == 2 then
      M.open_diff(args[1], args[2])
    elseif #args == 1 then
      local current = vim.api.nvim_buf_get_name(0)
      M.open_diff(current, args[1])
    else
      M.diff_prompt()
    end
  end, {
    nargs = "*",
    complete = "file",
    desc = "Open Yuho statute diff view",
  })
  
  -- Register :YuhoDiffClose command
  vim.api.nvim_create_user_command("YuhoDiffClose", function()
    M.close_diff()
  end, {
    desc = "Close Yuho diff view",
  })
end

return M
