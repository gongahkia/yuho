// Generated from Yuho.g4 by ANTLR 4.13.2
import org.antlr.v4.runtime.atn.*;
import org.antlr.v4.runtime.dfa.DFA;
import org.antlr.v4.runtime.*;
import org.antlr.v4.runtime.misc.*;
import org.antlr.v4.runtime.tree.*;
import java.util.List;
import java.util.Iterator;
import java.util.ArrayList;

@SuppressWarnings({"all", "warnings", "unchecked", "unused", "cast", "CheckReturnValue", "this-escape"})
public class YuhoParser extends Parser {
	static { RuntimeMetaData.checkVersion("4.13.2", RuntimeMetaData.VERSION); }

	protected static final DFA[] _decisionToDFA;
	protected static final PredictionContextCache _sharedContextCache =
		new PredictionContextCache();
	public static final int
		T__0=1, T__1=2, T__2=3, T__3=4, T__4=5, T__5=6, T__6=7, T__7=8, COMMENT=9, 
		MULTILINE_COMMENT=10, TRUE=11, FALSE=12, MATCH=13, CASE=14, CONSEQUENCE=15, 
		PASS=16, STRUCT=17, FN=18, PERCENT=19, MONEY_PREFIX=20, DAY=21, MONTH=22, 
		YEAR=23, DURATION_UNITS=24, IDENTIFIER=25, DOT=26, STRING=27, INTEGER=28, 
		FLOAT=29, PERCENTAGE=30, MONEY=31, DATE=32, DURATION=33, PLUS=34, MINUS=35, 
		MULT=36, DIV=37, ASSIGN=38, EQUAL=39, NOTEQUAL=40, GT=41, LT=42, AND=43, 
		OR=44, SEMICOLON=45, COLON=46, LBRACE=47, RBRACE=48, LPAREN=49, RPAREN=50, 
		COMMA=51, UNDERSCORE=52, WS=53;
	public static final int
		RULE_program = 0, RULE_declaration = 1, RULE_type = 2, RULE_expression = 3, 
		RULE_literal = 4, RULE_statement = 5, RULE_assignment = 6, RULE_matchCase = 7, 
		RULE_caseClause = 8, RULE_passStatement = 9, RULE_functionDefinition = 10, 
		RULE_parameterList = 11, RULE_parameter = 12, RULE_functionCall = 13, 
		RULE_argumentList = 14, RULE_structDefinition = 15, RULE_structMember = 16, 
		RULE_block = 17;
	private static String[] makeRuleNames() {
		return new String[] {
			"program", "declaration", "type", "expression", "literal", "statement", 
			"assignment", "matchCase", "caseClause", "passStatement", "functionDefinition", 
			"parameterList", "parameter", "functionCall", "argumentList", "structDefinition", 
			"structMember", "block"
		};
	}
	public static final String[] ruleNames = makeRuleNames();

	private static String[] makeLiteralNames() {
		return new String[] {
			null, "'int'", "'float'", "'percent'", "'money'", "'date'", "'duration'", 
			"'bool'", "'string'", null, null, "'TRUE'", "'FALSE'", "'match'", "'case'", 
			"'consequence'", "'pass'", "'struct'", "'fn'", "'%'", "'$'", "'day'", 
			"'month'", "'year'", null, null, "'.'", null, null, null, null, null, 
			null, null, "'+'", "'-'", "'*'", "'/'", "':='", "'=='", "'!='", "'>'", 
			"'<'", "'&&'", "'||'", "';'", "':'", "'{'", "'}'", "'('", "')'", "','", 
			"'_'"
		};
	}
	private static final String[] _LITERAL_NAMES = makeLiteralNames();
	private static String[] makeSymbolicNames() {
		return new String[] {
			null, null, null, null, null, null, null, null, null, "COMMENT", "MULTILINE_COMMENT", 
			"TRUE", "FALSE", "MATCH", "CASE", "CONSEQUENCE", "PASS", "STRUCT", "FN", 
			"PERCENT", "MONEY_PREFIX", "DAY", "MONTH", "YEAR", "DURATION_UNITS", 
			"IDENTIFIER", "DOT", "STRING", "INTEGER", "FLOAT", "PERCENTAGE", "MONEY", 
			"DATE", "DURATION", "PLUS", "MINUS", "MULT", "DIV", "ASSIGN", "EQUAL", 
			"NOTEQUAL", "GT", "LT", "AND", "OR", "SEMICOLON", "COLON", "LBRACE", 
			"RBRACE", "LPAREN", "RPAREN", "COMMA", "UNDERSCORE", "WS"
		};
	}
	private static final String[] _SYMBOLIC_NAMES = makeSymbolicNames();
	public static final Vocabulary VOCABULARY = new VocabularyImpl(_LITERAL_NAMES, _SYMBOLIC_NAMES);

	/**
	 * @deprecated Use {@link #VOCABULARY} instead.
	 */
	@Deprecated
	public static final String[] tokenNames;
	static {
		tokenNames = new String[_SYMBOLIC_NAMES.length];
		for (int i = 0; i < tokenNames.length; i++) {
			tokenNames[i] = VOCABULARY.getLiteralName(i);
			if (tokenNames[i] == null) {
				tokenNames[i] = VOCABULARY.getSymbolicName(i);
			}

			if (tokenNames[i] == null) {
				tokenNames[i] = "<INVALID>";
			}
		}
	}

	@Override
	@Deprecated
	public String[] getTokenNames() {
		return tokenNames;
	}

	@Override

	public Vocabulary getVocabulary() {
		return VOCABULARY;
	}

	@Override
	public String getGrammarFileName() { return "Yuho.g4"; }

	@Override
	public String[] getRuleNames() { return ruleNames; }

	@Override
	public String getSerializedATN() { return _serializedATN; }

	@Override
	public ATN getATN() { return _ATN; }

	public YuhoParser(TokenStream input) {
		super(input);
		_interp = new ParserATNSimulator(this,_ATN,_decisionToDFA,_sharedContextCache);
	}

