# part 1: symbol table extension to project 10 → see lectureNotes.txt
# part 2: generating actual code instead of XML
#
# ⊼².📹→📇 5.11 testing strategy
#	 staged development plan with unit testing
#	 	test programs for evolving compiler
#	 		⚙️seven: code → arithmetic expression involving constants only
#				do + return statements
#	 		⚙️convertToBin: 🔬 if/else flowchart
#	 			arbitrarily choose output location
#	 			converts RAM[8000] to binary → 16 bits in RAM[8001-8016]
#	 			tests:
#	 				expressions without arrays or method calls
#	 				procedural constructs: if while do let return
#	 			tips for testing the compiled code
#	 				cannot access RAM in 'no animation' mode
#	 				use binoculars to look at address 8000
#	 				click 'stop' button to see the results in state of the RAM
#	 		⚙️square: constructors, methods, expression including method calls
#	 			rework compilationEngine to hand multiple files
#	 				Square, SquareGame, Main
#	 		⚙️average: arrays and strings
#	 		⚙️pong: complete object-oriented app with objects, static vars
#	 			compile Bat, PongGame, Main, Ball
#	 			delay execution. reduce speed slider to play game
#	 		⚙️complexArrays: handles array manipulation with fancy indices
#	 			a[b[a[3]]] = a[a[5]] * b[7-a[3]-Main.double(2)+1];
#	 			test easily via screen's Output
#	 	use compiler to compile the program directory
#	 	inspect generated code
#	 	if no errors, load directory into VM emulator
#	 	run compiled program → inspect results
#	 	if problem, fix compiler and repeat
#
#	 compilers don't generate exactly the same VM code. that's okay!
#	 pop temp 0 after do Output.printInt gets rid of extra value
#	 push constant 0 follows contract with another dummy value
#
#	 recap
#	 	extend syntax analyzer into full-scale compiler
#	 	test evolving compiler on supplied test programs AS YOU DEVELOP IT

