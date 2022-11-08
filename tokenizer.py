import enum


# enumeration for tokenTypes
class TokenType(enum.Enum):
	KEYWORD = 1
	SYMBOL = 2
	IDENTIFIER = 3
	INT_CONST = 4
	STRING_CONST = 5


''' jack grammar guide for tokenizer.py

	lexical elements → the jack language includes five categories of terminal 
	elements, also known as tokens:
	
	keyword:
		class constructor function method field static var
		int char boolean
		void true false null this let do if else while return
	symbol: 
		{}()[].,;+-*/&|<>=~
		
	integerConstant: 
		a decimal number in the range 0... 32767
		
	StringConstant: 
		a sequence of Unicode chars not including double quotes or \n surrounded 
		by double quotes
		
	identifier: 
		a sequence of letters, digits, and underscore not starting with a digit
'''


class JackTokenizer:
	def __init__(self, filename):
		"""
		opens a .jack file and saves all .jack commands for later processing.
		strips whitespace, full-line comments, and inline comments

		:return: nothing, but fills self.jack_commands array
		"""

		jack_file = open(filename, 'r')
		lines = jack_file.readlines()

		self.code = ""  # all commands in one string, inc. newlines
		self.i = 0  # current index in above monolithic code string
		self.currentTokenType = None  # set in advance()

		# these 5 are used by their respective accessors, e.g. symbol(),
		# keyWord(), intVal(), stringVal(), identifier(). these are called
		# only if the current tokenType matches. invalid otherwise.
		self.currentSymbolValue = None
		self.currentIdentifierValue = None
		self.currentStrConstValue = None
		self.currentIntConstValue = None
		self.currentKeyWordValue = None

		self.symbols = "{}[]().,;+-*/&|<>=~"
		self.digits = "0123456789"  # for integer constants
		self.keywords = [
			'class',
			'constructor',
			'function',
			'method',
			'field',
			'static',
			'var',
			'int',
			'char',
			'boolean',
			'void',
			'true',
			'false',
			'null',
			'this',
			'let',
			'do',
			'if',
			'else',
			'while',
			'return'
		]

		for line in lines:
			# ignore whitespace

			# debug text
			# print(f'{line}', end=" ")

			if line == '\n':
				continue

			# ignore entire-line comments
			if line[0] == '/' and line[1] == '/':
				continue

			# ignore comments that start with /**
			# TODO add case if this appears mid-line: slice!
			#  but what about multiline?
			# if line[0] == '/' and line[1] == '*' and line[2] == '*':
			#	continue

			# ignore mid-line comments
			try:
				index = line.index('//')
				line = line[0:index]
			except ValueError:
				# '//' wasn't found!
				pass

			# strip whitespace
			line = line.strip()

			# combine lines into a single string separated by newlines
			# later, we can count our current line via newline characters?
			# unless newline chars are present in .jack file strings, too.
			self.code += line

		# unsure why this is needed
		# all .jack files have extra newline at the end
		self.code += '\n'

		# process out all multi-line comments starting '/**', ending '*/'
		while True:
			try:
				start = self.code.index('/**')
				end = self.code.index('*/') + 2
				self.code = self.code[:start] + self.code[end:]
			except ValueError:
				break

	# unnecessary; not part of the API
	def getJackCommands(self):
		return self.code

	def hasMoreTokens(self):
		# returns true if there are more tokens in the input file
		#
		# example: [0,1,2,3,4]
		# let's say the command string is length 5. if we're at index 3, we
		# still have one more index, 4, to see. if we're at index 4, that means
		# we're done and hasMoreTokens should return false.
		#
		# note that all .jack files have an extra newline at the end
		return self.i < len(self.code) - 1

	def advance(self):
		# 🏭 skip whitespace(s) and single newlines after tokens
		# lines cannot start with spaces, which the constructor handles w/trim()
		while self.code[self.i] == ' ':
			self.i += 1
			if not self.hasMoreTokens():
				return

		if self.code[self.i] == '\n':  # constructor ensures no double \n
			self.i += 1
			if not self.hasMoreTokens():
				return

		# every lexical category needs to:
		# 1. set self.currentTokenType
		# 2. set self.currentSymbolValue
		# 3. appropriately increment code index, self.i
		firstChar = self.code[self.i] # the first character in our new token!

		if self.__isSymbol(firstChar):
			self.__processSymbol()
			return

		# 🏭 detect string constants
		# 	search rest of string → isn't limited to one line which might be bad
		if firstChar == '\"':
			self.__processStringConstant()
			return

		# 🏭 detect integer constants: decimal numbers in range [0, 32767]
		if firstChar in self.digits:
			self.__processIntConstant()
			return

		# 🏭 now it's either a keyword or identifier. let's build a string!
		self.__processKeywordIdentifier()
		return

	# helper function to process symbols
	def __processSymbol(self):
		sym = self.code[self.i]
		self.currentSymbolValue = sym
		self.currentTokenType = TokenType.SYMBOL
		self.i += 1

		# debug print
		print(f'symbol → {sym}')

	# helper function to process string constants
	def __processStringConstant(self):
		# given: the current character is a double quote; now we need to find
		# the next double quote. code[i+1:] gives the 'rest' of the code
		nextDblQuoteIndex = self.code[self.i+1:].index('\"') + self.i
		self.currentTokenType = TokenType.STRING_CONST

		# it's ndqi+1 because the slice endpoint is not inclusive
		self.currentStrConstValue = self.code[self.i+1: nextDblQuoteIndex+1]
		self.i += len(self.currentStrConstValue) + 2

		# debug print
		print(f'stringConstant → {self.currentStrConstValue}')

	# helper function to process keywords and identifiers
	def __processKeywordIdentifier(self):
		stringBuilder: str = ''
		while not self.__isDelimiter(self.code[self.i]):
			stringBuilder += self.code[self.i]
			self.i += 1

		# 🏭 detect keyword
		if self.__isKeyword(stringBuilder):
			self.currentTokenType = TokenType.KEYWORD
			self.currentKeyWordValue = stringBuilder

			# debug print
			print(f'keyword → {self.currentKeyWordValue}')
		else:
			# 🏭 detect identifier; imperfect as we'd need checks on valid chars
			self.currentTokenType = TokenType.IDENTIFIER
			self.currentIdentifierValue = stringBuilder

			# debug print
			print(f'identifier → {self.currentIdentifierValue}')
			# print(f'{self.currentTokenType}')

	# helper function to process integer constant tokens
	def __processIntConstant(self):
		# build our int while we
		# 1: don't hit a delimiter, and
		# 2: we keep hitting digits
		intBuilder: str = ''
		while not self.__isDelimiter(self.code[self.i]) and self.code[
			self.i] in self.digits:
			intBuilder += self.code[self.i]
			self.i += 1

		# assert value does not overflow, according to spec
		assert 0 <= int(intBuilder) <= 32767

		self.currentTokenType = TokenType.INT_CONST
		self.currentIntConstValue = intBuilder

		# debug print
		print(f'intConstant → {self.currentIntConstValue}')

	# returns true if next char is ⎵, \n, symbol
	def __isDelimiter(self, char: str):
		return self.__isSymbol(char) or (char == ' ') or (char == '\n')

	# returns true if character input is in our symbols list
	def __isSymbol(self, char: str):
		return char in self.symbols

	# returns true if input string is a keyword
	def __isKeyword(self, token: str):
		return token in self.keywords

	def getTokenType(self):
		return self.currentTokenType

	def keyWord(self):
		# assert tokenType
		assert self.currentTokenType == TokenType.KEYWORD
		return self.currentKeyWordValue

	def symbol(self):
		assert self.currentTokenType == TokenType.SYMBOL
		return self.currentSymbolValue

	def identifier(self):
		assert self.currentTokenType == TokenType.IDENTIFIER
		return self.currentIdentifierValue

	def intVal(self):
		assert self.currentTokenType == TokenType.INT_CONST
		return self.currentIntConstValue

	def stringVal(self):
		assert self.currentTokenType == TokenType.STRING_CONST
		return self.currentStrConstValue
