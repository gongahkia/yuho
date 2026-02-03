-- lua/yuho/legal_terms.lua
-- Dictionary of common legal terms for completion suggestions

local M = {}

-- Common legal terms organized by category
M.terms = {
  -- Mental states (mens rea)
  mens_rea = {
    { word = "intentionally", info = "Acting with purpose or design" },
    { word = "knowingly", info = "Aware of the nature of conduct or circumstances" },
    { word = "recklessly", info = "Conscious disregard of substantial risk" },
    { word = "negligently", info = "Should have been aware of substantial risk" },
    { word = "wilfully", info = "Deliberate and voluntary action" },
    { word = "maliciously", info = "With ill will or spite" },
    { word = "fraudulently", info = "With intent to deceive" },
    { word = "dishonestly", info = "With intent to cause wrongful gain/loss" },
    { word = "voluntarily", info = "By exercise of free will" },
    { word = "corruptly", info = "With wrongful intent for benefit" },
  },
  
  -- Actions (actus reus)
  actus_reus = {
    { word = "causes", info = "Produces a result" },
    { word = "commits", info = "Performs an act" },
    { word = "attempts", info = "Tries but fails to complete" },
    { word = "conspires", info = "Agrees with others to commit" },
    { word = "abets", info = "Encourages or assists" },
    { word = "aids", info = "Helps in commission" },
    { word = "omits", info = "Fails to act when duty exists" },
    { word = "possesses", info = "Has control or custody of" },
    { word = "transfers", info = "Conveys from one to another" },
    { word = "obtains", info = "Gets or acquires" },
    { word = "receives", info = "Takes into possession" },
    { word = "conceals", info = "Hides from discovery" },
    { word = "destroys", info = "Renders useless or nonexistent" },
    { word = "falsifies", info = "Makes false or inaccurate" },
    { word = "forges", info = "Creates false document/instrument" },
    { word = "utters", info = "Passes or presents as genuine" },
    { word = "induces", info = "Persuades or influences" },
    { word = "deceives", info = "Causes false belief" },
    { word = "coerces", info = "Compels by force or threat" },
    { word = "intimidates", info = "Frightens into compliance" },
  },
  
  -- Subjects and objects
  subjects = {
    { word = "person", info = "Human being" },
    { word = "public_servant", info = "Government official or employee" },
    { word = "corporation", info = "Legal entity" },
    { word = "minor", info = "Person under age of majority" },
    { word = "accused", info = "Person charged with offense" },
    { word = "victim", info = "Person harmed by offense" },
    { word = "accomplice", info = "Partner in crime" },
    { word = "principal", info = "Main offender" },
    { word = "abettor", info = "One who encourages offense" },
    { word = "agent", info = "One who acts for another" },
  },
  
  -- Property terms
  property = {
    { word = "property", info = "Anything of value capable of ownership" },
    { word = "movable_property", info = "Property that can be moved" },
    { word = "immovable_property", info = "Land and things attached" },
    { word = "valuable_security", info = "Document creating/transferring rights" },
    { word = "document", info = "Written or electronic record" },
    { word = "instrument", info = "Formal legal document" },
    { word = "currency", info = "Money in circulation" },
    { word = "proceeds", info = "Gains from transaction" },
  },
  
  -- Circumstances
  circumstances = {
    { word = "public_place", info = "Area accessible to public" },
    { word = "private_place", info = "Non-public area" },
    { word = "dwelling", info = "Place of residence" },
    { word = "night_time", info = "Between sunset and sunrise" },
    { word = "in_custody", info = "Under lawful detention" },
    { word = "armed", info = "Carrying weapon" },
    { word = "disguised", info = "Concealing identity" },
    { word = "in_concert", info = "Acting together with others" },
  },
  
  -- Defenses
  defenses = {
    { word = "consent", info = "Victim agreed to conduct" },
    { word = "self_defense", info = "Protection from harm" },
    { word = "duress", info = "Compelled by threats" },
    { word = "necessity", info = "No reasonable alternative" },
    { word = "insanity", info = "Mental disorder negating culpability" },
    { word = "intoxication", info = "Impaired by substances" },
    { word = "mistake_of_fact", info = "Reasonable factual error" },
    { word = "entrapment", info = "Induced by law enforcement" },
    { word = "alibi", info = "Elsewhere when offense occurred" },
    { word = "provocation", info = "Victim's conduct caused reaction" },
  },
  
  -- Penalty terms
  penalties = {
    { word = "imprisonment", info = "Incarceration in prison" },
    { word = "fine", info = "Monetary penalty" },
    { word = "caning", info = "Corporal punishment" },
    { word = "death", info = "Capital punishment" },
    { word = "probation", info = "Supervised release" },
    { word = "community_service", info = "Unpaid work for community" },
    { word = "restitution", info = "Compensation to victim" },
    { word = "forfeiture", info = "Loss of property to state" },
    { word = "disqualification", info = "Loss of rights/privileges" },
  },
  
  -- Procedural terms
  procedural = {
    { word = "cognizable", info = "Arrestable without warrant" },
    { word = "non_cognizable", info = "Requires warrant for arrest" },
    { word = "bailable", info = "Entitled to bail as right" },
    { word = "non_bailable", info = "Bail at court's discretion" },
    { word = "compoundable", info = "Can be settled by parties" },
    { word = "non_compoundable", info = "Cannot be privately settled" },
    { word = "triable", info = "Jurisdictionally appropriate" },
  },
}

--- Get all terms as flat list
--- @return table[]
function M.get_all_terms()
  local all = {}
  for category, terms in pairs(M.terms) do
    for _, term in ipairs(terms) do
      table.insert(all, {
        word = term.word,
        info = term.info,
        category = category,
      })
    end
  end
  return all
end

--- Get terms by category
--- @param category string
--- @return table[]
function M.get_terms_by_category(category)
  return M.terms[category] or {}
end

--- Search terms by prefix
--- @param prefix string
--- @return table[]
function M.search_terms(prefix)
  local results = {}
  local pattern = "^" .. vim.pesc(prefix:lower())
  
  for _, term in ipairs(M.get_all_terms()) do
    if term.word:lower():match(pattern) then
      table.insert(results, term)
    end
  end
  
  return results
end

return M
