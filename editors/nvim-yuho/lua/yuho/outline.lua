-- lua/yuho/outline.lua
-- Statute Outline/TOC Panel module
-- Displays sidebar with statute structure and cursor tracking

local M = {}

-- State for outline management
M.state = {
  outline_buf = nil,
  outline_win = nil,
  source_buf = nil,
  source_win = nil,
  tree = nil,
  autocmd_group = nil,
}

-- Namespace for highlights
M.ns_id = vim.api.nvim_create_namespace("yuho_outline")

--- Setup highlight groups
function M.setup_highlights()
  vim.api.nvim_set_hl(0, "YuhoOutlineStatute", { fg = "#e5c07b", bold = true })
  vim.api.nvim_set_hl(0, "YuhoOutlineSection", { fg = "#61afef" })
  vim.api.nvim_set_hl(0, "YuhoOutlineBlock", { fg = "#98c379" })
  vim.api.nvim_set_hl(0, "YuhoOutlineFunction", { fg = "#c678dd" })
  vim.api.nvim_set_hl(0, "YuhoOutlineType", { fg = "#56b6c2" })
  vim.api.nvim_set_hl(0, "YuhoOutlineCurrent", { bg = "#3e4451", bold = true })
end

--- Node types for outline tree
M.node_types = {
  statute = { icon = "§", hl = "YuhoOutlineStatute" },
  section = { icon = "#", hl = "YuhoOutlineSection" },
  definitions = { icon = "📖", hl = "YuhoOutlineBlock" },
  elements = { icon = "⚖️", hl = "YuhoOutlineBlock" },
  penalty = { icon = "⚡", hl = "YuhoOutlineBlock" },
  illustrations = { icon = "💡", hl = "YuhoOutlineBlock" },
  exceptions = { icon = "🚫", hl = "YuhoOutlineBlock" },
  fn = { icon = "ƒ", hl = "YuhoOutlineFunction" },
  struct = { icon = "◇", hl = "YuhoOutlineType" },
  enum = { icon = "◆", hl = "YuhoOutlineType" },
}

