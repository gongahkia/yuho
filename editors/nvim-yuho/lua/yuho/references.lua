-- lua/yuho/references.lua
-- Statute Reference Jump module
-- Parses cross-references and provides navigation to referenced statutes

local M = {}

-- Reference patterns to match
M.patterns = {
  -- see "300" or see "s300"
  see_quoted = 'see%s*"([sS]?%d+)"',
  -- see section 300 or see Section 300
  see_section = "[sS]ection%s+(%d+)",
  -- (see s.300) or (see s300)
  see_s_dot = "[sS]%.?(%d+)",
  -- reference to S300 directly
  statute_ref = "S(%d+)",
  -- under section 300
  under_section = "under%s+[sS]ection%s+(%d+)",
  -- as defined in 300
  defined_in = "defined%s+in%s+(%d+)",
  -- within the meaning of section 300
  meaning_of = "meaning%s+of%s+[sS]ection%s+(%d+)",
}

-- Directories to search for statute files
M.search_dirs = {
  "library",
  "statutes",
  "library/penal_code",
}

--- Find statute file by section number
--- @param section_num string
--- @return string|nil filepath
function M.find_statute_file(section_num)
  local cwd = vim.fn.getcwd()
  
  -- Patterns to match statute filenames
  local file_patterns = {
    "s" .. section_num .. "_*.yh",
    "s" .. section_num .. ".yh",
    "*" .. section_num .. "*.yh",
  }
  
  for _, dir in ipairs(M.search_dirs) do
    local search_path = cwd .. "/" .. dir
    if vim.fn.isdirectory(search_path) == 1 then
      for _, pattern in ipairs(file_patterns) do
        local files = vim.fn.glob(search_path .. "/" .. pattern, false, true)
        if #files > 0 then
          return files[1]
        end
        -- Also check subdirectories
        local subfiles = vim.fn.glob(search_path .. "/*/" .. pattern, false, true)
        if #subfiles > 0 then
          return subfiles[1]
        end
      end
    end
  end
  
  return nil
end

--- Parse all references from current buffer
--- @param bufnr number|nil
--- @return table[] Array of {lnum, col, section_num, text}
function M.parse_references(bufnr)
  bufnr = bufnr or vim.api.nvim_get_current_buf()
  local lines = vim.api.nvim_buf_get_lines(bufnr, 0, -1, false)
  local refs = {}
  
  for lnum, line in ipairs(lines) do
    for name, pattern in pairs(M.patterns) do
      local init = 1
      while true do
        local start_pos, end_pos, section_num = line:find(pattern, init)
        if not start_pos then break end
        
        table.insert(refs, {
          lnum = lnum,
          col = start_pos,
          section_num = section_num,
          text = line:sub(start_pos, end_pos),
          pattern = name,
        })
        
        init = end_pos + 1
      end
    end
  end
  
  return refs
end

--- Get reference under cursor
--- @return table|nil {section_num, text}
function M.get_reference_at_cursor()
  local line = vim.api.nvim_get_current_line()
  local col = vim.api.nvim_win_get_cursor(0)[2] + 1
  
  for _, pattern in pairs(M.patterns) do
    local init = 1
    while true do
      local start_pos, end_pos, section_num = line:find(pattern, init)
      if not start_pos then break end
      
      -- Check if cursor is within this match
      if col >= start_pos and col <= end_pos then
        return {
          section_num = section_num,
          text = line:sub(start_pos, end_pos),
        }
      end
      
      init = end_pos + 1
    end
  end
  
  return nil
end

--- Jump to referenced statute (custom gd handler)
function M.goto_definition()
  local ref = M.get_reference_at_cursor()
  
  if not ref then
    -- Fall back to default gd
    vim.lsp.buf.definition()
    return
  end
  
  local filepath = M.find_statute_file(ref.section_num)
  
  if filepath then
    vim.cmd("edit " .. vim.fn.fnameescape(filepath))
    vim.notify("Jumped to section " .. ref.section_num, vim.log.levels.INFO)
  else
    vim.notify("Statute file for section " .. ref.section_num .. " not found", vim.log.levels.WARN)
  end
end

