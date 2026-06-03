{-# LANGUAGE OverloadedStrings #-}

module Euclid.Render.HTML
    ( renderInteractiveHtml
    ) where

import Data.Text (Text)
import qualified Data.Text as T
import Euclid.Render.Layout

renderInteractiveHtml :: Layout -> Text
renderInteractiveHtml layout = T.unlines
    [ "<!DOCTYPE html>"
    , "<html><head><meta charset=\"utf-8\">"
    , "<title>Euclid Timeline</title>"
    , "<style>"
    , "body { margin: 0; background: #1a1a2e; color: #eee; font-family: monospace; }"
    , ".controls { padding: 12px; background: #16213e; display: flex; gap: 12px; align-items: center; }"
    , ".controls input { width: 300px; }"
    , ".controls label { font-size: 13px; }"
    , ".controls button { background: #0f3460; color: #eee; border: none; padding: 6px 12px; cursor: pointer; border-radius: 4px; }"
    , ".controls button:hover { background: #533483; }"
    , "svg { display: block; }"
    , ".timeline-line { stroke: #e94560; stroke-width: 2; opacity: 0.4; }"
    , ".entity-rect { stroke: #e94560; stroke-width: 1; rx: 4; cursor: pointer; opacity: 0.85; }"
    , ".entity-rect:hover { opacity: 1; fill: #533483; }"
    , ".entity-label { fill: #eee; font-size: 11px; pointer-events: none; }"
    , ".timeline-label { fill: #e94560; font-size: 13px; }"
    , ".rel-line { stroke: #533483; stroke-width: 1; stroke-dasharray: 4,4; opacity: 0.6; }"
    , ".rel-line.contradiction { stroke: #dc2626; stroke-width: 2.75; stroke-dasharray: none; opacity: 0.9; }"
    , ".rel-label { fill: #533483; font-size: 10px; }"
    , ".rel-label.contradiction { fill: #dc2626; font-weight: 700; }"
    , ".axis-label { fill: #666; font-size: 10px; }"
    , ".scrub-line { stroke: #e94560; stroke-width: 1; stroke-dasharray: 2,2; }"
    , ".tooltip { position: absolute; background: #16213e; border: 1px solid #e94560; padding: 8px; font-size: 12px; pointer-events: none; display: none; border-radius: 4px; z-index: 10; }"
    , ".hidden { display: none; }"
    , "</style>"
    , "</head><body>"
    , "<div class=\"controls\">"
    , "  <label>Scrub: <input type=\"range\" id=\"scrubber\" min=\"" <> showT (layoutMinTime layout) <> "\" max=\"" <> showT (layoutMaxTime layout) <> "\" value=\"" <> showT (layoutMinTime layout) <> "\"></label>"
    , "  <span id=\"scrub-value\"></span>"
    , "  <button id=\"play-btn\">Play</button>"
    , "  <label>Search: <input type=\"text\" id=\"search\" placeholder=\"filter entities...\"></label>"
    , "</div>"
    , "<div id=\"tooltip\" class=\"tooltip\"></div>"
    , "<svg id=\"timeline\" width=\"1600\" height=\"" <> showT svgHeight <> "\"></svg>"
    , "<script>"
    , "const data = " <> layoutToJson layout <> ";"
    , interactiveScript
    , "</script>"
    , "</body></html>"
    ]
  where
    svgHeight = max 400 (100 + length (layoutTimelines layout) * 54 + 50)

showT :: Show a => a -> Text
showT = T.pack . show

layoutToJson :: Layout -> Text
layoutToJson layout = T.concat
    [ "{\"timelines\":["
    , T.intercalate "," (map timelineJson (layoutTimelines layout))
    , "],\"entities\":["
    , T.intercalate "," (map entityJson (layoutEntities layout))
    , "],\"relationships\":["
    , T.intercalate "," (map relJson (layoutRelationships layout))
    , "],\"minTime\":" <> showT (layoutMinTime layout)
    , ",\"maxTime\":" <> showT (layoutMaxTime layout)
    , "}"
    ]

timelineJson :: LayoutTimeline -> Text
timelineJson tl = T.concat
    [ "{\"name\":\"" <> esc (layoutTimelineName tl) <> "\""
    , ",\"lane\":" <> showT (layoutTimelineLane tl)
    , ",\"start\":" <> showT (layoutTimelineStart tl)
    , ",\"end\":" <> showT (layoutTimelineEnd tl)
    , "}"
    ]

entityJson :: LayoutEntity -> Text
entityJson e = T.concat
    [ "{\"name\":\"" <> esc (layoutEntityName e) <> "\""
    , ",\"type\":\"" <> esc (layoutEntityType e) <> "\""
    , ",\"narrative\":" <> maybe "null" (\n -> "\"" <> esc n <> "\"") (layoutEntityNarrative e)
    , ",\"timeline\":\"" <> esc (layoutEntityTimeline e) <> "\""
    , ",\"lane\":" <> showT (layoutEntityLane e)
    , ",\"start\":" <> showT (layoutEntityStart e)
    , ",\"end\":" <> showT (layoutEntityEnd e)
    , "}"
    ]

relJson :: LayoutRelationship -> Text
relJson r = T.concat
    [ "{\"source\":\"" <> esc (layoutRelSource r) <> "\""
    , ",\"target\":\"" <> esc (layoutRelTarget r) <> "\""
    , ",\"label\":" <> maybe "null" (\l -> "\"" <> esc l <> "\"") (layoutRelLabel r)
    , "}"
    ]

esc :: Text -> Text
esc = T.concatMap (\c -> case c of {'"' -> "\\\""; '\\' -> "\\\\"; '\n' -> "\\n"; _ -> T.singleton c})

interactiveScript :: Text
interactiveScript = T.unlines
    [ "const svg = document.getElementById('timeline');"
    , "const tooltip = document.getElementById('tooltip');"
    , "const scrubber = document.getElementById('scrubber');"
    , "const scrubValue = document.getElementById('scrub-value');"
    , "const searchBox = document.getElementById('search');"
    , "const playBtn = document.getElementById('play-btn');"
    , "const W = 1600, oX = 80, oY = 80, lH = 54, dW = W - 120;"
    , "const mn = data.minTime, mx = Math.max(data.maxTime, mn + 1);"
    , "const narrativePalette = ['#2563eb','#059669','#d97706','#7c3aed','#db2777','#0891b2'];"
    , "function sx(t) { return oX + (t - mn) / (mx - mn) * dW; }"
    , "function ly(lane) { return oY + lane * lH; }"
    , "function hashText(s) { let h = 5381; for (const ch of s) h = ((h * 33) + ch.codePointAt(0)) >>> 0; return h; }"
    , "function entityColor(narrative) { return narrative ? narrativePalette[hashText(narrative) % narrativePalette.length] : '#0f3460'; }"
    , "let scrubTime = mn, playing = false, playInterval = null;"
    , "function render() {"
    , "  const search = searchBox.value.toLowerCase();"
    , "  svg.innerHTML = '';"
    , "  // axis ticks"
    , "  const ticks = 10; for (let i = 0; i <= ticks; i++) {"
    , "    const t = mn + (mx - mn) * i / ticks;"
    , "    const x = sx(t);"
    , "    svg.innerHTML += `<text x=\"${x}\" y=\"${oY - 10}\" class=\"axis-label\" text-anchor=\"middle\">${Math.round(t)}</text>`;"
    , "  }"
    , "  // scrub line"
    , "  const scrubX = sx(scrubTime);"
    , "  svg.innerHTML += `<line x1=\"${scrubX}\" y1=\"${oY - 20}\" x2=\"${scrubX}\" y2=\"${oY + data.timelines.length * lH}\" class=\"scrub-line\"/>`;"
    , "  // timelines"
    , "  data.timelines.forEach(tl => {"
    , "    const y = ly(tl.lane);"
    , "    svg.innerHTML += `<line x1=\"${sx(tl.start)}\" y1=\"${y}\" x2=\"${sx(tl.end)}\" y2=\"${y}\" class=\"timeline-line\"/>`;"
    , "    svg.innerHTML += `<text x=\"10\" y=\"${y + 4}\" class=\"timeline-label\">${tl.name}</text>`;"
    , "  });"
    , "  // entities"
    , "  data.entities.forEach(e => {"
    , "    const visible = e.start <= scrubTime && e.end >= scrubTime;"
    , "    const matchesSearch = !search || e.name.toLowerCase().includes(search) || e.type.toLowerCase().includes(search);"
    , "    if (!matchesSearch) return;"
    , "    const y = ly(e.lane) - 14; const x = sx(e.start); const w = Math.max(14, sx(e.end) - x);"
    , "    const opacity = visible ? 0.9 : 0.2;"
    , "    svg.innerHTML += `<rect x=\"${x}\" y=\"${y}\" width=\"${w}\" height=\"24\" class=\"entity-rect\" fill=\"${entityColor(e.narrative)}\" opacity=\"${opacity}\" data-name=\"${e.name}\" data-type=\"${e.type}\" data-narrative=\"${e.narrative || ''}\"/>`;"
    , "    svg.innerHTML += `<text x=\"${x + 4}\" y=\"${y + 16}\" class=\"entity-label\" opacity=\"${opacity}\">${e.name}</text>`;"
    , "  });"
    , "  // relationships"
    , "  data.relationships.forEach(r => {"
    , "    const se = data.entities.find(e => e.name === r.source);"
    , "    const te = data.entities.find(e => e.name === r.target);"
    , "    if (!se || !te) return;"
    , "    const x1 = (sx(se.start) + sx(se.end)) / 2, y1 = ly(se.lane) - 2;"
    , "    const x2 = (sx(te.start) + sx(te.end)) / 2, y2 = ly(te.lane) - 2;"
    , "    const contradiction = r.label === 'contradicts';"
    , "    const relClass = contradiction ? 'rel-line contradiction' : 'rel-line';"
    , "    const relLabelClass = contradiction ? 'rel-label contradiction' : 'rel-label';"
    , "    const collapsed = Math.abs(x1 - x2) < 1 && Math.abs(y1 - y2) < 1;"
    , "    if (collapsed && contradiction) svg.innerHTML += `<path d=\"M ${x1} ${y1} C ${x1} ${y1 - 42} ${x1 + 72} ${y1 - 42} ${x1 + 72} ${y1}\" fill=\"none\" class=\"${relClass}\"/>`;"
    , "    else svg.innerHTML += `<line x1=\"${x1}\" y1=\"${y1}\" x2=\"${x2}\" y2=\"${y2}\" class=\"${relClass}\"/>`;"
    , "    // arrowhead"
    , "    const angle = Math.atan2(y2-y1, x2-x1); const aL = 8;"
    , "    svg.innerHTML += `<polygon points=\"${x2},${y2} ${x2-aL*Math.cos(angle-0.3)},${y2-aL*Math.sin(angle-0.3)} ${x2-aL*Math.cos(angle+0.3)},${y2-aL*Math.sin(angle+0.3)}\" fill=\"${contradiction ? '#dc2626' : '#533483'}\" opacity=\"${contradiction ? 0.9 : 0.6}\"/>`;"
    , "    if (r.label) svg.innerHTML += `<text x=\"${(x1+x2)/2}\" y=\"${(y1+y2)/2-4}\" class=\"${relLabelClass}\">${r.label}</text>`;"
    , "  });"
    , "  // tooltip listeners"
    , "  svg.querySelectorAll('.entity-rect').forEach(el => {"
    , "    el.addEventListener('mouseover', ev => {"
    , "      tooltip.style.display = 'block'; tooltip.style.left = (ev.pageX + 10) + 'px'; tooltip.style.top = (ev.pageY + 10) + 'px';"
    , "      tooltip.innerHTML = `<b>${el.dataset.name}</b><br>type: ${el.dataset.type}`;"
    , "    });"
    , "    el.addEventListener('mouseout', () => { tooltip.style.display = 'none'; });"
    , "  });"
    , "}"
    , "scrubber.addEventListener('input', () => { scrubTime = +scrubber.value; scrubValue.textContent = scrubTime; render(); });"
    , "searchBox.addEventListener('input', render);"
    , "playBtn.addEventListener('click', () => {"
    , "  playing = !playing; playBtn.textContent = playing ? 'Pause' : 'Play';"
    , "  if (playing) { playInterval = setInterval(() => { scrubTime = Math.min(+scrubber.max, scrubTime + Math.ceil((mx-mn)/200)); scrubber.value = scrubTime; scrubValue.textContent = scrubTime; render(); if (scrubTime >= +scrubber.max) { playing = false; playBtn.textContent = 'Play'; clearInterval(playInterval); } }, 50); }"
    , "  else clearInterval(playInterval);"
    , "});"
    , "render();"
    ]