--- Parse statute structure from buffer into tree
--- @param bufnr number
--- @return table[] Tree of {type, name, lnum, children}
function M.parse_structure(bufnr)
  local lines = vim.api.nvim_buf_get_lines(bufnr, 0, -1, false)
  local tree = {}
  local stack = { tree }
  local depth_stack = { 0 }
  
  for lnum, line in ipairs(lines) do
    -- Skip empty lines and comments
    if line:match("^%s*$") or line:match("^%s*//") then
      goto continue
    end
    
    -- Track brace depth
    local indent = #(line:match("^(%s*)") or "")
    
    -- Parse different node types
    local node = nil
    
    -- Statute definition
    local statute_name = line:match("^%s*statute%s+([%w_]+)")
    if statute_name then
      node = { type = "statute", name = statute_name, lnum = lnum, children = {} }
    end
    
    -- Section property
    local section_num = line:match('section:%s*"([^"]+)"')
    if section_num then
      node = { type = "section", name = "Section " .. section_num, lnum = lnum, children = {} }
    end
    
    -- Block types
    for block_type, _ in pairs(M.node_types) do
      if block_type ~= "statute" and block_type ~= "section" then
        local pattern = "^%s*" .. block_type .. "%s*{"
        if line:match(pattern) or line:match("^%s*" .. block_type .. "%s*$") then
          node = { type = block_type, name = block_type, lnum = lnum, children = {} }
          break
        end
      end
    end
    
    -- Function definition
    local fn_name = line:match("^%s*fn%s+([%w_]+)")
    if fn_name then
      node = { type = "fn", name = fn_name .. "()", lnum = lnum, children = {} }
    end
    
    -- Struct definition
    local struct_name = line:match("^%s*struct%s+([%w_]+)")
    if struct_name then
      node = { type = "struct", name = struct_name, lnum = lnum, children = {} }
    end
    
    -- Enum definition
    local enum_name = line:match("^%s*enum%s+([%w_]+)")
    if enum_name then
      node = { type = "enum", name = enum_name, lnum = lnum, children = {} }
    end
    
    if node then
      -- Find appropriate parent based on indentation
      while #depth_stack > 1 and depth_stack[#depth_stack] >= indent do
        table.remove(stack)
        table.remove(depth_stack)
      end
      
      -- Add node to current parent
      local parent = stack[#stack]
      table.insert(parent, node)
      
      -- Push node as potential parent for nested items
      table.insert(stack, node.children)
      table.insert(depth_stack, indent)
    end
    
    ::continue::
  end
  
  return tree
end

--- Flatten tree for display
--- @param tree table[]
--- @param level number
--- @return table[] Array of {type, name, lnum, level}
local function flatten_tree(tree, level)
  level = level or 0
  local flat = {}
  
  for _, node in ipairs(tree) do
    table.insert(flat, {
      type = node.type,
      name = node.name,
      lnum = node.lnum,
      level = level,
    })
    
    if node.children and #node.children > 0 then
      local children = flatten_tree(node.children, level + 1)
      for _, child in ipairs(children) do
        table.insert(flat, child)
      end
    end
  end
  
  return flat
end

--- Render outline tree to buffer
--- @param tree table[]
local function render_outline(tree)
  if not M.state.outline_buf or not vim.api.nvim_buf_is_valid(M.state.outline_buf) then
    return
  end
  
  local flat = flatten_tree(tree)
  M.state.flat_tree = flat
  
  local lines = {}
  local highlights = {}
  
  for i, node in ipairs(flat) do
    local node_info = M.node_types[node.type] or { icon = "•", hl = "Normal" }
    local indent = string.rep("  ", node.level)
    local line = string.format("%s%s %s", indent, node_info.icon, node.name)
    table.insert(lines, line)
    
    -- Store highlight info
    table.insert(highlights, {
      lnum = i - 1,
      hl = node_info.hl,
      col_start = #indent,
      col_end = -1,
    })
  end
  
  -- Update buffer
  vim.api.nvim_buf_set_option(M.state.outline_buf, "modifiable", true)
  vim.api.nvim_buf_set_lines(M.state.outline_buf, 0, -1, false, lines)
  vim.api.nvim_buf_set_option(M.state.outline_buf, "modifiable", false)
  
  -- Apply highlights
  vim.api.nvim_buf_clear_namespace(M.state.outline_buf, M.ns_id, 0, -1)
  for _, hl in ipairs(highlights) do
    vim.api.nvim_buf_add_highlight(M.state.outline_buf, M.ns_id, hl.hl, hl.lnum, hl.col_start, hl.col_end)
  end
end

--- Update cursor highlight in outline to match source position
function M.update_cursor_tracking()
  if not M.state.outline_buf or not vim.api.nvim_buf_is_valid(M.state.outline_buf) then
    return
  end
  
  if not M.state.flat_tree or #M.state.flat_tree == 0 then
    return
  end
  
  local cursor_lnum = vim.api.nvim_win_get_cursor(0)[1]
  
  -- Find the nearest outline node at or before cursor
  local best_match = nil
  local best_idx = nil
  
  for i, node in ipairs(M.state.flat_tree) do
    if node.lnum <= cursor_lnum then
      if not best_match or node.lnum > best_match.lnum then
        best_match = node
        best_idx = i
      end
    end
  end
  
  -- Clear existing current highlight
  vim.api.nvim_buf_clear_namespace(M.state.outline_buf, M.ns_id + 1, 0, -1)
  
  -- Highlight current node
  if best_idx then
    vim.api.nvim_buf_add_highlight(M.state.outline_buf, M.ns_id + 1, "YuhoOutlineCurrent", best_idx - 1, 0, -1)
    
    -- Scroll outline to show current item if window is valid
    if M.state.outline_win and vim.api.nvim_win_is_valid(M.state.outline_win) then
      pcall(vim.api.nvim_win_set_cursor, M.state.outline_win, { best_idx, 0 })
    end
  end
end

--- Jump to selected node in source
function M.jump_to_node()
  if not M.state.flat_tree then return end
  
  local cursor = vim.api.nvim_win_get_cursor(0)
  local idx = cursor[1]
  
  if idx > 0 and idx <= #M.state.flat_tree then
    local node = M.state.flat_tree[idx]
    
    -- Focus source window
    if M.state.source_win and vim.api.nvim_win_is_valid(M.state.source_win) then
      vim.api.nvim_set_current_win(M.state.source_win)
      vim.api.nvim_win_set_cursor(M.state.source_win, { node.lnum, 0 })
      vim.cmd("normal! zz")
    end
  end
end

--- Create outline sidebar buffer
--- @return number buf
--- @return number win
local function create_outline_window()
  -- Calculate dimensions
  local width = 35
  
  -- Create buffer
  local buf = vim.api.nvim_create_buf(false, true)
  vim.api.nvim_buf_set_option(buf, "buftype", "nofile")
  vim.api.nvim_buf_set_option(buf, "bufhidden", "wipe")
  vim.api.nvim_buf_set_option(buf, "swapfile", false)
  vim.api.nvim_buf_set_option(buf, "filetype", "yuho-outline")
  vim.api.nvim_buf_set_name(buf, "Yuho Outline")
  
  -- Create split window on left
  vim.cmd("topleft " .. width .. "vsplit")
  local win = vim.api.nvim_get_current_win()
  vim.api.nvim_win_set_buf(win, buf)
  
  -- Window options
  vim.api.nvim_win_set_option(win, "wrap", false)
  vim.api.nvim_win_set_option(win, "number", false)
  vim.api.nvim_win_set_option(win, "relativenumber", false)
  vim.api.nvim_win_set_option(win, "signcolumn", "no")
  vim.api.nvim_win_set_option(win, "foldcolumn", "0")
  vim.api.nvim_win_set_option(win, "winfixwidth", true)
  vim.api.nvim_win_set_option(win, "cursorline", true)
  
  return buf, win
end

--- Setup keybindings for outline buffer
--- @param buf number
local function setup_outline_keymaps(buf)
  local opts = { noremap = true, silent = true, buffer = buf }
  
  -- Jump to node with Enter
  vim.keymap.set("n", "<CR>", function()
    M.jump_to_node()
  end, vim.tbl_extend("force", opts, { desc = "Jump to node" }))
  
  -- Close with q
  vim.keymap.set("n", "q", function()
    M.close()
  end, vim.tbl_extend("force", opts, { desc = "Close outline" }))
  
  -- Refresh with r
  vim.keymap.set("n", "r", function()
    M.refresh()
  end, vim.tbl_extend("force", opts, { desc = "Refresh outline" }))
end

--- Refresh outline from current source
function M.refresh()
  if not M.state.source_buf or not vim.api.nvim_buf_is_valid(M.state.source_buf) then
    return
  end
  
  M.state.tree = M.parse_structure(M.state.source_buf)
  render_outline(M.state.tree)
end

--- Open outline panel
function M.open()
  local source_buf = vim.api.nvim_get_current_buf()
  local source_win = vim.api.nvim_get_current_win()
  local filepath = vim.api.nvim_buf_get_name(source_buf)
  
  -- Validate file
  if not filepath:match("%.yh$") then
    vim.notify("Outline only works with .yh files", vim.log.levels.ERROR)
    return
  end
  
  -- Close existing outline
  M.close()
  
  -- Store source info
  M.state.source_buf = source_buf
  M.state.source_win = source_win
  
  -- Create outline window
  M.state.outline_buf, M.state.outline_win = create_outline_window()
  
  -- Setup keybindings
  setup_outline_keymaps(M.state.outline_buf)
  
  -- Parse and render
  M.state.tree = M.parse_structure(source_buf)
  render_outline(M.state.tree)
  
  -- Setup cursor tracking
  M.state.autocmd_group = vim.api.nvim_create_augroup("YuhoOutline", { clear = true })
  
  vim.api.nvim_create_autocmd("CursorMoved", {
    group = M.state.autocmd_group,
    buffer = source_buf,
    callback = function()
      M.update_cursor_tracking()
    end,
    desc = "Track cursor in outline",
  })
  
  vim.api.nvim_create_autocmd({ "TextChanged", "TextChangedI" }, {
    group = M.state.autocmd_group,
    buffer = source_buf,
    callback = function()
      vim.defer_fn(function()
        M.refresh()
      end, 200)
    end,
    desc = "Update outline on change",
  })
  
  -- Focus back on source
  vim.api.nvim_set_current_win(source_win)
  
  -- Initial cursor tracking
  M.update_cursor_tracking()
end

--- Close outline panel
function M.close()
  -- Clear autocmds
  if M.state.autocmd_group then
    pcall(vim.api.nvim_del_augroup_by_id, M.state.autocmd_group)
    M.state.autocmd_group = nil
  end
  
  -- Close window
  if M.state.outline_win and vim.api.nvim_win_is_valid(M.state.outline_win) then
    vim.api.nvim_win_close(M.state.outline_win, true)
  end
  
  M.state = {
    outline_buf = nil,
    outline_win = nil,
    source_buf = nil,
    source_win = nil,
    tree = nil,
    flat_tree = nil,
    autocmd_group = nil,
  }
end

--- Toggle outline panel
function M.toggle()
  if M.state.outline_win and vim.api.nvim_win_is_valid(M.state.outline_win) then
    M.close()
  else
    M.open()
  end
end

--- Setup outline module
function M.setup()
  M.setup_highlights()
  
  -- Register commands
  vim.api.nvim_create_user_command("YuhoOutline", function()
    M.toggle()
  end, {
    desc = "Toggle Yuho outline panel",
  })
  
  vim.api.nvim_create_user_command("YuhoOutlineOpen", function()
    M.open()
  end, {
    desc = "Open Yuho outline panel",
  })
  
  vim.api.nvim_create_user_command("YuhoOutlineClose", function()
    M.close()
  end, {
    desc = "Close Yuho outline panel",
  })
end

return M
