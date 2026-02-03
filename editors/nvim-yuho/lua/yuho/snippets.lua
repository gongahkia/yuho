-- lua/yuho/snippets.lua
-- Snippet Expansion module for Yuho
-- Provides LuaSnip snippet definitions

local M = {}

--- Check if LuaSnip is available
--- @return boolean
local function has_luasnip()
  return pcall(require, "luasnip")
end

--- Setup LuaSnip snippets for Yuho
function M.setup()
  if not has_luasnip() then
    vim.notify("LuaSnip not found, Yuho snippets disabled", vim.log.levels.WARN)
    return
  end
  
  local ls = require("luasnip")
  local s = ls.snippet
  local t = ls.text_node
  local i = ls.insert_node
  local c = ls.choice_node
  local f = ls.function_node
  local d = ls.dynamic_node
  local sn = ls.snippet_node
  local fmt = require("luasnip.extras.fmt").fmt
  local rep = require("luasnip.extras").rep
  
  -- Helper: generate current date
  local function date()
    return os.date("%Y-%m-%d")
  end
  
  -- Statute scaffold snippet (stat)
  local statute_snippet = s("stat", fmt([[
// Section {} - {}
// Singapore Penal Code
// Created: {}

statute S{} {{
    section: "{}"
    title: "{}"
    
    definitions {{
        {}: "{}"
    }}
    
    elements {{
        actus_reus: "{}"
        mens_rea: "{}"
        circumstance: "{}"
    }}
    
    penalty {{
        imprisonment(Y: {}, {})
        fine(SGD: {})
    }}
    
    illustrations {{
        (a) {} => {}
    }}
    
    // Legal test function
    fn is_{}(case: Case) -> bool {{
        {}
    }}
}}
]], {
    i(1, "000"),              -- section number in comment
    i(2, "Offense Name"),     -- offense name in comment
    f(date, {}),              -- date
    rep(1),                   -- section in statute name
    rep(1),                   -- section property
    rep(2),                   -- title property
    i(3, "term"),             -- definition term
    i(4, "explanation"),      -- definition value
    i(5, "describes the prohibited conduct"),
    i(6, "describes the mental state required"),
    i(7, "describes surrounding conditions"),
    i(8, "1"),                -- min imprisonment
    i(9, "10"),               -- max imprisonment
    i(10, "10000"),           -- fine amount
    i(11, "Example scenario"),
    i(12, "guilty of offense"),
    f(function(args) return args[1][1]:lower():gsub(" ", "_") end, {2}), -- function name from title
    i(13, "return true"),
  }))
  
  -- Definition block snippet (def)
  local definition_snippet = s("def", fmt([[
definitions {{
    {}: "{}"
    {}: "{}"
    {}
}}
]], {
    i(1, "term1"),
    i(2, "definition of term1"),
    i(3, "term2"),
    i(4, "definition of term2"),
    i(0),
  }))
  
  -- Elements block snippet (elem)
  local elements_snippet = s("elem", fmt([[
elements {{
    actus_reus: "{}"
    mens_rea: "{}"
    circumstance: "{}"
    result: "{}"
    {}
}}
]], {
    i(1, "the prohibited act or conduct"),
    i(2, "the mental state or intention required"),
    i(3, "surrounding circumstances that must exist"),
    i(4, "the consequence or outcome"),
    i(0),
  }))
  
  -- Illustration entry snippet (ill)
  local illustration_snippet = s("ill", fmt([[
({}) {} => {}
]], {
    i(1, "a"),
    i(2, "A person does X in circumstance Y"),
    i(3, "guilty of offense under this section"),
  }))
  
  -- Illustrations block snippet (ills)
  local illustrations_block_snippet = s("ills", fmt([[
illustrations {{
    (a) {} => {}
    (b) {} => {}
    {}
}}
]], {
    i(1, "First scenario"),
    i(2, "outcome for first scenario"),
    i(3, "Second scenario"),
    i(4, "outcome for second scenario"),
    i(0),
  }))
  
  -- Penalty block snippet (pen)
  local penalty_snippet = s("pen", fmt([[
penalty {{
    imprisonment(Y: {}, {})
    fine(SGD: {})
    {}
}}
]], {
    i(1, "1"),
    i(2, "10"),
    i(3, "10000"),
    i(0),
  }))
  
  -- Penalty with caning snippet (penc)
  local penalty_caning_snippet = s("penc", fmt([[
penalty {{
    imprisonment(Y: {}, {})
    fine(SGD: {})
    caning(strokes: {}, {})
}}
]], {
    i(1, "2"),
    i(2, "14"),
    i(3, "50000"),
    i(4, "3"),
    i(5, "12"),
  }))
  
  -- Death penalty snippet (pend)
  local penalty_death_snippet = s("pend", fmt([[
penalty {{
    death()
    // OR
    imprisonment_life(Y: {})
}}
]], {
    i(1, "20"),
  }))
  
  -- Function snippet (fn)
  local function_snippet = s("fn", fmt([[
fn {}({}: {}) -> {} {{
    {}
}}
]], {
    i(1, "function_name"),
    i(2, "param"),
    i(3, "Type"),
    i(4, "bool"),
    i(0, "return true"),
  }))
  
  -- Match expression snippet (match)
  local match_snippet = s("match", fmt([[
match {} {{
    case {} => {{
        {}
    }}
    case {} => {{
        {}
    }}
}}
]], {
    i(1, "expr"),
    i(2, "true"),
    i(3, "// handle true case"),
    i(4, "false"),
    i(5, "// handle false case"),
  }))
  
  -- Struct snippet (struct)
  local struct_snippet = s("struct", fmt([[
struct {} {{
    {} {},
    {} {},
    {}
}}
]], {
    i(1, "StructName"),
    i(2, "string"),
    i(3, "field1"),
    i(4, "bool"),
    i(5, "field2"),
    i(0),
  }))
  
  -- Enum snippet (enum)
  local enum_snippet = s("enum", fmt([[
enum {} {{
    {},
    {},
    {},
}}
]], {
    i(1, "EnumName"),
    i(2, "Variant1"),
    i(3, "Variant2"),
    i(4, "Variant3"),
  }))
  
  -- Exceptions block snippet (exc)
  local exceptions_snippet = s("exc", fmt([[
exceptions {{
    {}: "{}"
    {}: "{}"
    {}
}}
]], {
    i(1, "exception1"),
    i(2, "description of when offense does not apply"),
    i(3, "exception2"),
    i(4, "another exception condition"),
    i(0),
  }))
  
  -- Let binding snippet (let)
  local let_snippet = s("let", fmt([[
let {} := {}
]], {
    i(1, "variable"),
    i(2, "value"),
  }))
  
  -- Comment header snippet (hdr)
  local header_snippet = s("hdr", fmt([[
// ============================================================================
// {}
// ============================================================================
]], {
    i(1, "SECTION HEADER"),
  }))
  
  -- Add all snippets for yuho filetype
  ls.add_snippets("yuho", {
    statute_snippet,
    definition_snippet,
    elements_snippet,
    illustration_snippet,
    illustrations_block_snippet,
    penalty_snippet,
    penalty_caning_snippet,
    penalty_death_snippet,
    function_snippet,
    match_snippet,
    struct_snippet,
    enum_snippet,
    exceptions_snippet,
    let_snippet,
    header_snippet,
  })
  
  -- Also add for yh extension (in case filetype isn't set)
  ls.filetype_extend("yh", { "yuho" })
end

--- Get snippet list for documentation
--- @return table[]
function M.get_snippet_list()
  return {
    { trigger = "stat", description = "Full statute scaffold template" },
    { trigger = "def", description = "Definitions block" },
    { trigger = "elem", description = "Elements block with actus_reus, mens_rea, etc." },
    { trigger = "ill", description = "Single illustration entry" },
    { trigger = "ills", description = "Illustrations block with multiple entries" },
    { trigger = "pen", description = "Penalty block with imprisonment and fine" },
    { trigger = "penc", description = "Penalty block with caning" },
    { trigger = "pend", description = "Death penalty block" },
    { trigger = "fn", description = "Function definition" },
    { trigger = "match", description = "Match expression" },
    { trigger = "struct", description = "Struct type definition" },
    { trigger = "enum", description = "Enum type definition" },
    { trigger = "exc", description = "Exceptions block" },
    { trigger = "let", description = "Let binding" },
    { trigger = "hdr", description = "Section header comment" },
  }
end

--- Show available snippets
function M.show_snippets()
  local snippets = M.get_snippet_list()
  local lines = { "Yuho Snippets:", "" }
  
  for _, snip in ipairs(snippets) do
    table.insert(lines, string.format("  %s - %s", snip.trigger, snip.description))
  end
  
  vim.notify(table.concat(lines, "\n"), vim.log.levels.INFO)
end

return M
