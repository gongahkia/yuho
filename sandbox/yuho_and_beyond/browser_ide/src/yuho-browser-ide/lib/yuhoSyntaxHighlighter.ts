import { StreamLanguage } from "@codemirror/language"

const yuhoLanguage = StreamLanguage.define({

  name: "yuho",

  startState: () => ({ bracketDepth: 0 }),

  token(stream, state) {

    if (stream.match(/\/\//) || stream.match(/\/\*/)) {
      stream.skipToEnd()
      return "comment"
    }

    if (stream.match(/[{([]]/)) {
      state.bracketDepth = (state.bracketDepth + 1) % 5
      return `bracket bracket-${state.bracketDepth}`
    }
    if (stream.match(/[})\]]]/)) {
      const depth = state.bracketDepth
      state.bracketDepth = (state.bracketDepth - 1 + 5) % 5
      return `bracket bracket-${depth}`
    }

    if (stream.match(/\b(TRUE|FALSE|match|case|consequence|pass|struct|fn|day|month|year)\b/)) {
      return "keyword"
    }

    if (stream.match(/\b(int|float|percent|money|date|duration|bool|string)\b/)) {
      return "type"
    }

    if (stream.match(/"[^"]*"/)) {
      return "string"
    }

    if (stream.match(/\$?\d+(\.\d*)?%?/) || stream.match(/\d{2}-\d{2}-\d{4}/) || stream.match(/\d+(day|month|year)/)) {
      return "number"
    }

    if (stream.match(/[:=+\-*/><!&|]+/) || stream.match(/[,;.]/)) {
      return "operator"
    }

    if (stream.match(/[a-zA-Z_][a-zA-Z_0-9]*/)) {
      return "variable"
    }

    stream.next()
    return null
  },
})

export { yuhoLanguage }