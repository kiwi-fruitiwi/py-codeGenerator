# project 11 compilationEngine: convert to use symbolTables. output to XML
#
# 	compilationEngine needs fields: class+srt level symbolTables
# 	reset when appropriate (never for class since each file is a class)
# 	search through compilationEngine for 'identifier'
# 		see where compileIdentifier is called
# 			verify with Jack grammar sheet
# 		classVarDec: (static|field) type varName (,varName)*;
# 		varDec: var type varName (,varName)*;
#
# 		discern between className and srtName →
# 		class: class className
# 		srtCall: not varName.srtName(exprList)
# 			srtName(exprList) | (className|varName).srtName(exprList)
# 		srtDec: (constructor|function|method) (void|type) srtName(pList) sBody
# 		type: int | char | boolean | className
# 	use typeOf, kindOf, indexOf to determine:
# 		what to add to symbolTable on each identifier
# 	goal → output per identifier
# 		identifier category: var arg static field, class srt
# 		running index for var arg static field
#
#	☒ create compilationEngine constructor symbolTables
#	☐ at end of compileSubroutine, we want subroutine name
#		followed by printout of class- and srt-level tables
#	☐ at end of class compilation: display class-level symbol table
#
#	☒ compileIdentifier split into three methods
#		☒ compileClassName
#			writes <class name> inside of <identifier> XML tag
#		☒ compileSubroutineName
#			writes <subroutine name> inside of <identifier> XML tag
#		☒ compileVariable(varType, varKind)
#			invokes self.symbolTables.define(name, type, kind)
#			name is next token
#	☐ call all three methods appropriate to replace every compileIdentifier call
#	☐ compileType needs additional argument: variable kind → SFVA
#		used in: (static field variable/local argument)
#			classVarDec ← static, field
#				VarKind.STATIC/FIELD
#			varDec ← local/var
#				VarKind.VAR
#			subRoutineDec ← argument via parameterList, but not before srtName
#				VarKind.ARGUMENT
#		example: var Point p1; ← compiler just updates the symbolTable with:
#			this would be a varDec case: var type varName (, varName)*;
#				symbolTable.define(name, type, kind) call a result of cpVarDeck
#					name: varName
#					type: type
#					kind: VarKind.VAR
#			symbolTable.define(p1, Point, VarKind.VAR)
#		example: static Point p1 ← cpClassVarDec uses VarKind.STATIC
#		example: field Point p1 ← cpClassVarDec uses VarKind.FIELD
#
#
#	☐ symbol table output requirements
#		identifier's name ← already done in p10
#		identifier's category ← var, arg, static, field, class, subroutine
#		if category in [var, arg, static, field], running index
#		identifier defined or used ❔
#
# part 2: generating actual code instead of XML


from tokenizer import JackTokenizer, TokenType
from symbolTable import SymbolTable, VarKind, Entry


def convertSymbolToHtml(value):
	match value:
		case '<':
			result = '&lt;'
		case '>':
			result = '&gt;'
		case '&':
			result = '&amp;'
		case _:
			result = value
	return result


