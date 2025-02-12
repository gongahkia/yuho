"use client"

import React, { useState } from "react"
import CodeMirror from "@uiw/react-codemirror"
import { yuhoLanguage } from "../lib/yuhoSyntaxHighlighter"

const bracketColors = [
  "#e6194B", 
  "#3cb44b",
  "#ffe119", 
  "#4363d8",
  "#f58231", 
]

const customStyles = `
  .cm-bracket-0 { color: ${bracketColors[0]} !important; }
  .cm-bracket-1 { color: ${bracketColors[1]} !important; }
  .cm-bracket-2 { color: ${bracketColors[2]} !important; }
  .cm-bracket-3 { color: ${bracketColors[3]} !important; }
  .cm-bracket-4 { color: ${bracketColors[4]} !important; }
`

export default function YuhoIDE() {
  const [code, setCode] = useState("")

  const onChange = React.useCallback((value: string) => {
    setCode(value)
  }, [])

  return (
    <div className="container mx-auto p-4">
      <style>{customStyles}</style>
      <h1 className="text-2xl font-bold mb-4">Yuho Language IDE</h1>
      <CodeMirror value={code} height="400px" extensions={[yuhoLanguage]} onChange={onChange} />
    </div>
  )
}