from tokenizer import JackTokenizer, TokenType
from symbolTable import SymbolTable, VarKind, Entry
from vmWriter import VMWriter, SegType, ArithType


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
	def __init__(self, inputJackUri, outputXmlUri, outputVMUri):
		# create a Tokenizer object from the inputURI
		self.tk = JackTokenizer(inputJackUri)

		# create a VMWriter object to write to file
		self.vmWriter = VMWriter(outputVMUri)

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

		# keeps track of the class's name because it's a variable type for our
		# symbol tables. notably, it's used for 'this' in subRoutineDec
		self.className = 'undef'
		self.subroutineName = 'undef'

		# accumulator to track number of variables in srt
		# compileVarDec increments this while compileSubroutineDec resets to 0
		self.nLocals = 0

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

		self.peek()  # look ahead to set the className field
		# remember the class name for later symbol table usage
		assert self.tk.getTokenType() == TokenType.IDENTIFIER
		self.className = self.tk.identifier()

		# className is an identifier
		self.compileClassName()
		self.eat('{')

		while self.compileClassVarDec():
			continue  # probably unnecessary continue; empty body

		while self.compileSubroutineDec():
			# TODO: remove temporary extra newline for ease of reading
			self.write('\n')
			continue


		self.eat('}')
		self.outdent()
		self.write('</class>\n')

		print(f'\n{self.symbolTables.getClassLevelSymTableRepr()}')

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

		vKind: VarKind = None
		match self.tk.keyWord():
			case 'static':
				vKind = VarKind.STATIC
			case 'field':
				vKind = VarKind.FIELD
			case _:
				raise ValueError(f'unexpected vKind. expected static or field')

		self.write('<classVarDec>\n')
		self.indent()

		self.advance()
		self.write(f'<keyword> {self.tk.keyWord()} </keyword>\n')
		vType: str = self.__compileType()

		# varName(',' varName)*
		self.__compileVarNameList(vType, vKind)
		self.outdent()
		self.write('</classVarDec>\n')

		return True

	# helper method for classVarDec, subroutineDec, parameterList, varDec
	# pattern: int | char | boolean | className
	# returns the type in string format!
	def __compileType(self) -> str:
		# type → advance, if TokenType is keyword: int char or boolean
		self.advance()

		match self.tk.getTokenType():
			case TokenType.KEYWORD:  # process int, char, boolean
				assert self.tk.keyWord() in ['int', 'char', 'boolean'], f'{self.tk.keyWord()}'
				self.write(f'<keyword> {self.tk.keyWord()} </keyword>\n')
				return self.tk.keyWord()
			case TokenType.IDENTIFIER:  # process className
				self.skipNextAdvance = True
				self.compileClassName()
				return self.tk.identifier()
			case _:
				raise ValueError(
					f'did not find identifier or keyword token: {self.tk.getTokenType()}')

	# compiles a complete method, function, or constructor
	def compileSubroutineDec(self):
		"""
		:return: True if we found a subroutineDec, False if not.
			this is so we can use while self.compileSubroutineDec
		"""
		# clear our subroutine symbol table
		self.symbolTables.startSubroutine()
		self.subroutineName = 'unset'
		self.nLocals = 0

		# skipNextAdvOnEat because we might fail to find a subroutineDec
		self.peek()

		# if compileSubroutineDec is being called, it must start with:
		# 'constructor', 'function', or 'method'
		# so if it doesn't, we know compileClass's subRoutineDec* clause is done
		# and we can return False
		if self.tk.getTokenType() != TokenType.KEYWORD:
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

		# if we have a method or constructor, add 'this' to the srt symbol table
		# 	to do this we call self.symbolTable.define(name, vType, kind) with:
		# 		name=this, vType=what the class is, kind=argument
		# probably not necessary for constructor, but let's start with it in
		if keywordValue in ['method', 'constructor']:
			self.symbolTables.define('this', self.className, VarKind.ARG)

		# ('void'|type)
		self.peek()

		# must be void, int, char, boolean, or className
		if self.tk.getTokenType() == TokenType.KEYWORD and self.tk.keyWord() == 'void':
			self.eat('void')
		else:  # it must be int, char, boolean, or className, aka 'type'$
			self.__compileType()

		# subroutineName
		self.subroutineName = self.compileSubroutineName()

		# '(' parameterList ')'
		self.eat('(')
		self.compileParameterList()
		self.eat(')')

		# subroutineBody → { varDec* statements }
		self.compileSubroutineBody()
		print(f'\n{self.symbolTables.getSrtLevelSymTableRepr(self.subroutineName)}')

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
		vType: str = self.__compileType()

		self.compileUndefinedVariable(vType, VarKind.ARG)

		# then while next token is ',', consume type varName
		self.peek()

		# pattern: (, type varName)*
		# next token must be either ',' or ';'
		assert self.tk.getTokenType() == TokenType.SYMBOL
		while self.tk.symbol() == ',':
			self.eat(',')
			vType: str = self.__compileType()
			self.compileUndefinedVariable(vType, VarKind.ARG)
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

		self.vmWriter.writeFunction(self.className, self.subroutineName, self.nLocals)

		# statements always starts with keyword in [let, if, while, do, return]
		self.compileStatements()
		self.eat('}')
		self.outdent()
		self.write('</subroutineBody>\n')

	# compiles a var declaration in the format var type varName (, varName)*;
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
		vType: str = self.__compileType()

		# varName (',' varName)*';'
		self.__compileVarNameList(vType, VarKind.VAR)
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
			pass  # probably not necessary

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
			# print(f'🌌 statement ended with {self.tk.getTokenType()}: {self.tk.symbol()}')
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
	def __compileVarNameList(self, vType: str, vKind: VarKind):
		# varName
		self.compileUndefinedVariable(vType, vKind)
		self.nLocals += 1  # update nLocals count for current subroutine
		self.peek()  # check ahead to see: ',' or ';' ?

		# (',' varName)*
		while self.tk.symbol() == ',':
			self.eat(',')
			self.compileUndefinedVariable(vType, vKind)
			self.nLocals += 1
			self.peek()

		# the only token we have left is ';'
		self.eat(';')

	# eats token = identifier, checks type
	# currently not called
	def compileIdentifier__deprecated(self):
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
	# returns subroutine's name
	def compileSubroutineName(self) -> str:
		self.advance()
		assert self.tk.getTokenType() == TokenType.IDENTIFIER, f'{self.tk.getTokenType()}'
		self.write(
			f'<subroutineName> {self.tk.identifier()} </subroutineName>\n')
		return self.tk.identifier()

	# compile a variable already known to be defined in our symbolTables
	# used for compileLet, term?
	def compileDefinedVariable(self):
		self.advance()
		assert self.tk.getTokenType() == TokenType.IDENTIFIER, f'{self.tk.getTokenType()}'
		varName = self.tk.identifier()

		# if we're just using the variable, like in a let statement, don't
		# add a new entry to the symbolTable; verify this pre-defined
		# variable exists in our symbolTable
		#  	verify variable existence
		# 	find VarKind via table lookup using 🦔: st.kindOf
		# 	output appropriate tag
		st = self.symbolTables
		assert st.hasVar(varName)

		k: VarKind = st.kindOf(varName)
		kindPrefix: str = k.value

		self.write(f'<{kindPrefix}Variable> {varName} </{kindPrefix}Variable>\n')

	# sub-method of compileIdentifier: covers static field arg var
	def compileUndefinedVariable(self, vType: str, vKind: VarKind):
		self.advance()
		assert self.tk.getTokenType() == TokenType.IDENTIFIER, f'{self.tk.getTokenType()}'
		varName = self.tk.identifier()
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

		# variable not yet defined: add to symbol table, write tag
		self.symbolTables.define(varName, vType, vKind)
		self.write(f'<{tag}> {varName} </{tag}>\n')

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
		self.compileDefinedVariable()

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

		# for expressionLess, use term: id, strC, intC
		# can also be true, false, null, this ← keywords!
		# → actually, these are both taken care of in compileExpr,Term
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
		self.peek()  # check for else token
		if self.tk.getTokenType() == TokenType.KEYWORD:
			if self.tk.keyWord() == 'else':
				self.write('<elseStatement>\n')
				self.indent()
				self.eat('else')
				self.__compileStatementsWithinBrackets()
				self.outdent()
				self.write('</elseStatement>\n')

		self.outdent()
		self.write('</ifStatement>\n')

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

		# when a doStatement occurs, nothing is done with the function's retVal
		# so we can get rid of it with pop temp 0
		self.vmWriter.writePop(SegType.TEMP, 0)

	def __compileSubroutineCallHelper(self):
		st = self.symbolTables
		# subroutineName '(' expressionList ')' |
		# (className | varName) '.' subroutineName '(' expressionList ')'
		#
		# two possibilities:
		# 	identifier (className | varName) → '.' e.g. obj.render(x, y)
		# 	identifier (subroutineName) → '(' e.g. render(x, y)
		self.advance()
		identifierName = self.tk.identifier()

		# we have either of two symbols, '.' or '(':
		# 1. subroutineName(expressionList), or
		# 2. (className|varName).subroutineName(expressionList)
		# upon reading the first identifier token, we can peek at the next token
		# if it's a ., we must be in case 2 and identify (className|varName)
		# if it's (, we are in case 1 and it's easy.
		self.peek()

		if self.tk.symbol() == '.':
			# we are in case 2! (className|varName).srtName(expressionList)
			# check the symbolTable for varName. if not found, it's a className
			if st.hasVar(identifierName):
				k: VarKind = st.kindOf(identifierName)  # static field lcl arg
				kindPrefix: str = k.value

				self.write(
					f'<{kindPrefix}Variable> {identifierName} '
					f'</{kindPrefix}Variable>\n')
			else:
				self.write(f'<className> {identifierName} </className>\n')

			self.eat('.')

		# now process the common tail grammar: subroutineName(expressionList)
		srtName: str = self.compileSubroutineName()

		# then eat('(') → compileExpressionList
		self.eat('(')
		expressionCount: int = self.compileExpressionList()
		self.eat(')')

		# TODO this needs work depending on what idName is: class or var
		#   for class, output `call className srtName nArgs`
		#   for var, we want `call typeof(varName) srtName nArgs+1`
		self.vmWriter.writeCall(identifierName, srtName, expressionCount)

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

				self.vmWriter.writePush(SegType.CONST, 0)
				self.vmWriter.writeReturn()
				return
		else:
			# there's an expression in → expression? ';'
			self.compileExpression()
			self.eat(';')
			self.outdent()
			self.write('</returnStatement>\n')

			# TODO maybe compileExpression needs to return the value of the exp?
			# the result of this expression should be on top of the stack
			# 	not sure if anything is needed here
			# self.vmWriter.writeReturn()

	# compiles a term. if the current token is an identifier, the routine must
	# distinguish between a variable, an array entry, or a subroutine call. a
	# single look-ahead token, which may be one of [, (, or ., suffices to
	# distinguish between the possibilities. any other token is not part of this
	# term and should not be advanced over.
	def compileTerm(self):
		"""
		pattern:
			intConst | strConst | keywordConst |
			varName |
			varName'['expression']' |
			subroutineCall |
			'('expression')' |
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
				identifier: str = self.tk.identifier()
				classOrSrtName: bool = False

				# can remove this comment block when everything works:
				# what identifier is this? use st.kindOf with {value}
				#  (static|field|argument|local)Variable tag
				#  .
				#  varName ← already defined
				#  varName[expr]
				#  srtCall(exprList)
				#  className|varName.srtName(exprList)
				#		if not symbolTables.hasVar: className, else varName
				#		srtName is guaranteed → compileSubroutineName()

				# it's an identifier not in our symbolTables:
				# this means it's a className or subRoutineName
				# this only happens in Jack Grammar: subroutineCall
				#	subroutineName(expressionList)
				#	(className|varName).subroutineName(expressionList)
				if not self.symbolTables.hasVar(identifier):
					# set a classOrSrtName flag and skip self.write for now
					# → check LL2 for next token
					# 	case '(': write <srtName> as tag
					#	case '.': must be className → '.' → srtName
					classOrSrtName = True

					# we will take care of token output in LL2 cases below!
				else:
					# it's an identifier in our symbolTables! these cases apply:
					# 	varName
					#	varName[expression]
					#	varName.subroutineName(expressionList)
					# regardless, it must be static, field, argument, local
					kind: VarKind = self.symbolTables.kindOf(identifier)
					tag: str = kind.value  # e.g. static field argument local
					self.write(
						f'<{tag}Variable> {identifier} </{tag}Variable>\n')

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
							# we're at the end of the line! we can stop here
							pass
						case '.':
							# remember that flag we set earlier?
							# in case '.' it can only be a class

							# matches pattern in subroutineCall:
							# 	(className | varName).srtName(exprList)
							#
							# example:
							# 	let key = Keyboard.keyPressed();
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
							if classOrSrtName:
								self.write(
									f'<className> {identifier} </className>\n')
							else:
								# not className means it must be varName
								# we already output this varName in LL1 clause
								pass
							self.eat('.')

							self.compileSubroutineName()
							self.eat('(')
							self.compileExpressionList()
							self.eat(')')

						case '(':  # must match subroutineName(expressionList)
							assert classOrSrtName
							self.compileSubroutineName()
							self.eat('(')
							self.compileExpressionList()
							self.eat(')')

						case '[':  # matches varName[expression]
							assert not classOrSrtName
							self.eat('[')
							self.compileExpression()
							self.eat(']')

						# these are all ops!
						case '+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=':
							pass

						# this is the next token for expressionList
						case ',':  # TODO is this needed?
							pass

						# closing array bracket for our simple term
						case ']':  # TODO is this needed?
							pass

						case _:
							raise ValueError(
								f'invalid symbol in term LL2: {advTokenValue}')

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
						self.vmWriter.writeArithmetic(ArithType.NEG)
					case '~':
						self.eat('~')
						self.compileTerm()
					case _:
						raise ValueError(f'invalid symbol in term LL2: {value}')

			case TokenType.KEYWORD:
				self.advance()
				value = self.tk.keyWord()
				assert value in ['true', 'false', 'null', 'this'], value

				# VMWriter handles each of 4 cases separately
				# TODO
				self.write(f'<keyword> {value} </keyword>\n')

			case TokenType.INT_CONST:
				self.advance()
				value = self.tk.intVal()

				# VMWriter needs to execute: push constant n
				self.vmWriter.writePush(SegType.CONST, value)
				self.write(f'<integerConstant> {value} </integerConstant>\n')

			case TokenType.STRING_CONST:
				self.advance()
				value = self.tk.stringVal()

				# VMWriter uses OS method to handle string constants
				# TODO
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

		# keep track of any ops we see from self.opsList
		# reverse list at the end of expression to apply them one by one
		encounteredOps: list = []

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
			encounteredOps.append(self.tk.symbol())

			# eat it
			self.advance()
			self.write(
				f'<symbol> {convertSymbolToHtml(self.tk.symbol())} </symbol>\n')

			# compile the next term in pattern: op term
			self.compileTerm()

			# peek at next token to see if it's another op so we can continue
			self.peek()

		# if the next term isn't a symbol in opsList, the expression is over
		self.indentLevel -= 1
		self.outdent()
		self.write('</expression>\n')

		# process the ops backwards
		encounteredOps = encounteredOps[::-1]

		for op in encounteredOps:
			match op:
				case '+':
					self.vmWriter.writeArithmetic(ArithType.ADD)
				case '-':
					self.vmWriter.writeArithmetic(ArithType.SUB)
				case '*':
					self.vmWriter.writeCall('Math', 'multiply', 2)

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

		:return: the number of expressions encountered!
		"""
		# (expression (',' expression)*)?
		self.write('<expressionList>\n')
		self.indent()
		# how do we check if an expression exists? if it's ')', exprList empty
		# e.g. out.write('compiler') vs out.write()
		# hitting the last ')' ensures the expressionList is done
		self.peek()

		# keep track of how many expressions we've compiled
		expressionCount: int = 0
		if self.tk.getTokenType() == TokenType.SYMBOL and self.tk.symbol() == ')':
			self.outdent()
			self.write('</expressionList>\n')
			return expressionCount
		else:
			self.compileExpression()
			expressionCount = 1

		self.peek()

		# after compileExpression, next token has only two options:  ')' vs ','
		# ',' corresponds to (',' expression)*. eat(',') → compileExpression
		while self.tk.symbol() == ',':
			self.eat(',')
			self.compileExpression()
			expressionCount += 1
			self.peek()

		# ending case: ')' means we're done
		# TODO potential bug double evaluating ')' in subroutineName(exprList)
		# TODO maybe move this code to compileDo
		if self.tk.symbol() == ')':
			self.outdent()
			self.write('</expressionList>\n')
			return expressionCount
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
				raise ValueError(f'IDENTIFIER tokens no longer handled in eat')

				# value = self.tk.identifier()
				# self.write(f'<identifier> {value} </identifier>\n')

			case TokenType.INT_CONST:
				value = self.tk.intVal()
				self.write(f'<integerConstant> {value} </integerConstant>\n')

			case TokenType.STRING_CONST:
				value = self.tk.stringVal()
				self.write(f'<stringConstant> {value} </stringConstant>\n')

			case _:  # impossible
				raise ValueError(f'token type invalid: not keyword, symbol, \
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
