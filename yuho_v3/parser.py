"""
Yuho Parser - Converts tokens to Abstract Syntax Tree
"""

from typing import List, Optional, Dict, Any
from lark import Transformer, Tree, Token
from .ast_nodes import *
from .lexer import YuhoLexer

class YuhoTransformer(Transformer):
    """Transforms Lark parse tree into Yuho AST"""

    def program(self, children):
        """Transform program node"""
        return Program(statements=children)

    def import_statement(self, children):
        """Transform import statement: referencing StructName from module"""
        return ImportStatement(
            struct_name=str(children[0]),
            module_name=str(children[1])
        )

    def declaration(self, children):
        """Transform variable declaration"""
        if len(children) == 3:  # type name value
            return Declaration(
                type_node=children[0],
                name=str(children[1]),
                value=children[2]
            )
        else:  # type name (no value)
            return Declaration(
                type_node=children[0],
                name=str(children[1])
            )

    def assignment(self, children):
        """Transform assignment statement"""
        return Assignment(
            name=str(children[0]),
            value=children[1]
        )

    def type(self, children):
        """Transform type annotation"""
        type_str = str(children[0])
        if type_str in [t.value for t in YuhoType]:
            return TypeNode(YuhoType(type_str))
        else:
            return TypeNode(type_str)  # Custom type

    def qualified_identifier(self, children):
        """Transform qualified identifier like module.StructName"""
        return QualifiedIdentifier(parts=[str(child) for child in children])

    def expression(self, children):
        """Transform expression"""
        return children[0]

    def logical_expression(self, children):
        """Transform logical expression"""
        if len(children) == 1:
            return children[0]

        # Build left-associative tree for multiple operators
        result = children[0]
        for i in range(1, len(children), 2):
            operator = Operator(str(children[i]))
            right = children[i + 1]
            result = BinaryOperation(left=result, operator=operator, right=right)
        return result

    def relational_expression(self, children):
        """Transform relational expression"""
        if len(children) == 1:
            return children[0]

        result = children[0]
        for i in range(1, len(children), 2):
            operator = Operator(str(children[i]))
            right = children[i + 1]
            result = BinaryOperation(left=result, operator=operator, right=right)
        return result

    def additive_expression(self, children):
        """Transform additive expression"""
        if len(children) == 1:
            return children[0]

        result = children[0]
        for i in range(1, len(children), 2):
            operator = Operator(str(children[i]))
            right = children[i + 1]
            result = BinaryOperation(left=result, operator=operator, right=right)
        return result

    def multiplicative_expression(self, children):
        """Transform multiplicative expression"""
        if len(children) == 1:
            return children[0]

        result = children[0]
        for i in range(1, len(children), 2):
            operator = Operator(str(children[i]))
            right = children[i + 1]
            result = BinaryOperation(left=result, operator=operator, right=right)
        return result

    def primary_expression(self, children):
        """Transform primary expression"""
        return children[0]

    def literal(self, children):
        """Transform literal value"""
        token = children[0]
        if isinstance(token, Token):
            token_type = token.type
            value = token.value

            if token_type == "STRING":
                return Literal(value=value.strip('"'), literal_type=YuhoType.STRING)
            elif token_type == "INTEGER":
                return Literal(value=int(value), literal_type=YuhoType.INT)
            elif token_type == "FLOAT":
                return Literal(value=float(value), literal_type=YuhoType.FLOAT)
            elif token_type == "PERCENTAGE":
                return Literal(value=int(value[:-1]), literal_type=YuhoType.PERCENT)
            elif token_type == "MONEY":
                return Literal(value=float(value[1:]), literal_type=YuhoType.MONEY)
            elif token_type == "DATE":
                return Literal(value=value, literal_type=YuhoType.DATE)
            elif token_type == "DURATION":
                return Literal(value=value, literal_type=YuhoType.DURATION)
            elif token_type == "TRUE":
                return Literal(value=True, literal_type=YuhoType.BOOL)
            elif token_type == "FALSE":
                return Literal(value=False, literal_type=YuhoType.BOOL)

        return Literal(value=str(token), literal_type=YuhoType.STRING)

    def struct_definition(self, children):
        """Transform struct definition"""
        name = str(children[0])
        members = children[1:]
        return StructDefinition(name=name, members=members)

    def struct_member(self, children):
        """Transform struct member"""
        return StructMember(
            type_node=children[0],
            name=str(children[1])
        )

    def match_case(self, children):
        """Transform match-case statement"""
        if children[0] and not isinstance(children[0], CaseClause):
            # Match with expression
            expression = children[0]
            cases = children[1:]
        else:
            # Bare match
            expression = None
            cases = children

        return MatchCase(expression=expression, cases=cases)

    def case_clause(self, children):
        """Transform case clause"""
        if len(children) == 2:
            # case condition := consequence expression
            return CaseClause(condition=children[0], consequence=children[1])
        else:
            # case _ := consequence pass
            return CaseClause(condition=None, consequence=children[0])

    def pass_statement(self, children):
        """Transform pass statement"""
        return PassStatement()

    def function_definition(self, children):
        """Transform function definition"""
        name = str(children[0])
        parameters = children[1] if children[1] else []
        return_type = children[2]
        body = children[3:]
        return FunctionDefinition(
            name=name,
            parameters=parameters,
            return_type=return_type,
            body=body
        )

    def parameter(self, children):
        """Transform function parameter"""
        return Parameter(
            type_node=children[0],
            name=str(children[1])
        )

    def function_call(self, children):
        """Transform function call"""
        name = str(children[0])
        arguments = children[1] if len(children) > 1 else []
        return FunctionCall(name=name, arguments=arguments)

    # Token transformations
    def IDENTIFIER(self, token):
        return Identifier(name=str(token))

    def logical_operator(self, children):
        return children[0]

    def relational_operator(self, children):
        return children[0]

    def additive_operator(self, children):
        return children[0]

    def multiplicative_operator(self, children):
        return children[0]

class YuhoParser:
    """Main parser class for Yuho language"""

    def __init__(self):
        self.lexer = YuhoLexer()
        self.transformer = YuhoTransformer()

    def parse(self, text: str) -> Program:
        """
        Parse Yuho source code into AST

        Args:
            text: Yuho source code string

        Returns:
            Program AST node
        """
        try:
            # Parse with Lark
            parse_tree = self.lexer.parse(text)

            # Transform to Yuho AST
            ast = self.transformer.transform(parse_tree)

            return ast
        except Exception as e:
            raise SyntaxError(f"Parse error: {str(e)}")

    def parse_file(self, filepath: str) -> Program:
        """
        Parse a Yuho source file

        Args:
            filepath: Path to .yh file

        Returns:
            Program AST node
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        return self.parse(content)