// Generated from Yuho.g4 by ANTLR 4.13.2
import org.antlr.v4.runtime.tree.ParseTreeListener;

/**
 * This interface defines a complete listener for a parse tree produced by
 * {@link YuhoParser}.
 */
public interface YuhoListener extends ParseTreeListener {
	/**
	 * Enter a parse tree produced by {@link YuhoParser#program}.
	 * @param ctx the parse tree
	 */
	void enterProgram(YuhoParser.ProgramContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#program}.
	 * @param ctx the parse tree
	 */
	void exitProgram(YuhoParser.ProgramContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#declaration}.
	 * @param ctx the parse tree
	 */
	void enterDeclaration(YuhoParser.DeclarationContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#declaration}.
	 * @param ctx the parse tree
	 */
	void exitDeclaration(YuhoParser.DeclarationContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#type}.
	 * @param ctx the parse tree
	 */
	void enterType(YuhoParser.TypeContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#type}.
	 * @param ctx the parse tree
	 */
	void exitType(YuhoParser.TypeContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#expression}.
	 * @param ctx the parse tree
	 */
	void enterExpression(YuhoParser.ExpressionContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#expression}.
	 * @param ctx the parse tree
	 */
	void exitExpression(YuhoParser.ExpressionContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#literal}.
	 * @param ctx the parse tree
	 */
	void enterLiteral(YuhoParser.LiteralContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#literal}.
	 * @param ctx the parse tree
	 */
	void exitLiteral(YuhoParser.LiteralContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#statement}.
	 * @param ctx the parse tree
	 */
	void enterStatement(YuhoParser.StatementContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#statement}.
	 * @param ctx the parse tree
	 */
	void exitStatement(YuhoParser.StatementContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#assignment}.
	 * @param ctx the parse tree
	 */
	void enterAssignment(YuhoParser.AssignmentContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#assignment}.
	 * @param ctx the parse tree
	 */
	void exitAssignment(YuhoParser.AssignmentContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#matchCase}.
	 * @param ctx the parse tree
	 */
	void enterMatchCase(YuhoParser.MatchCaseContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#matchCase}.
	 * @param ctx the parse tree
	 */
	void exitMatchCase(YuhoParser.MatchCaseContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#caseClause}.
	 * @param ctx the parse tree
	 */
	void enterCaseClause(YuhoParser.CaseClauseContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#caseClause}.
	 * @param ctx the parse tree
	 */
	void exitCaseClause(YuhoParser.CaseClauseContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#passStatement}.
	 * @param ctx the parse tree
	 */
	void enterPassStatement(YuhoParser.PassStatementContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#passStatement}.
	 * @param ctx the parse tree
	 */
	void exitPassStatement(YuhoParser.PassStatementContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#functionDefinition}.
	 * @param ctx the parse tree
	 */
	void enterFunctionDefinition(YuhoParser.FunctionDefinitionContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#functionDefinition}.
	 * @param ctx the parse tree
	 */
	void exitFunctionDefinition(YuhoParser.FunctionDefinitionContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#parameterList}.
	 * @param ctx the parse tree
	 */
	void enterParameterList(YuhoParser.ParameterListContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#parameterList}.
	 * @param ctx the parse tree
	 */
	void exitParameterList(YuhoParser.ParameterListContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#parameter}.
	 * @param ctx the parse tree
	 */
	void enterParameter(YuhoParser.ParameterContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#parameter}.
	 * @param ctx the parse tree
	 */
	void exitParameter(YuhoParser.ParameterContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#functionCall}.
	 * @param ctx the parse tree
	 */
	void enterFunctionCall(YuhoParser.FunctionCallContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#functionCall}.
	 * @param ctx the parse tree
	 */
	void exitFunctionCall(YuhoParser.FunctionCallContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#argumentList}.
	 * @param ctx the parse tree
	 */
	void enterArgumentList(YuhoParser.ArgumentListContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#argumentList}.
	 * @param ctx the parse tree
	 */
	void exitArgumentList(YuhoParser.ArgumentListContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#structDefinition}.
	 * @param ctx the parse tree
	 */
	void enterStructDefinition(YuhoParser.StructDefinitionContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#structDefinition}.
	 * @param ctx the parse tree
	 */
	void exitStructDefinition(YuhoParser.StructDefinitionContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#structMember}.
	 * @param ctx the parse tree
	 */
	void enterStructMember(YuhoParser.StructMemberContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#structMember}.
	 * @param ctx the parse tree
	 */
	void exitStructMember(YuhoParser.StructMemberContext ctx);
	/**
	 * Enter a parse tree produced by {@link YuhoParser#block}.
	 * @param ctx the parse tree
	 */
	void enterBlock(YuhoParser.BlockContext ctx);
	/**
	 * Exit a parse tree produced by {@link YuhoParser#block}.
	 * @param ctx the parse tree
	 */
	void exitBlock(YuhoParser.BlockContext ctx);
}