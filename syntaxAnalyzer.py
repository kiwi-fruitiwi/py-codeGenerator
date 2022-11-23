"""
@author kiwi
@date 2022.11.26

make symbolTables → see 5.10 API
test handling of identifiers

test programs for evolving compiler
	seven
		arithmetic expression involving constants only
		do + return statements
	convertToBin
		arbitrarily choose output location
		converts RAM[8000] to binary → 16 bits in RAM[8001-8016]
		tests:
			expressions without arrays or method calls
			procedural constructs: if while do let return
		tips for testing the compiled code
			cannot access RAM in 'no animation' mode
			use binoculars to look at address 8000
			click 'stop' button to see the results in state of the RAM
	square: constructors, methods, expression including method calls
		multiple files! Square, SquareGame, Main
	average: arrays and strings
	pong: complete object-oriented app with objects, static vars
		compile Bat, PongGame, Main, Ball
		delay execution. reduce speed slider to play game
	complexArrays: handles array manipulation with fancy indices
		a[b[a[3]]] = a[a[5]] * b[7-a[3]-Main.double(2)+1];
		test easily via screen's Output
use compiler to compile the program directory
inspect generated code
if no errors, load directory into VM emulator
run compiled program → inspect results
if problem, fix compiler and repeat

"""

# take care of multiple files in a directory vs one target file

from compilationEngine import CompilationEngine

from tokenizer import JackTokenizer
from tokenizer import TokenType


def generateTokensFromJack():
    # root: str = 'C:/Dropbox/code/nand2tetris/kiwi/nand2tetris/projects/'
    # filename: str = root + '10/ArrayTest/Main.jack'
    filename: str = 'test.jack'

    tk = JackTokenizer(filename)
    tk.advance()
    # output = open('tests/ArrayTest/output.xml', 'w')
    output = open('output.xml', 'w')
    output.write(f'<tokens>\n')

    # main loop
    while tk.hasMoreTokens():
        tokenClassification = tk.getTokenType()
        match tokenClassification:  # determine value of token
            case TokenType.KEYWORD:
                value = tk.keyWord()
                tagName = 'keyword'
            case TokenType.SYMBOL:
                value = tk.symbol()
                tagName = 'symbol'
            case TokenType.IDENTIFIER:
                value = tk.identifier()
                tagName = 'identifier'
            case TokenType.INT_CONST:
                value = tk.intVal()
                tagName = 'integerConstant'
            case TokenType.STRING_CONST:
                value = tk.stringVal()
                tagName = 'stringConstant'
            case _:
                raise TypeError(f'token type invalid: not keyword, symbol, '
                                f'identifier, int constant, or string constant.')

        output.write(f'<{tagName}> {value} </{tagName}>\n')
        tk.advance()


    output.write(f'</tokens>\n')


# generateTokensFromJack()


def generateCompilationEngineOutput():
    # root: str = 'C:/Dropbox/code/nand2tetris/kiwi/nand2tetris/projects/'
    # filename: str = root + '10/ArrayTest/Main.jack'
    filename: str = 'test.jack'
    outputUri = 'output.xml'  # compilation engine output

    ce = CompilationEngine(filename, outputUri)
    ce.testCompile()


generateCompilationEngineOutput()
