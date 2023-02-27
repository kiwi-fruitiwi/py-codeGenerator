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

# used for Path().stem
from pathlib import Path
import os


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


def compileSingleFile(filename: str, xmlOutput: str, vmOutput: str):  # format: 'test.jack'
    # root: str = 'C:/Users/kiwi/Dropbox/code/nand2tetris/kiwi/nand2tetris/projects/'
    # filename: str = root + '10/ArrayTest/Main.jack'

    ce = CompilationEngine(filename, xmlOutput, vmOutput)
    ce.testCompile()


def main(path: str) -> None:
    # main must determine if filename is directory or file
    # → and instantiate parser objects to read .vm files inside the directory

    """
    encapsulate parser writer loop with a single method
    save the directory name

        if a file is detected:
            parser reads loc.vm
            writer outputs to loc.asm
        if directory:
            vmFileList ← generate
                parser reads all .vm files in vmFileList
                while codeWriter writes each one to loc.asm

    :param path:
    :return:
    """

    # os.path.abspath returns abspath from where the .py file is executing
    if os.path.isfile(path):
        print(f'\n🐳 file detected: {path}')
        # run parser writer loop on the file
        # todo find directory name. or chop off .vm and replace with .asm

        basename = os.path.basename(os.path.dirname(path))
        print(f'directory name → {basename}')

        stem = Path(path).stem  # a stem is a filename without an extension
        print(f'stem → {stem}')

        path = Path(path)
        parentPath = path.parent.absolute()
        print(f'parent path → {str(parentPath) + os.sep}')

        # if the path is a file, set .xml and .vm output paths
        xmlOutputPath = str(parentPath) + os.sep + stem + ".xml"
        vmOutputPath = str(parentPath) + os.sep + stem + ".vm"
        readpath = str(path)
        basename = os.path.basename(os.path.dirname(path))

        print(f'readpath → {readpath}')
        print(f'basename → {basename}\n\n')
        compileSingleFile(path, xmlOutputPath, vmOutputPath)

    elif os.path.isdir(path):
        print(f'[DETECT] directory detected: {path}')
        # if the path is a directory, generate list of vm files in directory
        # run parser writer loop on each one; codeWriter uses 'w[rite]' mode at
        # first, then '[a]ppend' mode for subsequent files in the list

        # loop through .vm files in directory
        for file in os.listdir(path):
            if file.lower().endswith('.vm'):
                print(f'🚙 looping through vm files → {file}, '
                      f'{os.path.abspath(file)}')
        print('\n')

        # detect .vm files in this directory
        # save directory root, which always contains a slash at the end?
        root = path
        print(f'root → {root}')

        # basename is the name of the directory, e.g.
        # c:/Dropbox/StaticTest/ → StaticTest
        basename = os.path.basename(os.path.dirname(path))
        print(f'os.path.dirname(absPath) → {os.path.dirname(path)}')
        print(f'dirname → {basename}\n')

        outputPath = root + basename + ".asm"
        print(f'✒ overwriting {outputPath}')

        writer = CodeWriter(outputPath)
        writer.writeBootstrap()

        '''
        overwrite .asm output if this is the first time we're in a directory,
        but append for all following files ← deprecated because we now open 
        codeWriter only once.

        we must start with Sys.vm, and then the other files; raise an error 
        if Sys.vm is not present, but move it to index 0 if it is
        '''
        filesInDirectory = os.listdir(path)
        if 'Sys.vm' not in filesInDirectory:
            raise ValueError(f'Sys.vm not present in directory.')
        else:
            vmFiles = []
            for file in filesInDirectory:
                if file.lower().endswith('.vm'):
                    if file != 'Sys.vm':
                        vmFiles.append(file)
            vmFiles.insert(0, 'Sys.vm')

        for file in vmFiles:
            if file.lower().endswith('.vm'):  # 'file' is a VM file
                readPath = root + file
                print(f'📃 translating: {readPath}')

                # TODO: file should strip .vm :p
                translate(readPath, writer, file)

    else:
        raise ValueError(f'{path} does not seem to be a file or directory')


main('tests/Seven/Main.jack')