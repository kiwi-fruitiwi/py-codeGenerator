# encapsulates all activities related to generating output from the compiler
import enum
from typing import overload
from symbolTable import VarKind


class SegType(enum.Enum):
	CONST = 'constant'
	ARG = 'argument'
	LOCAL = 'local'
	STATIC = 'static'
	THIS = 'this'
	THAT = 'that'
	POINTER = 'pointer'
	TEMP = 'temp'


class ArithType(enum.Enum):
	ADD = 'add'
	SUB = 'sub'
	NEG = 'neg'
	EQ = 'eq'
	GT = 'gt'
	LT = 'lt'
	AND = 'and'
	OR = 'or'
	NOT = 'not'


class VMWriter:
	# set the DEBUG flag to True when you want extra variable name info in the
	# vm output. very handy!
	DEBUG: bool = False
	maxLineWidth: int = 28

	def __init__(self, outputUri):
		"""
		creates a new output .vm file and prepares it for writing
		"""
		self.out = open(outputUri, 'w', encoding='utf-8')

	# writes a string to self.out. includes extra information if DEBUG = True
	def writeToFile(self, output: str, varName: str):
		# sometimes varName is None, like when dealing with constants, this/that
		if self.DEBUG and varName:
			self.out.write(f'{output:{self.maxLineWidth}}  [{varName}]\n')
		else:
			self.out.write(f'{output}\n')

	def writeSegPush(self, segment: SegType, index: int, varName: str = None):
		"""
		writes a VM push command, e.g. 'push local 0'
		"""
		output: str = f'push {segment.value} {index}'
		self.writeToFile(output, varName)

	def writeVarPush(self, segment: VarKind, index: int, varName: str = None):
		"""
		writes a VM push command, e.g. 'push local 0'
		but supports SymbolTable's VarKind enumeration instead of our SegType
		"""
		output: str = f'push {segment.value} {index}'
		self.writeToFile(output, varName)

	def writeSegPop(self, segment: SegType, index: int):
		"""
		writes a VM pop command, e.g. 'pop argument 0'
		"""
		self.out.write(f'pop {segment.value} {index}\n')

	def writeVarPop(self, segment: VarKind, index: int, varName: str = None):
		"""
		writes a VM pop command, e.g. 'pop argument 0'
		but supports SymbolTable's VarKind enumeration instead of our SegType
		"""
		output: str = f'pop {segment.value} {index}'
		self.writeToFile(output, varName)


	def writeArithmetic(self, command: ArithType):
		"""
		writes a VM arithmetic-logical command, e.g. 'and'
		"""
		self.out.write(f'{command.value}\n')


	def writeLabel(self, label: str):
		"""
		writes a VM label command, e.g. 'label END_PROGRAM'
		"""
		self.out.write(f'label {label}\n')


	def writeGoto(self, label: str):
		"""
		writes a VM goto command, e.g. 'goto MAIN_LOOP_START'
		"""
		self.out.write(f'goto {label}\n')


	def writeIfGoto(self, label: str):
		"""
		writes a VM if-goto command, e.g. 'if-goto COMPUTE_ELEMENT'
		"""
		self.out.write(f'if-goto {label}\n')


	def writeCall(self, className: str, functionName: str, nArgs: int):
		"""
		writes a VM call command
		"""
		print(
			f'[ DEBUG ] __compileSubroutineCallHelper '
			f'writeCall for class method 🖋️{className}.{functionName}'
		)
		self.out.write(f'call {className}.{functionName} {nArgs}\n')


	def writeFunction(self, className: str, functionName: str, nLocals: int):
		"""
		writes a VM function command, e.g. 'function SimpleFunction.test 2'
		"""
		self.out.write(f'function {className}.{functionName} {nLocals}\n')


	def writeReturn(self):
		"""
		writes a VM return command
		"""
		self.out.write(f'return\n\n')


	def close(self):
		"""
		closes the output file
		"""
		self.out.close()









