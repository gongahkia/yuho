import { LanguageSupport, LRLanguage } from "@codemirror/language"
import { styleTags, tags as t } from "@lezer/highlight"

const customLanguage = LRLanguage.define({
  parser: {
    parse: (input: string) => {
      return {
      }
    },
  },
  languageData: {
    commentTokens: { line: "//" },
  },
})

export const customSyntaxHighlighter = new LanguageSupport(customLanguage, [
  customLanguage.data.of({
    tokenTypes: {
      keyword: t.keyword,
      string: t.string,
      number: t.number,
      comment: t.comment,
    },
  }),
])

export const customHighlightStyle = styleTags({
  Keyword: t.keyword,
  String: t.string,
  Number: t.number,
  Comment: t.comment,
})