	@SuppressWarnings("CheckReturnValue")
	public static class ProgramContext extends ParserRuleContext {
		public TerminalNode EOF() { return getToken(YuhoParser.EOF, 0); }
		public List<DeclarationContext> declaration() {
			return getRuleContexts(DeclarationContext.class);
		}
		public DeclarationContext declaration(int i) {
			return getRuleContext(DeclarationContext.class,i);
		}
		public List<FunctionDefinitionContext> functionDefinition() {
			return getRuleContexts(FunctionDefinitionContext.class);
		}
		public FunctionDefinitionContext functionDefinition(int i) {
			return getRuleContext(FunctionDefinitionContext.class,i);
		}
		public List<StructDefinitionContext> structDefinition() {
			return getRuleContexts(StructDefinitionContext.class);
		}
		public StructDefinitionContext structDefinition(int i) {
			return getRuleContext(StructDefinitionContext.class,i);
		}
		public List<MatchCaseContext> matchCase() {
			return getRuleContexts(MatchCaseContext.class);
		}
		public MatchCaseContext matchCase(int i) {
			return getRuleContext(MatchCaseContext.class,i);
		}
		public ProgramContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_program; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterProgram(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitProgram(this);
		}
	}

	public final ProgramContext program() throws RecognitionException {
		ProgramContext _localctx = new ProgramContext(_ctx, getState());
		enterRule(_localctx, 0, RULE_program);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(42);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while ((((_la) & ~0x3f) == 0 && ((1L << _la) & 33956350L) != 0)) {
				{
				setState(40);
				_errHandler.sync(this);
				switch (_input.LA(1)) {
				case T__0:
				case T__1:
				case T__2:
				case T__3:
				case T__4:
				case T__5:
				case T__6:
				case T__7:
				case IDENTIFIER:
					{
					setState(36);
					declaration();
					}
					break;
				case FN:
					{
					setState(37);
					functionDefinition();
					}
					break;
				case STRUCT:
					{
					setState(38);
					structDefinition();
					}
					break;
				case MATCH:
					{
					setState(39);
					matchCase();
					}
					break;
				default:
					throw new NoViableAltException(this);
				}
				}
				setState(44);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(45);
			match(EOF);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class DeclarationContext extends ParserRuleContext {
		public TypeContext type() {
			return getRuleContext(TypeContext.class,0);
		}
		public TerminalNode IDENTIFIER() { return getToken(YuhoParser.IDENTIFIER, 0); }
		public TerminalNode ASSIGN() { return getToken(YuhoParser.ASSIGN, 0); }
		public ExpressionContext expression() {
			return getRuleContext(ExpressionContext.class,0);
		}
		public TerminalNode SEMICOLON() { return getToken(YuhoParser.SEMICOLON, 0); }
		public DeclarationContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_declaration; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterDeclaration(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitDeclaration(this);
		}
	}

	public final DeclarationContext declaration() throws RecognitionException {
		DeclarationContext _localctx = new DeclarationContext(_ctx, getState());
		enterRule(_localctx, 2, RULE_declaration);
		try {
			setState(57);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,2,_ctx) ) {
			case 1:
				enterOuterAlt(_localctx, 1);
				{
				setState(47);
				type();
				setState(48);
				match(IDENTIFIER);
				setState(49);
				match(ASSIGN);
				setState(50);
				expression(0);
				setState(51);
				match(SEMICOLON);
				}
				break;
			case 2:
				enterOuterAlt(_localctx, 2);
				{
				setState(53);
				type();
				setState(54);
				match(IDENTIFIER);
				setState(55);
				match(SEMICOLON);
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class TypeContext extends ParserRuleContext {
		public TerminalNode IDENTIFIER() { return getToken(YuhoParser.IDENTIFIER, 0); }
		public TypeContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_type; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterType(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitType(this);
		}
	}

	public final TypeContext type() throws RecognitionException {
		TypeContext _localctx = new TypeContext(_ctx, getState());
		enterRule(_localctx, 4, RULE_type);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(59);
			_la = _input.LA(1);
			if ( !((((_la) & ~0x3f) == 0 && ((1L << _la) & 33554942L) != 0)) ) {
			_errHandler.recoverInline(this);
			}
			else {
				if ( _input.LA(1)==Token.EOF ) matchedEOF = true;
				_errHandler.reportMatch(this);
				consume();
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class ExpressionContext extends ParserRuleContext {
		public List<TerminalNode> IDENTIFIER() { return getTokens(YuhoParser.IDENTIFIER); }
		public TerminalNode IDENTIFIER(int i) {
			return getToken(YuhoParser.IDENTIFIER, i);
		}
		public TerminalNode DOT() { return getToken(YuhoParser.DOT, 0); }
		public LiteralContext literal() {
			return getRuleContext(LiteralContext.class,0);
		}
		public List<ExpressionContext> expression() {
			return getRuleContexts(ExpressionContext.class);
		}
		public ExpressionContext expression(int i) {
			return getRuleContext(ExpressionContext.class,i);
		}
		public TerminalNode PLUS() { return getToken(YuhoParser.PLUS, 0); }
		public TerminalNode MINUS() { return getToken(YuhoParser.MINUS, 0); }
		public TerminalNode MULT() { return getToken(YuhoParser.MULT, 0); }
		public TerminalNode DIV() { return getToken(YuhoParser.DIV, 0); }
		public TerminalNode GT() { return getToken(YuhoParser.GT, 0); }
		public TerminalNode LT() { return getToken(YuhoParser.LT, 0); }
		public TerminalNode EQUAL() { return getToken(YuhoParser.EQUAL, 0); }
		public TerminalNode NOTEQUAL() { return getToken(YuhoParser.NOTEQUAL, 0); }
		public TerminalNode AND() { return getToken(YuhoParser.AND, 0); }
		public TerminalNode OR() { return getToken(YuhoParser.OR, 0); }
		public ExpressionContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_expression; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterExpression(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitExpression(this);
		}
	}

	public final ExpressionContext expression() throws RecognitionException {
		return expression(0);
	}

	private ExpressionContext expression(int _p) throws RecognitionException {
		ParserRuleContext _parentctx = _ctx;
		int _parentState = getState();
		ExpressionContext _localctx = new ExpressionContext(_ctx, _parentState);
		ExpressionContext _prevctx = _localctx;
		int _startState = 6;
		enterRecursionRule(_localctx, 6, RULE_expression, _p);
		int _la;
		try {
			int _alt;
			enterOuterAlt(_localctx, 1);
			{
			setState(67);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,3,_ctx) ) {
			case 1:
				{
				setState(62);
				match(IDENTIFIER);
				}
				break;
			case 2:
				{
				setState(63);
				match(IDENTIFIER);
				setState(64);
				match(DOT);
				setState(65);
				match(IDENTIFIER);
				}
				break;
			case 3:
				{
				setState(66);
				literal();
				}
				break;
			}
			_ctx.stop = _input.LT(-1);
			setState(80);
			_errHandler.sync(this);
			_alt = getInterpreter().adaptivePredict(_input,5,_ctx);
			while ( _alt!=2 && _alt!=org.antlr.v4.runtime.atn.ATN.INVALID_ALT_NUMBER ) {
				if ( _alt==1 ) {
					if ( _parseListeners!=null ) triggerExitRuleEvent();
					_prevctx = _localctx;
					{
					setState(78);
					_errHandler.sync(this);
					switch ( getInterpreter().adaptivePredict(_input,4,_ctx) ) {
					case 1:
						{
						_localctx = new ExpressionContext(_parentctx, _parentState);
						pushNewRecursionContext(_localctx, _startState, RULE_expression);
						setState(69);
						if (!(precpred(_ctx, 6))) throw new FailedPredicateException(this, "precpred(_ctx, 6)");
						setState(70);
						_la = _input.LA(1);
						if ( !((((_la) & ~0x3f) == 0 && ((1L << _la) & 257698037760L) != 0)) ) {
						_errHandler.recoverInline(this);
						}
						else {
							if ( _input.LA(1)==Token.EOF ) matchedEOF = true;
							_errHandler.reportMatch(this);
							consume();
						}
						setState(71);
						expression(7);
						}
						break;
					case 2:
						{
						_localctx = new ExpressionContext(_parentctx, _parentState);
						pushNewRecursionContext(_localctx, _startState, RULE_expression);
						setState(72);
						if (!(precpred(_ctx, 5))) throw new FailedPredicateException(this, "precpred(_ctx, 5)");
						setState(73);
						_la = _input.LA(1);
						if ( !((((_la) & ~0x3f) == 0 && ((1L << _la) & 8246337208320L) != 0)) ) {
						_errHandler.recoverInline(this);
						}
						else {
							if ( _input.LA(1)==Token.EOF ) matchedEOF = true;
							_errHandler.reportMatch(this);
							consume();
						}
						setState(74);
						expression(6);
						}
						break;
					case 3:
						{
						_localctx = new ExpressionContext(_parentctx, _parentState);
						pushNewRecursionContext(_localctx, _startState, RULE_expression);
						setState(75);
						if (!(precpred(_ctx, 4))) throw new FailedPredicateException(this, "precpred(_ctx, 4)");
						setState(76);
						_la = _input.LA(1);
						if ( !(_la==AND || _la==OR) ) {
						_errHandler.recoverInline(this);
						}
						else {
							if ( _input.LA(1)==Token.EOF ) matchedEOF = true;
							_errHandler.reportMatch(this);
							consume();
						}
						setState(77);
						expression(5);
						}
						break;
					}
					} 
				}
				setState(82);
				_errHandler.sync(this);
				_alt = getInterpreter().adaptivePredict(_input,5,_ctx);
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			unrollRecursionContexts(_parentctx);
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class LiteralContext extends ParserRuleContext {
		public TerminalNode STRING() { return getToken(YuhoParser.STRING, 0); }
		public TerminalNode INTEGER() { return getToken(YuhoParser.INTEGER, 0); }
		public TerminalNode FLOAT() { return getToken(YuhoParser.FLOAT, 0); }
		public TerminalNode PERCENTAGE() { return getToken(YuhoParser.PERCENTAGE, 0); }
		public TerminalNode MONEY() { return getToken(YuhoParser.MONEY, 0); }
		public TerminalNode DATE() { return getToken(YuhoParser.DATE, 0); }
		public TerminalNode DURATION() { return getToken(YuhoParser.DURATION, 0); }
		public TerminalNode TRUE() { return getToken(YuhoParser.TRUE, 0); }
		public TerminalNode FALSE() { return getToken(YuhoParser.FALSE, 0); }
		public LiteralContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_literal; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterLiteral(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitLiteral(this);
		}
	}

	public final LiteralContext literal() throws RecognitionException {
		LiteralContext _localctx = new LiteralContext(_ctx, getState());
		enterRule(_localctx, 8, RULE_literal);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(83);
			_la = _input.LA(1);
			if ( !((((_la) & ~0x3f) == 0 && ((1L << _la) & 17045657600L) != 0)) ) {
			_errHandler.recoverInline(this);
			}
			else {
				if ( _input.LA(1)==Token.EOF ) matchedEOF = true;
				_errHandler.reportMatch(this);
				consume();
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class StatementContext extends ParserRuleContext {
		public DeclarationContext declaration() {
			return getRuleContext(DeclarationContext.class,0);
		}
		public AssignmentContext assignment() {
			return getRuleContext(AssignmentContext.class,0);
		}
		public FunctionCallContext functionCall() {
			return getRuleContext(FunctionCallContext.class,0);
		}
		public MatchCaseContext matchCase() {
			return getRuleContext(MatchCaseContext.class,0);
		}
		public PassStatementContext passStatement() {
			return getRuleContext(PassStatementContext.class,0);
		}
		public StatementContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_statement; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterStatement(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitStatement(this);
		}
	}

	public final StatementContext statement() throws RecognitionException {
		StatementContext _localctx = new StatementContext(_ctx, getState());
		enterRule(_localctx, 10, RULE_statement);
		try {
			setState(90);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,6,_ctx) ) {
			case 1:
				enterOuterAlt(_localctx, 1);
				{
				setState(85);
				declaration();
				}
				break;
			case 2:
				enterOuterAlt(_localctx, 2);
				{
				setState(86);
				assignment();
				}
				break;
			case 3:
				enterOuterAlt(_localctx, 3);
				{
				setState(87);
				functionCall();
				}
				break;
			case 4:
				enterOuterAlt(_localctx, 4);
				{
				setState(88);
				matchCase();
				}
				break;
			case 5:
				enterOuterAlt(_localctx, 5);
				{
				setState(89);
				passStatement();
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class AssignmentContext extends ParserRuleContext {
		public TerminalNode IDENTIFIER() { return getToken(YuhoParser.IDENTIFIER, 0); }
		public TerminalNode ASSIGN() { return getToken(YuhoParser.ASSIGN, 0); }
		public ExpressionContext expression() {
			return getRuleContext(ExpressionContext.class,0);
		}
		public TerminalNode SEMICOLON() { return getToken(YuhoParser.SEMICOLON, 0); }
		public AssignmentContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_assignment; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterAssignment(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitAssignment(this);
		}
	}

	public final AssignmentContext assignment() throws RecognitionException {
		AssignmentContext _localctx = new AssignmentContext(_ctx, getState());
		enterRule(_localctx, 12, RULE_assignment);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(92);
			match(IDENTIFIER);
			setState(93);
			match(ASSIGN);
			setState(94);
			expression(0);
			setState(95);
			match(SEMICOLON);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class MatchCaseContext extends ParserRuleContext {
		public TerminalNode MATCH() { return getToken(YuhoParser.MATCH, 0); }
		public TerminalNode LBRACE() { return getToken(YuhoParser.LBRACE, 0); }
		public TerminalNode RBRACE() { return getToken(YuhoParser.RBRACE, 0); }
		public TerminalNode LPAREN() { return getToken(YuhoParser.LPAREN, 0); }
		public ExpressionContext expression() {
			return getRuleContext(ExpressionContext.class,0);
		}
		public TerminalNode RPAREN() { return getToken(YuhoParser.RPAREN, 0); }
		public List<CaseClauseContext> caseClause() {
			return getRuleContexts(CaseClauseContext.class);
		}
		public CaseClauseContext caseClause(int i) {
			return getRuleContext(CaseClauseContext.class,i);
		}
		public MatchCaseContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_matchCase; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterMatchCase(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitMatchCase(this);
		}
	}

	public final MatchCaseContext matchCase() throws RecognitionException {
		MatchCaseContext _localctx = new MatchCaseContext(_ctx, getState());
		enterRule(_localctx, 14, RULE_matchCase);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(97);
			match(MATCH);
			setState(102);
			_errHandler.sync(this);
			_la = _input.LA(1);
			if (_la==LPAREN) {
				{
				setState(98);
				match(LPAREN);
				setState(99);
				expression(0);
				setState(100);
				match(RPAREN);
				}
			}

			setState(104);
			match(LBRACE);
			setState(108);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while (_la==CASE) {
				{
				{
				setState(105);
				caseClause();
				}
				}
				setState(110);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(111);
			match(RBRACE);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class CaseClauseContext extends ParserRuleContext {
		public TerminalNode CASE() { return getToken(YuhoParser.CASE, 0); }
		public List<ExpressionContext> expression() {
			return getRuleContexts(ExpressionContext.class);
		}
		public ExpressionContext expression(int i) {
			return getRuleContext(ExpressionContext.class,i);
		}
		public TerminalNode ASSIGN() { return getToken(YuhoParser.ASSIGN, 0); }
		public TerminalNode CONSEQUENCE() { return getToken(YuhoParser.CONSEQUENCE, 0); }
		public TerminalNode SEMICOLON() { return getToken(YuhoParser.SEMICOLON, 0); }
		public TerminalNode UNDERSCORE() { return getToken(YuhoParser.UNDERSCORE, 0); }
		public PassStatementContext passStatement() {
			return getRuleContext(PassStatementContext.class,0);
		}
		public CaseClauseContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_caseClause; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterCaseClause(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitCaseClause(this);
		}
	}

	public final CaseClauseContext caseClause() throws RecognitionException {
		CaseClauseContext _localctx = new CaseClauseContext(_ctx, getState());
		enterRule(_localctx, 16, RULE_caseClause);
		try {
			setState(127);
			_errHandler.sync(this);
			switch ( getInterpreter().adaptivePredict(_input,9,_ctx) ) {
			case 1:
				enterOuterAlt(_localctx, 1);
				{
				setState(113);
				match(CASE);
				setState(114);
				expression(0);
				setState(115);
				match(ASSIGN);
				setState(116);
				match(CONSEQUENCE);
				setState(117);
				expression(0);
				setState(118);
				match(SEMICOLON);
				}
				break;
			case 2:
				enterOuterAlt(_localctx, 2);
				{
				setState(120);
				match(CASE);
				setState(121);
				match(UNDERSCORE);
				setState(122);
				match(ASSIGN);
				setState(123);
				match(CONSEQUENCE);
				setState(124);
				passStatement();
				setState(125);
				match(SEMICOLON);
				}
				break;
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class PassStatementContext extends ParserRuleContext {
		public TerminalNode PASS() { return getToken(YuhoParser.PASS, 0); }
		public TerminalNode SEMICOLON() { return getToken(YuhoParser.SEMICOLON, 0); }
		public PassStatementContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_passStatement; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterPassStatement(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitPassStatement(this);
		}
	}

	public final PassStatementContext passStatement() throws RecognitionException {
		PassStatementContext _localctx = new PassStatementContext(_ctx, getState());
		enterRule(_localctx, 18, RULE_passStatement);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(129);
			match(PASS);
			setState(130);
			match(SEMICOLON);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class FunctionDefinitionContext extends ParserRuleContext {
		public TerminalNode FN() { return getToken(YuhoParser.FN, 0); }
		public TerminalNode IDENTIFIER() { return getToken(YuhoParser.IDENTIFIER, 0); }
		public TerminalNode LPAREN() { return getToken(YuhoParser.LPAREN, 0); }
		public ParameterListContext parameterList() {
			return getRuleContext(ParameterListContext.class,0);
		}
		public TerminalNode RPAREN() { return getToken(YuhoParser.RPAREN, 0); }
		public TerminalNode COLON() { return getToken(YuhoParser.COLON, 0); }
		public TypeContext type() {
			return getRuleContext(TypeContext.class,0);
		}
		public BlockContext block() {
			return getRuleContext(BlockContext.class,0);
		}
		public FunctionDefinitionContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_functionDefinition; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterFunctionDefinition(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitFunctionDefinition(this);
		}
	}

	public final FunctionDefinitionContext functionDefinition() throws RecognitionException {
		FunctionDefinitionContext _localctx = new FunctionDefinitionContext(_ctx, getState());
		enterRule(_localctx, 20, RULE_functionDefinition);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(132);
			match(FN);
			setState(133);
			match(IDENTIFIER);
			setState(134);
			match(LPAREN);
			setState(135);
			parameterList();
			setState(136);
			match(RPAREN);
			setState(137);
			match(COLON);
			setState(138);
			type();
			setState(139);
			block();
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class ParameterListContext extends ParserRuleContext {
		public List<ParameterContext> parameter() {
			return getRuleContexts(ParameterContext.class);
		}
		public ParameterContext parameter(int i) {
			return getRuleContext(ParameterContext.class,i);
		}
		public List<TerminalNode> COMMA() { return getTokens(YuhoParser.COMMA); }
		public TerminalNode COMMA(int i) {
			return getToken(YuhoParser.COMMA, i);
		}
		public ParameterListContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_parameterList; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterParameterList(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitParameterList(this);
		}
	}

	public final ParameterListContext parameterList() throws RecognitionException {
		ParameterListContext _localctx = new ParameterListContext(_ctx, getState());
		enterRule(_localctx, 22, RULE_parameterList);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(149);
			_errHandler.sync(this);
			_la = _input.LA(1);
			if ((((_la) & ~0x3f) == 0 && ((1L << _la) & 33554942L) != 0)) {
				{
				setState(141);
				parameter();
				setState(146);
				_errHandler.sync(this);
				_la = _input.LA(1);
				while (_la==COMMA) {
					{
					{
					setState(142);
					match(COMMA);
					setState(143);
					parameter();
					}
					}
					setState(148);
					_errHandler.sync(this);
					_la = _input.LA(1);
				}
				}
			}

			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class ParameterContext extends ParserRuleContext {
		public TypeContext type() {
			return getRuleContext(TypeContext.class,0);
		}
		public TerminalNode IDENTIFIER() { return getToken(YuhoParser.IDENTIFIER, 0); }
		public ParameterContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_parameter; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterParameter(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitParameter(this);
		}
	}

	public final ParameterContext parameter() throws RecognitionException {
		ParameterContext _localctx = new ParameterContext(_ctx, getState());
		enterRule(_localctx, 24, RULE_parameter);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(151);
			type();
			setState(152);
			match(IDENTIFIER);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class FunctionCallContext extends ParserRuleContext {
		public TerminalNode IDENTIFIER() { return getToken(YuhoParser.IDENTIFIER, 0); }
		public TerminalNode LPAREN() { return getToken(YuhoParser.LPAREN, 0); }
		public ArgumentListContext argumentList() {
			return getRuleContext(ArgumentListContext.class,0);
		}
		public TerminalNode RPAREN() { return getToken(YuhoParser.RPAREN, 0); }
		public TerminalNode SEMICOLON() { return getToken(YuhoParser.SEMICOLON, 0); }
		public FunctionCallContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_functionCall; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterFunctionCall(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitFunctionCall(this);
		}
	}

	public final FunctionCallContext functionCall() throws RecognitionException {
		FunctionCallContext _localctx = new FunctionCallContext(_ctx, getState());
		enterRule(_localctx, 26, RULE_functionCall);
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(154);
			match(IDENTIFIER);
			setState(155);
			match(LPAREN);
			setState(156);
			argumentList();
			setState(157);
			match(RPAREN);
			setState(158);
			match(SEMICOLON);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class ArgumentListContext extends ParserRuleContext {
		public List<ExpressionContext> expression() {
			return getRuleContexts(ExpressionContext.class);
		}
		public ExpressionContext expression(int i) {
			return getRuleContext(ExpressionContext.class,i);
		}
		public List<TerminalNode> COMMA() { return getTokens(YuhoParser.COMMA); }
		public TerminalNode COMMA(int i) {
			return getToken(YuhoParser.COMMA, i);
		}
		public ArgumentListContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_argumentList; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterArgumentList(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitArgumentList(this);
		}
	}

	public final ArgumentListContext argumentList() throws RecognitionException {
		ArgumentListContext _localctx = new ArgumentListContext(_ctx, getState());
		enterRule(_localctx, 28, RULE_argumentList);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(168);
			_errHandler.sync(this);
			_la = _input.LA(1);
			if ((((_la) & ~0x3f) == 0 && ((1L << _la) & 17079212032L) != 0)) {
				{
				setState(160);
				expression(0);
				setState(165);
				_errHandler.sync(this);
				_la = _input.LA(1);
				while (_la==COMMA) {
					{
					{
					setState(161);
					match(COMMA);
					setState(162);
					expression(0);
					}
					}
					setState(167);
					_errHandler.sync(this);
					_la = _input.LA(1);
				}
				}
			}

			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class StructDefinitionContext extends ParserRuleContext {
		public TerminalNode STRUCT() { return getToken(YuhoParser.STRUCT, 0); }
		public TerminalNode IDENTIFIER() { return getToken(YuhoParser.IDENTIFIER, 0); }
		public TerminalNode LBRACE() { return getToken(YuhoParser.LBRACE, 0); }
		public TerminalNode RBRACE() { return getToken(YuhoParser.RBRACE, 0); }
		public List<StructMemberContext> structMember() {
			return getRuleContexts(StructMemberContext.class);
		}
		public StructMemberContext structMember(int i) {
			return getRuleContext(StructMemberContext.class,i);
		}
		public StructDefinitionContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_structDefinition; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterStructDefinition(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitStructDefinition(this);
		}
	}

	public final StructDefinitionContext structDefinition() throws RecognitionException {
		StructDefinitionContext _localctx = new StructDefinitionContext(_ctx, getState());
		enterRule(_localctx, 30, RULE_structDefinition);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(170);
			match(STRUCT);
			setState(171);
			match(IDENTIFIER);
			setState(172);
			match(LBRACE);
			setState(176);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while ((((_la) & ~0x3f) == 0 && ((1L << _la) & 33554942L) != 0)) {
				{
				{
				setState(173);
				structMember();
				}
				}
				setState(178);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(179);
			match(RBRACE);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class StructMemberContext extends ParserRuleContext {
		public TypeContext type() {
			return getRuleContext(TypeContext.class,0);
		}
		public TerminalNode IDENTIFIER() { return getToken(YuhoParser.IDENTIFIER, 0); }
		public TerminalNode COMMA() { return getToken(YuhoParser.COMMA, 0); }
		public TerminalNode SEMICOLON() { return getToken(YuhoParser.SEMICOLON, 0); }
		public StructMemberContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_structMember; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterStructMember(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitStructMember(this);
		}
	}

	public final StructMemberContext structMember() throws RecognitionException {
		StructMemberContext _localctx = new StructMemberContext(_ctx, getState());
		enterRule(_localctx, 32, RULE_structMember);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(181);
			type();
			setState(182);
			match(IDENTIFIER);
			setState(183);
			_la = _input.LA(1);
			if ( !(_la==SEMICOLON || _la==COMMA) ) {
			_errHandler.recoverInline(this);
			}
			else {
				if ( _input.LA(1)==Token.EOF ) matchedEOF = true;
				_errHandler.reportMatch(this);
				consume();
			}
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	@SuppressWarnings("CheckReturnValue")
	public static class BlockContext extends ParserRuleContext {
		public TerminalNode LBRACE() { return getToken(YuhoParser.LBRACE, 0); }
		public TerminalNode RBRACE() { return getToken(YuhoParser.RBRACE, 0); }
		public List<StatementContext> statement() {
			return getRuleContexts(StatementContext.class);
		}
		public StatementContext statement(int i) {
			return getRuleContext(StatementContext.class,i);
		}
		public BlockContext(ParserRuleContext parent, int invokingState) {
			super(parent, invokingState);
		}
		@Override public int getRuleIndex() { return RULE_block; }
		@Override
		public void enterRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).enterBlock(this);
		}
		@Override
		public void exitRule(ParseTreeListener listener) {
			if ( listener instanceof YuhoListener ) ((YuhoListener)listener).exitBlock(this);
		}
	}

	public final BlockContext block() throws RecognitionException {
		BlockContext _localctx = new BlockContext(_ctx, getState());
		enterRule(_localctx, 34, RULE_block);
		int _la;
		try {
			enterOuterAlt(_localctx, 1);
			{
			setState(185);
			match(LBRACE);
			setState(189);
			_errHandler.sync(this);
			_la = _input.LA(1);
			while ((((_la) & ~0x3f) == 0 && ((1L << _la) & 33628670L) != 0)) {
				{
				{
				setState(186);
				statement();
				}
				}
				setState(191);
				_errHandler.sync(this);
				_la = _input.LA(1);
			}
			setState(192);
			match(RBRACE);
			}
		}
		catch (RecognitionException re) {
			_localctx.exception = re;
			_errHandler.reportError(this, re);
			_errHandler.recover(this, re);
		}
		finally {
			exitRule();
		}
		return _localctx;
	}

	public boolean sempred(RuleContext _localctx, int ruleIndex, int predIndex) {
		switch (ruleIndex) {
		case 3:
			return expression_sempred((ExpressionContext)_localctx, predIndex);
		}
		return true;
	}
	private boolean expression_sempred(ExpressionContext _localctx, int predIndex) {
		switch (predIndex) {
		case 0:
			return precpred(_ctx, 6);
		case 1:
			return precpred(_ctx, 5);
		case 2:
			return precpred(_ctx, 4);
		}
		return true;
	}

	public static final String _serializedATN =
		"\u0004\u00015\u00c3\u0002\u0000\u0007\u0000\u0002\u0001\u0007\u0001\u0002"+
		"\u0002\u0007\u0002\u0002\u0003\u0007\u0003\u0002\u0004\u0007\u0004\u0002"+
		"\u0005\u0007\u0005\u0002\u0006\u0007\u0006\u0002\u0007\u0007\u0007\u0002"+
		"\b\u0007\b\u0002\t\u0007\t\u0002\n\u0007\n\u0002\u000b\u0007\u000b\u0002"+
		"\f\u0007\f\u0002\r\u0007\r\u0002\u000e\u0007\u000e\u0002\u000f\u0007\u000f"+
		"\u0002\u0010\u0007\u0010\u0002\u0011\u0007\u0011\u0001\u0000\u0001\u0000"+
		"\u0001\u0000\u0001\u0000\u0005\u0000)\b\u0000\n\u0000\f\u0000,\t\u0000"+
		"\u0001\u0000\u0001\u0000\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001"+
		"\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001"+
		"\u0003\u0001:\b\u0001\u0001\u0002\u0001\u0002\u0001\u0003\u0001\u0003"+
		"\u0001\u0003\u0001\u0003\u0001\u0003\u0001\u0003\u0003\u0003D\b\u0003"+
		"\u0001\u0003\u0001\u0003\u0001\u0003\u0001\u0003\u0001\u0003\u0001\u0003"+
		"\u0001\u0003\u0001\u0003\u0001\u0003\u0005\u0003O\b\u0003\n\u0003\f\u0003"+
		"R\t\u0003\u0001\u0004\u0001\u0004\u0001\u0005\u0001\u0005\u0001\u0005"+
		"\u0001\u0005\u0001\u0005\u0003\u0005[\b\u0005\u0001\u0006\u0001\u0006"+
		"\u0001\u0006\u0001\u0006\u0001\u0006\u0001\u0007\u0001\u0007\u0001\u0007"+
		"\u0001\u0007\u0001\u0007\u0003\u0007g\b\u0007\u0001\u0007\u0001\u0007"+
		"\u0005\u0007k\b\u0007\n\u0007\f\u0007n\t\u0007\u0001\u0007\u0001\u0007"+
		"\u0001\b\u0001\b\u0001\b\u0001\b\u0001\b\u0001\b\u0001\b\u0001\b\u0001"+
		"\b\u0001\b\u0001\b\u0001\b\u0001\b\u0001\b\u0003\b\u0080\b\b\u0001\t\u0001"+
		"\t\u0001\t\u0001\n\u0001\n\u0001\n\u0001\n\u0001\n\u0001\n\u0001\n\u0001"+
		"\n\u0001\n\u0001\u000b\u0001\u000b\u0001\u000b\u0005\u000b\u0091\b\u000b"+
		"\n\u000b\f\u000b\u0094\t\u000b\u0003\u000b\u0096\b\u000b\u0001\f\u0001"+
		"\f\u0001\f\u0001\r\u0001\r\u0001\r\u0001\r\u0001\r\u0001\r\u0001\u000e"+
		"\u0001\u000e\u0001\u000e\u0005\u000e\u00a4\b\u000e\n\u000e\f\u000e\u00a7"+
		"\t\u000e\u0003\u000e\u00a9\b\u000e\u0001\u000f\u0001\u000f\u0001\u000f"+
		"\u0001\u000f\u0005\u000f\u00af\b\u000f\n\u000f\f\u000f\u00b2\t\u000f\u0001"+
		"\u000f\u0001\u000f\u0001\u0010\u0001\u0010\u0001\u0010\u0001\u0010\u0001"+
		"\u0011\u0001\u0011\u0005\u0011\u00bc\b\u0011\n\u0011\f\u0011\u00bf\t\u0011"+
		"\u0001\u0011\u0001\u0011\u0001\u0011\u0000\u0001\u0006\u0012\u0000\u0002"+
		"\u0004\u0006\b\n\f\u000e\u0010\u0012\u0014\u0016\u0018\u001a\u001c\u001e"+
		" \"\u0000\u0006\u0002\u0000\u0001\b\u0019\u0019\u0001\u0000\"%\u0001\u0000"+
		"\'*\u0001\u0000+,\u0002\u0000\u000b\f\u001b!\u0002\u0000--33\u00c7\u0000"+
		"*\u0001\u0000\u0000\u0000\u00029\u0001\u0000\u0000\u0000\u0004;\u0001"+
		"\u0000\u0000\u0000\u0006C\u0001\u0000\u0000\u0000\bS\u0001\u0000\u0000"+
		"\u0000\nZ\u0001\u0000\u0000\u0000\f\\\u0001\u0000\u0000\u0000\u000ea\u0001"+
		"\u0000\u0000\u0000\u0010\u007f\u0001\u0000\u0000\u0000\u0012\u0081\u0001"+
		"\u0000\u0000\u0000\u0014\u0084\u0001\u0000\u0000\u0000\u0016\u0095\u0001"+
		"\u0000\u0000\u0000\u0018\u0097\u0001\u0000\u0000\u0000\u001a\u009a\u0001"+
		"\u0000\u0000\u0000\u001c\u00a8\u0001\u0000\u0000\u0000\u001e\u00aa\u0001"+
		"\u0000\u0000\u0000 \u00b5\u0001\u0000\u0000\u0000\"\u00b9\u0001\u0000"+
		"\u0000\u0000$)\u0003\u0002\u0001\u0000%)\u0003\u0014\n\u0000&)\u0003\u001e"+
		"\u000f\u0000\')\u0003\u000e\u0007\u0000($\u0001\u0000\u0000\u0000(%\u0001"+
		"\u0000\u0000\u0000(&\u0001\u0000\u0000\u0000(\'\u0001\u0000\u0000\u0000"+
		"),\u0001\u0000\u0000\u0000*(\u0001\u0000\u0000\u0000*+\u0001\u0000\u0000"+
		"\u0000+-\u0001\u0000\u0000\u0000,*\u0001\u0000\u0000\u0000-.\u0005\u0000"+
		"\u0000\u0001.\u0001\u0001\u0000\u0000\u0000/0\u0003\u0004\u0002\u0000"+
		"01\u0005\u0019\u0000\u000012\u0005&\u0000\u000023\u0003\u0006\u0003\u0000"+
		"34\u0005-\u0000\u00004:\u0001\u0000\u0000\u000056\u0003\u0004\u0002\u0000"+
		"67\u0005\u0019\u0000\u000078\u0005-\u0000\u00008:\u0001\u0000\u0000\u0000"+
		"9/\u0001\u0000\u0000\u000095\u0001\u0000\u0000\u0000:\u0003\u0001\u0000"+
		"\u0000\u0000;<\u0007\u0000\u0000\u0000<\u0005\u0001\u0000\u0000\u0000"+
		"=>\u0006\u0003\uffff\uffff\u0000>D\u0005\u0019\u0000\u0000?@\u0005\u0019"+
		"\u0000\u0000@A\u0005\u001a\u0000\u0000AD\u0005\u0019\u0000\u0000BD\u0003"+
		"\b\u0004\u0000C=\u0001\u0000\u0000\u0000C?\u0001\u0000\u0000\u0000CB\u0001"+
		"\u0000\u0000\u0000DP\u0001\u0000\u0000\u0000EF\n\u0006\u0000\u0000FG\u0007"+
		"\u0001\u0000\u0000GO\u0003\u0006\u0003\u0007HI\n\u0005\u0000\u0000IJ\u0007"+
		"\u0002\u0000\u0000JO\u0003\u0006\u0003\u0006KL\n\u0004\u0000\u0000LM\u0007"+
		"\u0003\u0000\u0000MO\u0003\u0006\u0003\u0005NE\u0001\u0000\u0000\u0000"+
		"NH\u0001\u0000\u0000\u0000NK\u0001\u0000\u0000\u0000OR\u0001\u0000\u0000"+
		"\u0000PN\u0001\u0000\u0000\u0000PQ\u0001\u0000\u0000\u0000Q\u0007\u0001"+
		"\u0000\u0000\u0000RP\u0001\u0000\u0000\u0000ST\u0007\u0004\u0000\u0000"+
		"T\t\u0001\u0000\u0000\u0000U[\u0003\u0002\u0001\u0000V[\u0003\f\u0006"+
		"\u0000W[\u0003\u001a\r\u0000X[\u0003\u000e\u0007\u0000Y[\u0003\u0012\t"+
		"\u0000ZU\u0001\u0000\u0000\u0000ZV\u0001\u0000\u0000\u0000ZW\u0001\u0000"+
		"\u0000\u0000ZX\u0001\u0000\u0000\u0000ZY\u0001\u0000\u0000\u0000[\u000b"+
		"\u0001\u0000\u0000\u0000\\]\u0005\u0019\u0000\u0000]^\u0005&\u0000\u0000"+
		"^_\u0003\u0006\u0003\u0000_`\u0005-\u0000\u0000`\r\u0001\u0000\u0000\u0000"+
		"af\u0005\r\u0000\u0000bc\u00051\u0000\u0000cd\u0003\u0006\u0003\u0000"+
		"de\u00052\u0000\u0000eg\u0001\u0000\u0000\u0000fb\u0001\u0000\u0000\u0000"+
		"fg\u0001\u0000\u0000\u0000gh\u0001\u0000\u0000\u0000hl\u0005/\u0000\u0000"+
		"ik\u0003\u0010\b\u0000ji\u0001\u0000\u0000\u0000kn\u0001\u0000\u0000\u0000"+
		"lj\u0001\u0000\u0000\u0000lm\u0001\u0000\u0000\u0000mo\u0001\u0000\u0000"+
		"\u0000nl\u0001\u0000\u0000\u0000op\u00050\u0000\u0000p\u000f\u0001\u0000"+
		"\u0000\u0000qr\u0005\u000e\u0000\u0000rs\u0003\u0006\u0003\u0000st\u0005"+
		"&\u0000\u0000tu\u0005\u000f\u0000\u0000uv\u0003\u0006\u0003\u0000vw\u0005"+
		"-\u0000\u0000w\u0080\u0001\u0000\u0000\u0000xy\u0005\u000e\u0000\u0000"+
		"yz\u00054\u0000\u0000z{\u0005&\u0000\u0000{|\u0005\u000f\u0000\u0000|"+
		"}\u0003\u0012\t\u0000}~\u0005-\u0000\u0000~\u0080\u0001\u0000\u0000\u0000"+
		"\u007fq\u0001\u0000\u0000\u0000\u007fx\u0001\u0000\u0000\u0000\u0080\u0011"+
		"\u0001\u0000\u0000\u0000\u0081\u0082\u0005\u0010\u0000\u0000\u0082\u0083"+
		"\u0005-\u0000\u0000\u0083\u0013\u0001\u0000\u0000\u0000\u0084\u0085\u0005"+
		"\u0012\u0000\u0000\u0085\u0086\u0005\u0019\u0000\u0000\u0086\u0087\u0005"+
		"1\u0000\u0000\u0087\u0088\u0003\u0016\u000b\u0000\u0088\u0089\u00052\u0000"+
		"\u0000\u0089\u008a\u0005.\u0000\u0000\u008a\u008b\u0003\u0004\u0002\u0000"+
		"\u008b\u008c\u0003\"\u0011\u0000\u008c\u0015\u0001\u0000\u0000\u0000\u008d"+
		"\u0092\u0003\u0018\f\u0000\u008e\u008f\u00053\u0000\u0000\u008f\u0091"+
		"\u0003\u0018\f\u0000\u0090\u008e\u0001\u0000\u0000\u0000\u0091\u0094\u0001"+
		"\u0000\u0000\u0000\u0092\u0090\u0001\u0000\u0000\u0000\u0092\u0093\u0001"+
		"\u0000\u0000\u0000\u0093\u0096\u0001\u0000\u0000\u0000\u0094\u0092\u0001"+
		"\u0000\u0000\u0000\u0095\u008d\u0001\u0000\u0000\u0000\u0095\u0096\u0001"+
		"\u0000\u0000\u0000\u0096\u0017\u0001\u0000\u0000\u0000\u0097\u0098\u0003"+
		"\u0004\u0002\u0000\u0098\u0099\u0005\u0019\u0000\u0000\u0099\u0019\u0001"+
		"\u0000\u0000\u0000\u009a\u009b\u0005\u0019\u0000\u0000\u009b\u009c\u0005"+
		"1\u0000\u0000\u009c\u009d\u0003\u001c\u000e\u0000\u009d\u009e\u00052\u0000"+
		"\u0000\u009e\u009f\u0005-\u0000\u0000\u009f\u001b\u0001\u0000\u0000\u0000"+
		"\u00a0\u00a5\u0003\u0006\u0003\u0000\u00a1\u00a2\u00053\u0000\u0000\u00a2"+
		"\u00a4\u0003\u0006\u0003\u0000\u00a3\u00a1\u0001\u0000\u0000\u0000\u00a4"+
		"\u00a7\u0001\u0000\u0000\u0000\u00a5\u00a3\u0001\u0000\u0000\u0000\u00a5"+
		"\u00a6\u0001\u0000\u0000\u0000\u00a6\u00a9\u0001\u0000\u0000\u0000\u00a7"+
		"\u00a5\u0001\u0000\u0000\u0000\u00a8\u00a0\u0001\u0000\u0000\u0000\u00a8"+
		"\u00a9\u0001\u0000\u0000\u0000\u00a9\u001d\u0001\u0000\u0000\u0000\u00aa"+
		"\u00ab\u0005\u0011\u0000\u0000\u00ab\u00ac\u0005\u0019\u0000\u0000\u00ac"+
		"\u00b0\u0005/\u0000\u0000\u00ad\u00af\u0003 \u0010\u0000\u00ae\u00ad\u0001"+
		"\u0000\u0000\u0000\u00af\u00b2\u0001\u0000\u0000\u0000\u00b0\u00ae\u0001"+
		"\u0000\u0000\u0000\u00b0\u00b1\u0001\u0000\u0000\u0000\u00b1\u00b3\u0001"+
		"\u0000\u0000\u0000\u00b2\u00b0\u0001\u0000\u0000\u0000\u00b3\u00b4\u0005"+
		"0\u0000\u0000\u00b4\u001f\u0001\u0000\u0000\u0000\u00b5\u00b6\u0003\u0004"+
		"\u0002\u0000\u00b6\u00b7\u0005\u0019\u0000\u0000\u00b7\u00b8\u0007\u0005"+
		"\u0000\u0000\u00b8!\u0001\u0000\u0000\u0000\u00b9\u00bd\u0005/\u0000\u0000"+
		"\u00ba\u00bc\u0003\n\u0005\u0000\u00bb\u00ba\u0001\u0000\u0000\u0000\u00bc"+
		"\u00bf\u0001\u0000\u0000\u0000\u00bd\u00bb\u0001\u0000\u0000\u0000\u00bd"+
		"\u00be\u0001\u0000\u0000\u0000\u00be\u00c0\u0001\u0000\u0000\u0000\u00bf"+
		"\u00bd\u0001\u0000\u0000\u0000\u00c0\u00c1\u00050\u0000\u0000\u00c1#\u0001"+
		"\u0000\u0000\u0000\u0010(*9CNPZfl\u007f\u0092\u0095\u00a5\u00a8\u00b0"+
		"\u00bd";
	public static final ATN _ATN =
		new ATNDeserializer().deserialize(_serializedATN.toCharArray());
	static {
		_decisionToDFA = new DFA[_ATN.getNumberOfDecisions()];
		for (int i = 0; i < _ATN.getNumberOfDecisions(); i++) {
			_decisionToDFA[i] = new DFA(_ATN.getDecisionState(i), i);
		}
	}
}