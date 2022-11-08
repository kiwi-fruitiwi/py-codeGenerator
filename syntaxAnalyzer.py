"""
@author kiwi
@date 2022.08.14

project contract
  implement syntaxAnalyzer in python
    parses .jack files → xml from nand2tetris/projects/10
    compare with TextComparer in nand2tetris/tools
  see chapter.10 of book

  1. build JackTokenizer ← unit 4.8
  2. build CompilationEngine, basic expressionless → complete with expressions
    xml file needs to be wrapped in <tokens> tag
    string constants have no double quotes
    remember html special characters [< > " &] → [&lt; &gt; &quot; &amp]

  currentToken varName has 5 branches:
    foo
    foo[expression]
    foo.bar(expList)
    Foo.bar(expList) ← what's the difference? static method vs member?
    bar(expList)

  this is the only case where the jack grammar is LL(2)
    save current token
    look ahead to next one


  ⊼² finish tokenizer, 📹→L4.8, 12:57 is compilation engine
    test using *T.xml files after reading *.jack
    ExpressionLessSquare after basic compilationEngine done
    Square when expressions done

→ a bunch of characters with no space in the middle does not necessarily mean that you have only one token, e.g. getx() has three: getx and two symbols
    look up getx in keywords list. not there, so must be identifier
    next is straightforward symbol table lookup

  consider implementations in library string functions and regex
    check lexical elements diagram in this order. nc = next character
        check if nc is in the symbols list
        integerConstant → is nc [0-9]? take rest of [0-9]
        surrounded by "" → stringConstant. next "[all char ex. " \n]"
        else nc is alphabetical:
            check keywords list for next token. should be all alphabetic
            identifier → [0-9a-zA-Z_]+

  tokenizing strategy
    observations:
        every line ends with a newline or symbol
        every token ends with a space or a symbol (or newline)
        → find position of next space, \n, or symbol →  evaluate current token

    advance()
    for code line `class Main {`
        first character 'c'
        append until we reach: ⎵ \n symbol → 'class'
            identify as keyword. if it hadn't, identifier
        for 'Main', append until ⎵. same as above

    for code line 'function void main() {'
        main() will parse 'main' and arrive upon a symbol

    for code line `let length = Keyboard.readInt("HOW MANY NUMBERS? ");`
        reading in the first double quote makes us find the next one in the line
            throw error if not

    for code line `let i = 0;`
        if numeric, must be an integerConstant because identifiers can't start
            eat until delimiter: ⎵ \n symbol

    method: #detectDelimiter returns true if next char is ⎵, \n, symbol

  tokenizer testing method: line by line parsing: one new category at a time
  tokenizer pseudocode

"""

# take care of multiple files in a directory vs one target file

from compilationEngine import CompilationEngine

from tokenizer import JackTokenizer
from tokenizer import TokenType

from pathlib import Path
import os


def generateTokensFromJack():
    root: str = 'C:/Dropbox/code/nand2tetris/kiwi/nand2tetris/projects/'
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
    root: str = 'C:/Dropbox/code/nand2tetris/kiwi/nand2tetris/projects/'
    # filename: str = root + '10/ArrayTest/Main.jack'
    filename: str = 'test.jack'
    outputUri = 'output.xml'  # compilation engine output

    ce = CompilationEngine(filename, outputUri)
    ce.testCompile()


generateCompilationEngineOutput()