"""
Yuho Lexer - Tokenization for Yuho source files
"""

from typing import List, Dict, Any
from lark import Lark, Token, Tree
import os

class YuhoLexer:
    """Tokenizer for Yuho language using Lark parser"""

    def __init__(self):
        # Load grammar from file
        grammar_path = os.path.join(os.path.dirname(__file__), 'grammar.lark')
        with open(grammar_path, 'r') as f:
            grammar = f.read()

        self.parser = Lark(grammar, parser='lalr', start='program')

    def tokenize(self, text: str) -> List[Token]:
        """
        Tokenize Yuho source code

        Args:
            text: Yuho source code string

        Returns:
            List of tokens
        """
        try:
            tree = self.parser.parse(text)
            return self._extract_tokens(tree)
        except Exception as e:
            raise SyntaxError(f"Tokenization failed: {str(e)}")

    def _extract_tokens(self, tree: Tree) -> List[Token]:
        """Extract tokens from parse tree"""
        tokens = []
        for child in tree.iter_subtrees():
            if isinstance(child, Token):
                tokens.append(child)
        return tokens

    def parse(self, text: str) -> Tree:
        """
        Parse Yuho source code into AST

        Args:
            text: Yuho source code string

        Returns:
            Parse tree
        """
        try:
            return self.parser.parse(text)
        except Exception as e:
            raise SyntaxError(f"Parsing failed: {str(e)}")