class CompilationEngine:
	"""
	The compilationEngine generates the compiler's output
	"""

	# creates a new compilation engine with the given input and output
	# the next routine called must be compileClass
	def __init__(self, inputJackUri, outputXmlUri):
		# create a Tokenizer object from the inputURI
		self.tk = JackTokenizer(inputJackUri)

		# open file for writing with URI=outputXML
		self.out = open(outputXmlUri, 'w')

		# indentation level of XML. after each tag, indent contents, then revert
		self.indentLevel = 0

		# sometimes compileTerm will need to do an additional advance for LL2.
		# this flag tells us to skip the next advance() if that's the case.
		# foo, foo[expr], foo.bar(exprList), bar(exprList)
		# unsure about difference between Foo.bar(exprList) vs foo.bar(exprList)

		# if true, the next eat() doesn't advance
		self.skipNextAdvance = False

		# ops in the Jack Grammar
		self.opsList = ['+', '-', '*', '/', '&', '|', '<', '>', '=']

		# initialize symbolTable, which creates empty class+srtTables
		# compileClass will overwrite this instantiation but this is useful for
		# testing methods
		self.symbolTables = SymbolTable()


	def indent(self):
		self.indentLevel += 1

	def outdent(self):
		self.indentLevel -= 1

	def write(self, s):
		self.out.write(self.indentLevel * '  ' + s)

	# calls compile on whatever needs testing at the moment
	def testCompile(self):
		# self.compileClassVarDec()
		# self.compileSubroutineBody()
		# self.compileVarDec()
		# self.compileSubroutineDec()
		# self.compileReturn()
		# self.compileStatements()
		self.compileClass()
		# self.compileDo()
		# self.compileExpression()
		pass

	# compiles a complete class. called after the constructor
	def compileClass(self):
		"""
		expected output example:
			<class>
			  <keyword> class </keyword>
			  <identifier> Main </identifier>
			  <symbol> { </symbol>
			  <subroutineDec>
				<keyword> function </keyword>
				<keyword> void </keyword>
				<identifier> main </identifier>
				<symbol> ( </symbol>
				<parameterList>
				</parameterList>
				<symbol> ) </symbol>
				<subroutineBody>
				...

		follows pattern: class className '{' classVarDec* subroutineDec* '}'
		"""
		self.symbolTables = SymbolTable()

		self.write('<class>\n')
		self.indent()
		self.eat('class')  # this will output <keyword> class </keyword>

		# className is an identifier
		self.compileClassName()
		self.eat('{')

		while self.compileClassVarDec():
			continue  # probably unnecessary continue; empty body

		while self.compileSubroutineDec():
			continue

		self.eat('}')
		self.outdent()
		self.write('</class>\n')

		# TODO DEBUG PRINT class-level symbol table
		print(f'{self.symbolTables}')

	# compiles a static variable or field declaration
	def compileClassVarDec(self):
		"""
		<classVarDec>
		  <keyword> field </keyword>
		  <keyword> int </keyword>
		  <identifier> size </identifier>
		  <symbol> ; </symbol>
		</classVarDec>

		used by compileClass, following this pattern:
		(static | field) type varName (',' varName)* ';'
		type → int | char | boolean | className
		"""
		# static or field?
		self.peek()

		if self.tk.getTokenType() != TokenType.KEYWORD:
			return False

		if self.tk.keyWord() not in ['static', 'field']:
			return False

		self.write('<classVarDec>\n')
		self.indent()

		self.advance()
		self.write(f'<keyword> {self.tk.keyWord()} </keyword>\n')
		self.__compileType()

		# varName(',' varName)*
		self.__compileVarNameList()
		self.outdent()
		self.write('</classVarDec>\n')

		return True

	# helper method for classVarDec, subroutineDec, parameterList, varDec
	# pattern: int | char | boolean | className
	def __compileType(self):
		# type → advance, if TokenType is keyword: int char or boolean
		self.advance()

		match self.tk.getTokenType():
			case TokenType.KEYWORD:
				# process int, char, boolean
				assert self.tk.keyWord() in ['int', 'char', 'boolean'], f'{self.tk.keyWord()}'
				self.write(f'<keyword> {self.tk.keyWord()} </keyword>\n')
			case TokenType.IDENTIFIER:
				# process className

				self.skipNextAdvance = True
				self.compileClassName()

			case _:
				raise ValueError(
					f'did not find identifier or keyword token: {self.tk.getTokenType()}')

	# compiles a complete method, function, or constructor
	def compileSubroutineDec(self):
		"""
		:return: True if we found a subroutineDec, False if not.
			this is so we can use while self.compileSubroutineDec
		"""
		# skipNextAdvOnEat because we might fail to find a subroutineDec
		self.peek()

		# if compileSubroutineDec is being called, it must start with:
		# 'constructor', 'function', or 'method'
		# so if it doesn't, we can return False
		if self.tk.getTokenType() != TokenType.KEYWORD:
			print(f'compileSrtDec → {self.tk.getTokenType()}')
			return False
		else:
			keywordValue = self.tk.keyWord()
			if keywordValue not in ['constructor', 'function', 'method']:
				return False
			else:
				# starts with the right keyword for subroutineDec!
				self.__subroutineDecHelper()
				return True

	# helper method that compiles subroutineDec with the help of detector logic
	def __subroutineDecHelper(self):
		"""
		  <subroutineDec>
			<keyword> method </keyword>
			<keyword> void </keyword>
			<identifier> dispose </identifier>
			<symbol> ( </symbol>
			<parameterList>
			</parameterList>
			<symbol> ) </symbol>
			<subroutineBody>
			  <symbol> { </symbol>
			  <statements>
			  	...
			  </statements>
			  <symbol> } </symbol>
			</subroutineBody>
		  </subroutineDec>

		pattern: ('constructor'|'function'|'method') ('void'|type)
			subroutineName '('parameterList')' subroutineBody
		"""
		self.write('<subroutineDec>\n')
		self.indent()

		# remember we've already advanced when calling __subroutineDecHelper
		# the skipOnNextEat flag is set to True
		# we've already checked for keywordValue not in:
		# 	['constructor', 'function', 'method']

		# ('constructor'|'function'|'method')
		self.advance()
		keywordValue = self.tk.keyWord()
		self.write(f'<keyword> {keywordValue} </keyword>\n')

		# ('void'|type)
		self.peek()

		if self.tk.getTokenType() == TokenType.KEYWORD:
			self.eat('void')
		else:
			self.__compileType()

		# subroutineName
		self.compileIdentifier()  # TODO subroutine name

		# '(' parameterList ')'
		self.eat('(')
		self.compileParameterList()
		self.eat(')')

		# subroutineBody
		self.compileSubroutineBody()
		self.outdent()
		self.write('</subroutineDec>\n')

	# compiles a (possibly empty) parameter list. does not handle enclosing '()'
	def compileParameterList(self):
		"""
		<parameterList>
		  <keyword> int </keyword>
		  <identifier> Ax </identifier>
		  <symbol> , </symbol>
		  <keyword> int </keyword>
		  <identifier> Ay </identifier>
		  <symbol> , </symbol>
		  <keyword> int </keyword>
		  <identifier> Asize </identifier>
		</parameterList>

		follows pattern:
			((type varName) (, type varName)*)?
			note that the entire pattern could be empty
				the character after parameterList ends is always ')'
		"""
		self.write('<parameterList>\n')
		self.indent()
		self.peek()

		# if next symbol is ')', end the parameterList
		if self.tk.getTokenType() == TokenType.SYMBOL:
			self.outdent()
			self.write('</parameterList>\n')
			return

		# otherwise the next symbol MUST be a type: int char bool className
		# consume: type varName
		self.__compileType()  # type
		self.compileIdentifier()  # varName TODO symbolTable: argument

		# then while next token is ',', consume type varName
		self.peek()

		# pattern: (, type varName)*
		# next token must be either ',' or ';'
		assert self.tk.getTokenType() == TokenType.SYMBOL
		while self.tk.symbol() == ',':
			self.eat(',')
			self.__compileType()
			self.compileIdentifier()  # TODO symbolTable: argument
			self.peek()  # check next symbol: ',' or ';'

		self.outdent()
		self.write('</parameterList>\n')

	# compiles a subroutine's body
	# pattern: '{' varDec* statements'}'
	def compileSubroutineBody(self):
		"""
		<subroutineBody>
		  <symbol> { </symbol>
		  <statements>

			<letStatement>
			  <keyword> let </keyword>
			  <identifier> x </identifier>
			  <symbol> = </symbol>
			  <expression>
				<term>
				  <identifier> Ax </identifier>
				</term>
			  </expression>
			  <symbol> ; </symbol>
			</letStatement>

			<returnStatement>
			  <keyword> return </keyword>
			  <expression>
				<term>
				  <identifier> x </identifier>
				</term>
			  </expression>
			  <symbol> ; </symbol>
			</returnStatement>

		  </statements>
		  <symbol> } </symbol>
		</subroutineBody>

		🏭 our aim is to match the pattern: '{' varDec* statements'}'
		"""
		self.write('<subroutineBody>\n')
		self.indent()
		self.eat('{')

		# varDec* vs statements
		self.peek()

		# varDec always starts with 'var'
		while self.tk.getTokenType() == TokenType.KEYWORD and self.tk.keyWord() == 'var':
			self.compileVarDec()
			self.peek()

		# statements always starts with keyword in [let, if, while, do, return]
		self.compileStatements()
		self.eat('}')
		self.outdent()
		self.write('</subroutineBody>\n')

	# compiles a var declaration
	def compileVarDec(self):
		"""
	    <varDec>
	    	<keyword> var </keyword>
	    	<identifier> Array </identifier>
	    	<identifier> a </identifier>
	    	<symbol> ; </symbol>
	    </varDec>
	    <varDec>
	    	<keyword> var </keyword>
	    	<keyword> int </keyword>
	    	<identifier> length </identifier>
	    	<symbol> ; </symbol>
	    </varDec>
	    <varDec>
	    	<keyword> var </keyword>
	    	<keyword> int </keyword>
	    	<identifier> i </identifier>
	    	<symbol> , </symbol>
	    	<identifier> sum </identifier>
	    	<symbol> ; </symbol>
	    </varDec>

	    pattern: var type varName (',' varName)*';'
		"""
		self.write('<varDec>\n')
		self.indent()

		# var type varName
		self.eat('var')
		self.__compileType()

		# varName (',' varName)*';'
		self.__compileVarNameList()
		self.outdent()
		self.write('</varDec>\n')

	# compiles a sequence of statements. does not handle enclosing '{}'
	# a statement is one of 5 options: let, if, while, do, return
	# statements is statement*, meaning it can be nothing
	def compileStatements(self):
		"""
		<statements>
            <letStatement>
              <keyword> let </keyword>
              <identifier> a </identifier>
              <symbol> [ </symbol>
              <expression>
                <term>
                  <identifier> i </identifier>
                </term>
              </expression>
              <symbol> ] </symbol>
              <symbol> = </symbol>
              <expression>
                <term>
                  <identifier> Keyboard </identifier>
                  <symbol> . </symbol>
                  <identifier> readInt </identifier>
                  <symbol> ( </symbol>
                  <expressionList>
                    <expression>
                      <term>
                        <stringConstant> ENTER THE NEXT NUMBER:  </stringConstant>
                      </term>
                    </expression>
                  </expressionList>
                  <symbol> ) </symbol>
                </term>
              </expression>
              <symbol> ; </symbol>
            </letStatement>
            <letStatement>
              <keyword> let </keyword>
              <identifier> i </identifier>
              <symbol> = </symbol>
              <expression>
                <term>
                  <identifier> i </identifier>
                </term>
                <symbol> + </symbol>
                <term>
                  <integerConstant> 1 </integerConstant>
                </term>
              </expression>
              <symbol> ; </symbol>
            </letStatement>
          </statements>
		:return:

		statements is found in if, while, and subroutineBody
			if (expression) {statements} else {statements}
			while (expression) {statements}
			{varDec* statements}

		note that statements always ends in '}'!
		"""
		self.write('<statements>\n')
		self.indent()

		# we want to try to compile {let, if, while, do, return} statements
		# until we run out of those keywords
		# ✒note! currently statements always ends with '}'
		while self.__compileStatement():
			# empty because we want to stop when it returns false
			continue  # probably not necessary

		self.outdent()
		self.write('</statements>\n')

	# helper method for compileStatements, returning false if
	# {let, if, while, do, return} are not found
	def __compileStatement(self):
		"""

		:return: true if a statement was found, false if not
		"""
		self.peek()

		# if compileStatement is being called, tokenType must be one of
		# {let, if, while, do, return}
		if self.tk.getTokenType() != TokenType.KEYWORD:
			return False
		else:
			match self.tk.keyWord():
				case 'let':
					self.compileLet()
					return True
				case 'if':
					self.compileIf()
					return True
				case 'while':
					self.compileWhile()
					return True
				case 'do':
					self.compileDo()
					return True
				case 'return':
					self.compileReturn()
					return True
				case _:
					raise ValueError(
						f'did not find let, if, while, do, or return → {self.tk.keyWord()}')

	# helper method for compileClassVarDec, compileVarDec
	# classVarDec pattern: (static | field) type varName (, varName)* ';'
	# varDec: var type varName (, varName)* ';'
	#
	# the pattern we are targeting is:
	# 	varName (',' varName)*;
	# the goal is to implement this repeated handling code once here
	def __compileVarNameList(self):  # TODO needs class or srt flag
		# varName
		self.compileIdentifier()  # TODO if class: FIELD; if srt: VAR/LOCAL
		self.peek()  # check ahead to see: ',' or ';' ?

		# (',' varName)*
		while self.tk.symbol() == ',':
			self.eat(',')
			self.compileIdentifier()  # TODO same as above
			self.peek()

		# the only token we have left is ';'
		self.eat(';')

	# eats token = identifier, checks type
	def compileIdentifier(self):  # TODO needs type, kind parameters
		# we actually don't eat because we're not sure what identifier it is
		# instead, we advance and assert tokenType
		self.advance()

		# print(f'{self.tk.getTokenType()}')
		assert self.tk.getTokenType() == TokenType.IDENTIFIER, f'{self.tk.getTokenType()}'

		# then write <identifier> value </identifier>
		self.write(f'<identifier> {self.tk.identifier()} </identifier>\n')

	# sub-method of compileIdentifier
	def compileClassName(self):
		self.advance()
		assert self.tk.getTokenType() == TokenType.IDENTIFIER, f'{self.tk.getTokenType()}'

		# skip writing <id> tag with indented <className> tag
		# code generator will clobber writing XML for code instead
		self.write(f'<className> {self.tk.identifier()} </className>\n')

	# sub-method of compileIdentifier
	def compileSubroutineName(self):
		self.advance()
		assert self.tk.getTokenType() == TokenType.IDENTIFIER, f'{self.tk.getTokenType()}'
		self.write(f'<subroutineName> {self.tk.identifier()} </subroutineName>\n')

	# sub-method of compileIdentifier: covers static field arg var
	def compileVariable(self, vType: str, vKind: VarKind):
		self.advance()
		assert self.tk.getTokenType() == TokenType.IDENTIFIER, f'{self.tk.getTokenType()}'
		tag: str = 'unset'

		match vKind:
			case VarKind.STATIC:
				tag = 'staticVariable'
			case VarKind.FIELD:
				tag = 'fieldVariable'
			case VarKind.ARG:
				tag = 'argumentVariable'
			case VarKind.VAR:
				tag = 'localVariable'

		self.symbolTables.define(self.tk.identifier(), vType, vKind)
		self.write(f'<{tag}> {self.tk.identifier()} </{tag}>')

	def compileLet(self):
		"""
		letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
		:return:
		"""
		self.write('<letStatement>\n')
		self.indent()

		# 'let'
		self.eat('let')

		# className, varName, subRName all identifiers ← 'program structure'
		self.compileIdentifier()  # TODO symbolTable → must be VarKind.VAR

		# check next token for two options: '[' or '='
		self.peek()

		# assert it's a symbol
		assert self.tk.getTokenType() == TokenType.SYMBOL
		assert self.tk.symbol() == '[' or self.tk.symbol() == '='

		# if next token is '[', eat('['), compileExpr, eat(']')
		if self.tk.symbol() == '[':
			self.eat('[')
			self.compileExpression()
			self.eat(']')
			self.peek()  # reach the '='

		# we are guaranteed the next symbol is '='
		# eat it, compileExpr, eat(';')
		assert self.tk.symbol() == '='

		self.eat('=')

		# TODO # for expressionLess, use term: id, strC, intC
		# TODO can also be true, false, null, this ← keywords!
		# actually these are both taken care of in compileExpr,Term
		self.compileExpression()
		self.eat(';')

		self.outdent()
		self.write('</letStatement>\n')

	# compiles an if statement, possibly with a trailing else clause
	# if '(' expression ')' '{' statements '}' (else '{' statements '}')?
	def compileIf(self):
		"""
		<ifStatement>
          <keyword> if </keyword>
          <symbol> ( </symbol>
          <expression>
            <term>
              <identifier> b </identifier>
            </term>
          </expression>
          <symbol> ) </symbol>
          <symbol> { </symbol>
          <statements>
          </statements>
          <symbol> } </symbol>
          <keyword> else </keyword>
          <symbol> { </symbol>
          <statements>
          </statements>
          <symbol> } </symbol>
        </ifStatement>
		:return:
		"""
		self.write('<ifStatement>\n')
		self.indent()

		# if '(' expression ')'
		self.eat('if')
		self.__compileExprWithinParens()

		# '{' statements '}'
		self.__compileStatementsWithinBrackets()

		# (else '{' statements '}')?
		self.advance()  # check for else token
		if self.tk.getTokenType() == TokenType.KEYWORD:
			if self.tk.keyWord() == 'else':
				self.write('<keyword> else </keyword>\n')
				self.__compileStatementsWithinBrackets()
			else:  # we've already advanced once to check the else keyword
				self.skipNextAdvance = True

		self.write('</ifStatement>\n')
		self.outdent()

	def __compileExprWithinParens(self):
		self.eat('(')
		self.compileExpression()
		self.eat(')')

	def __compileStatementsWithinBrackets(self):
		self.eat('{')
		self.compileStatements()
		self.eat('}')

	# 'while' '(' expression ')' '{' statements '}'
	def compileWhile(self):

		# 'while'
		self.write('<whileStatement>\n')
		self.indent()
		self.eat('while')

		# '(' expression ')'
		self.__compileExprWithinParens()

		# '{' statements '}'
		self.__compileStatementsWithinBrackets()

		self.outdent()
		self.write('</whileStatement>\n')

	# 'do' subroutineCall ';'
	def compileDo(self):
		"""
		<doStatement>
          <keyword> do </keyword>
          <identifier> Memory </identifier>
          <symbol> . </symbol>
          <identifier> deAlloc </identifier>
          <symbol> ( </symbol>
          <expressionList>
            <expression>
              <term>
                <keyword> this </keyword>
              </term>
            </expression>
          </expressionList>
          <symbol> ) </symbol>
          <symbol> ; </symbol>
        </doStatement>
		:return:
		"""
		self.write('<doStatement>\n')
		self.indent()
		self.eat('do')

		self.__compileSubroutineCallHelper()

		# ';'
		self.eat(';')
		self.outdent()
		self.write('</doStatement>\n')

	def __compileSubroutineCallHelper(self):
		# subroutineName '(' expressionList ')' |
		# (className | varName) '.' subroutineName '(' expressionList ')'
		#
		# two possibilities:
		# 	identifier (className | varName) → '.' e.g. obj.render(x, y)
		# 	identifier (subroutineName) → '(' e.g. render(x, y)
		self.advance()
		self.write(f'<identifier> {self.tk.identifier()} </identifier>\n')

		self.peek()

		# handling the ',render' subroutineName after '.'
		if self.tk.symbol() == '.':
			self.eat('.')
			# advance and grab the subroutineName
			self.advance()
			self.write(f'<identifier> {self.tk.identifier()} </identifier>\n')

		# then eat('(') → compileExpressionList
		self.eat('(')
		self.compileExpressionList()
		self.eat(')')

	# 'return' expression? ';'
	def compileReturn(self):
		"""
		<returnStatement>
          <keyword> return </keyword>
          <expression>
            <term>
              <identifier> x </identifier>
            </term>
          </expression>
          <symbol> ; </symbol>
        </returnStatement>

		'return' expression? ';'
		:return:
		"""
		# 'return'
		self.write('<returnStatement>\n')
		self.indent()
		self.eat('return')

		# expression? ';'
		# the next token is either a ';' or an expression
		# expressions are more difficult to check for so, check for symbol ';'
		# if it's a ';' we're done! although unary ops can start terms
		self.peek()

		if self.tk.getTokenType() == TokenType.SYMBOL:
			if self.tk.symbol() == ';':
				self.eat(';')
				self.outdent()
				self.write('</returnStatement>\n')
				return
		else:
			# there's an expression in → expression? ';'
			self.compileExpression()
			self.eat(';')
			self.outdent()
			self.write('</returnStatement>\n')

	# the expressionless tests for project 10 use simplified 'term' tokens
	# that can only be single identifiers or the keyword 'this'.
	def compileSimpleTerm(self):
		# the simple version of this rule is identifier | 'this' ←🦔

		self.write('<term>\n')
		self.indent()
		self.advance()
		value = None

		match self.tk.getTokenType():
			case TokenType.IDENTIFIER:
				value = self.tk.identifier()
				self.write(f'<identifier> {value} </identifier>\n')
			case TokenType.KEYWORD:
				assert self.tk.keyWord() in ['this', 'false', 'true', 'null']
				value = self.tk.keyWord()
				self.write(f'<keyword> {value} </keyword>\n')

			# adding extra cases: integer and string constant
			case TokenType.INT_CONST:
				value = self.tk.intVal()
				self.write(f'<integerConstant> {value} </integerConstant>\n')
			case TokenType.STRING_CONST:
				value = self.tk.stringVal()
				self.write(f'<stringConstant> {value} </stringConstant>\n')

			# TODO technically we do unaryOp term here
			case TokenType.SYMBOL:
				value = convertSymbolToHtml(self.tk.symbol())
				self.write(f'<symbol> {value} </symbol>\n')
			case _:
				raise ValueError(
					f'simple term was not an identifier or keywordConstant: {self.tk.getTokenType()}→{value}')

		self.outdent()
		self.write('</term>\n')

	# compiles a term. if the current token is an identifier, the routine must
	# distinguish between a variable, an array entry, or a subroutine call. a
	# single look-ahead token, which may be one of [, (, or ., suffices to
	# distinguish between the possibilities. any other token is not part of this
	# term and should not be advanced over.
	def compileTerm(self):
		"""
		pattern: intConst | strConst | keywordConst | varName |
			varName'['expression']' | subroutineCall | '('expression')' |
			unaryOp term

		unaryOp is ['-', '~']
		"""
		# 🏭 integerConst stringConst keywordConst identifier unaryOp→term
		# remember that keywordConstants are false, true, null, this
		self.write('<term>\n')
		self.indent()
		self.peek()

		match self.tk.getTokenType():
			case TokenType.IDENTIFIER:
				self.advance()
				value = self.tk.identifier()
				self.write(f'<identifier> {value} </identifier>\n')

				# we need to advance one more time to check 4 LL2 cases
				#   foo ← varName
				#	foo'['expression']' ← varName'['expression']'
				#	subroutineCall if next token is '.' or '('
				#		foo.bar'('expressionList')'
				#		bar'('expressionList')'
				self.peek()

				tokenType = self.tk.getTokenType()
				if tokenType == TokenType.SYMBOL:
					advTokenValue = self.tk.symbol()
					match advTokenValue:
						case ';' | ')':
							# we're at the end of the line!
							pass
						case '.':
							# matches pattern (className | varName).srtName(exprList) in subroutineCall
							# let key = Keyboard.keyPressed();
							#
							# <expression>
							#   <term>
							#     <identifier> Keyboard </identifier>
							#     <symbol> . </symbol>
							#     <identifier> keyPressed </identifier>
							#     <symbol> ( </symbol>
							#     <expressionList>
							#     </expressionList>
							#     <symbol> ) </symbol>
							#   </term>
							# </expression>
							self.eat('.')

							# TODO is varName if already in symbolTable
							#  but className if not
							self.compileIdentifier()
							self.eat('(')
							self.compileExpressionList()
							self.eat(')')

						case '(':
							# this matches subroutineName(expressionList)
							self.eat('(')
							self.compileExpressionList()
							self.eat(')')

						case '[':
							# TODO process varName[expression]
							self.eat('[')
							self.compileExpression()
							self.eat(']')

						# these are all ops!
						case '+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=':
							pass

						# this is the next token for expressionList
						case ',':
							pass

						# closing array bracket for our simple term
						case ']':
							pass

						case _:
							raise ValueError(f'invalid symbol in term LL2: {advTokenValue}')

			case TokenType.SYMBOL:
				value = self.tk.symbol()
				match value:
					# '(' expression ')'
					case '(':
						self.eat('(')
						self.compileExpression()
						self.eat(')')

					# unaryOp term: write op, recursively compileTerm
					#   <expression>
					#     <term>
					#       <symbol> ~ </symbol>
					#       <term>
					#         <identifier> exit </identifier>
					#       </term>
					#     </term>
					#   </expression>
					case '-':
						self.eat('-')
						self.compileTerm()
					case '~':
						self.eat('~')
						self.compileTerm()
					case _:
						raise ValueError(f'invalid symbol in term LL2: {value}')

			case TokenType.KEYWORD:
				self.advance()
				value = self.tk.keyWord()
				assert value in ['true', 'false', 'null', 'this'], value
				self.write(f'<keyword> {value} </keyword>\n')

			case TokenType.INT_CONST:
				self.advance()
				value = self.tk.intVal()
				self.write(f'<integerConstant> {value} </integerConstant>\n')

			case TokenType.STRING_CONST:
				self.advance()
				value = self.tk.stringVal()
				self.write(f'<stringConstant> {value} </stringConstant>\n')

			case _:
				raise TypeError(f'invalid TokenType: {self.tk.getTokenType()}')

		self.outdent()
		self.write('</term>\n')

	# not used in the first pass
	def compileExpression(self):
		"""
		  <expression>
			<term>
			  <identifier> i </identifier>
			</term>
			<symbol> * </symbol>
			<term>
			  <symbol> ( </symbol>
			  <expression>
				<term>
				  <symbol> - </symbol>
				  <term>
					<identifier> j </identifier>
				  </term>
				</term>
			  </expression>
			  <symbol> ) </symbol>
			</term>
		  </expression>

		→ i * (-j)
		pattern: term (op term)*
		"""
		self.write('<expression>\n')
		self.indent()
		self.indentLevel += 1

		# temporarily call compileTerm for expressionLessSquare testing
		# when we're ready to test expressions, then we can test Square
		self.compileTerm()

		# look ahead to determine if the next token is an op
		# op symbols are: + - * / & | < > =
		self.peek()

		# while next symbol is an op: compile the term that follows and check
		# for another op!
		while self.tk.getTokenType() == TokenType.SYMBOL and \
			self.tk.symbol() in self.opsList:

			# eat it
			self.advance()
			self.write(f'<symbol> {convertSymbolToHtml(self.tk.symbol())} </symbol>\n')

			# compile the next term in pattern: op term
			self.compileTerm()

			# peek at next token to see if it's another op so we can continue
			self.peek()

		# if the next term isn't a symbol in opsList, the expression is over
		self.indentLevel -= 1
		self.outdent()
		self.write('</expression>\n')

	# compiles a (possibly empty) comma-separated list of expressions
	# (expression (',' expression)*)?
	def compileExpressionList(self):
		"""
		empty expressionList tags are a possibility
			<expressionList>
			</expressionList>

		otherwise, expressions separated by ',' symbols: x, y, z
			<expressionList>
			<expression>
			  <term>
				<identifier> x </identifier>
			  </term>
			</expression>
			<symbol> , </symbol>
			<expression>
			  <term>
				<identifier> y </identifier>
			  </term>
			</expression>
			</expressionList>
		:return:
		"""
		# (expression (',' expression)*)?
		self.write('<expressionList>\n')
		self.indent()
		# how do we check if an expression exists? if it's ')', exprList empty
		# e.g. out.write('compiler') vs out.write()
		# hitting the last ')' ensures the expressionList is done
		self.peek()

		if self.tk.getTokenType() == TokenType.SYMBOL and self.tk.symbol() == ')':
			self.outdent()
			self.write('</expressionList>\n')
			return
		else:
			self.compileExpression()

		self.peek()

		# after compileExpression, next token has only two options:  ')' vs ','
		# ',' corresponds to (',' expression)*. eat(',') → compileExpression
		while self.tk.symbol() == ',':
			self.eat(',')
			self.compileExpression()
			self.peek()

		# ending case: ')' means we're done
		# TODO potential bug double evaluating ')' in subroutineName(exprList)
		# TODO maybe move this code to compileDo
		if self.tk.symbol() == ')':
			self.outdent()
			self.write('</expressionList>\n')
		else:
			raise ValueError(
				f'expressionList did not end with closeParen token')

	# we must have two versions of eat: one with advance and one without
	# this is for cases with ()? or ()* and we must advance first before
	# checking the token, e.g.
	# → varDec: 'var' type varName (',' varName)*';'
	# → let: 'let' varName ('[' expression ']')? '=' expression ';'
	def eat(self, expectedTokenValue: str):
		# expected token ← what the compile_ method that calls eat expects
		# actual tokenizer token ← tokenizer.advance
		# note that sometimes we don't advance because the compile method
		# calling this has already done so

		# four cases between doNotAdvWhileEating and advance parameters:
		# skipNextAdvance advanceFlag action
		#               T T           → don't advance()
		#               T F           → don't advance()
		#               F T           → advance(), reset sna
		#               F F           → don't advance(), reset sna
		# ∴ only advance if skipNextAdvance=False, advanceFlag=True

		# if not self.skipNextAdvanceOnEat and advanceFlag:
		# skip advance if flag is on from LL2 read-ahead situation
		# → see term: foo, foo[expr], foo.bar(exprList), bar(exprList)
		# turn off the "skip next eat()'s advance()" toggle if it's on
		self.advance()
		# reset the flag now that we've 'consumed' an eat command

		tokenType = self.tk.getTokenType()  # current token

		match tokenType:  # determine value of token
			case TokenType.KEYWORD:
				value = self.tk.keyWord()
				self.write(f'<keyword> {value} </keyword>\n')

			case TokenType.SYMBOL:
				value = convertSymbolToHtml(self.tk.symbol())
				self.write(f'<symbol> {value} </symbol>\n')

			case TokenType.IDENTIFIER:
				value = self.tk.identifier()
				self.write(f'<identifier> {value} </identifier>\n')

			case TokenType.INT_CONST:
				value = self.tk.intVal()
				self.write(f'<integerConstant> {value} </integerConstant>\n')

			case TokenType.STRING_CONST:
				value = self.tk.stringVal()
				self.write(f'<stringConstant> {value} </stringConstant>\n')

			case _:  # impossible
				raise TypeError(f'token type invalid: not keyword, symbol, \
					identifier, int constant, or string constant: {tokenType}')

		# assert expectedToken matches actual token
		# print(f'[eating → {value}]')
		assert expectedTokenValue == value, f'expected: {expectedTokenValue}, actual: {value}'

	# wrapper for self.tk.advance. skips next advance
	def peek(self):
		self.advance()
		self.skipNextAdvance = True

	# advances unless 'skipNextAdvance' is True
	def advance(self):
		if not self.skipNextAdvance:
			self.tk.advance()

		self.skipNextAdvance = False