--- Find all statutes that reference the current statute
--- @return table[] Array of {filepath, lnum, text}
function M.find_incoming_references()
  local current_file = vim.api.nvim_buf_get_name(0)
  local current_section = nil
  
  -- Extract section number from current file
  local filename = vim.fn.fnamemodify(current_file, ":t")
  current_section = filename:match("s(%d+)")
  
  if not current_section then
    -- Try to find section from file content
    local lines = vim.api.nvim_buf_get_lines(0, 0, 50, false)
    for _, line in ipairs(lines) do
      local section = line:match('section:%s*"(%d+)"')
      if section then
        current_section = section
        break
      end
    end
  end
  
  if not current_section then
    vim.notify("Could not determine current statute section", vim.log.levels.ERROR)
    return {}
  end
  
  local incoming = {}
  local cwd = vim.fn.getcwd()
  
  -- Search all .yh files
  for _, dir in ipairs(M.search_dirs) do
    local search_path = cwd .. "/" .. dir
    if vim.fn.isdirectory(search_path) == 1 then
      local files = vim.fn.glob(search_path .. "/**/*.yh", false, true)
      
      for _, filepath in ipairs(files) do
        -- Skip current file
        if filepath ~= current_file then
          local file_lines = vim.fn.readfile(filepath)
          
          for lnum, line in ipairs(file_lines) do
            -- Check if line references current section
            for _, pattern in pairs(M.patterns) do
              local section_num = line:match(pattern)
              if section_num == current_section then
                table.insert(incoming, {
                  filepath = filepath,
                  lnum = lnum,
                  text = line,
                })
                break -- Only one entry per line
              end
            end
          end
        end
      end
    end
  end
  
  return incoming
end

--- Show incoming references in quickfix
function M.show_incoming_references()
  local refs = M.find_incoming_references()
  
  if #refs == 0 then
    vim.notify("No incoming references found", vim.log.levels.INFO)
    return
  end
  
  -- Build quickfix list
  local qf_items = {}
  for _, ref in ipairs(refs) do
    table.insert(qf_items, {
      filename = ref.filepath,
      lnum = ref.lnum,
      col = 1,
      text = ref.text:gsub("^%s+", ""),
    })
  end
  
  vim.fn.setqflist(qf_items, "r")
  vim.fn.setqflist({}, "a", { title = "Incoming References" })
  vim.cmd("copen")
  
  vim.notify(string.format("Found %d incoming references", #refs), vim.log.levels.INFO)
end

--- Show outgoing references from current file
function M.show_outgoing_references()
  local refs = M.parse_references()
  
  if #refs == 0 then
    vim.notify("No outgoing references found", vim.log.levels.INFO)
    return
  end
  
  -- Build quickfix list
  local qf_items = {}
  local current_file = vim.api.nvim_buf_get_name(0)
  
  for _, ref in ipairs(refs) do
    local target_file = M.find_statute_file(ref.section_num)
    table.insert(qf_items, {
      filename = current_file,
      lnum = ref.lnum,
      col = ref.col,
      text = string.format("→ Section %s: %s", ref.section_num, target_file or "(not found)"),
    })
  end
  
  vim.fn.setqflist(qf_items, "r")
  vim.fn.setqflist({}, "a", { title = "Outgoing References" })
  vim.cmd("copen")
  
  vim.notify(string.format("Found %d outgoing references", #refs), vim.log.levels.INFO)
end

--- Setup custom gd handler for Yuho files
function M.setup_gd_handler()
  vim.api.nvim_create_autocmd("FileType", {
    pattern = "yuho",
    callback = function(args)
      vim.keymap.set("n", "gd", function()
        M.goto_definition()
      end, {
        buffer = args.buf,
        noremap = true,
        silent = true,
        desc = "Go to statute definition",
      })
    end,
    desc = "Setup Yuho gd handler",
  })
end

--- Setup references module
function M.setup()
  M.setup_gd_handler()
  
  -- Register commands
  vim.api.nvim_create_user_command("YuhoReferences", function()
    M.show_incoming_references()
  end, {
    desc = "Show statutes that reference current statute",
  })
  
  vim.api.nvim_create_user_command("YuhoOutgoing", function()
    M.show_outgoing_references()
  end, {
    desc = "Show references from current statute",
  })
end

return M
