"use client"

import React, { useState } from "react"
import dynamic from "next/dynamic"
import { EditorView } from "@codemirror/view"
import { customSyntaxHighlighter, customHighlightStyle } from "../lib/customSyntaxHighlighter"

const CodeMirror = dynamic(() => import("@uiw/react-codemirror"), { ssr: false })

export default function CustomIDE() {
  const [code, setCode] = useState("")

  const onChange = React.useCallback((value: string) => {
    setCode(value)
  }, [])

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Custom Language IDE</h1>
      <CodeMirror
        value={code}
        height="400px"
        extensions={[EditorView.lineWrapping, customSyntaxHighlighter, customHighlightStyle]}
        onChange={onChange}
      />
    </div>
  )
}