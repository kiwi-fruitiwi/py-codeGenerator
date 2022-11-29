# encapsulates all activities related to generating output from the compiler
import enum


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
	def __init__(self, outputUri):
		"""
		creates a new output .vm file and prepares it for writing
		"""
		self.out = open(outputUri, 'w')


	def writePush(self, segment: SegType, index: int):
		"""
		writes a VM push command, e.g. 'push local 0'
		"""
		self.out.write(f'push {segment.value} {index}')


	def writePop(self, segment: SegType, index: int):
		"""
		writes a VM pop command, e.g. 'pop argument 0'
		"""
		self.out.write(f'pop {segment.value} {index}')


	def writeArithmetic(self, command: ArithType):
		"""
		writes a VM arithmetic-logical command, e.g. 'and'
		"""
		self.out.write(f'{command.value}')


	def writeLabel(self, label: str):
		"""
		writes a VM label command, e.g. 'label END_PROGRAM'
		"""
		self.out.write(f'label {label}')


	def writeGoto(self, label: str):
		"""
		writes a VM goto command, e.g. 'goto MAIN_LOOP_START'
		"""
		self.out.write(f'goto {label}')


	def writeIf(self, label: str):
		"""
		writes a VM if-goto command, e.g. 'if-goto COMPUTE_ELEMENT'
		"""
		self.out.write(f'if-goto {label}')


	def writeCall(self, functionName: str, nArgs: int):
		"""
		writes a VM call command
		"""
		self.out.write(f'call {functionName} {nArgs}')


	def writeFunction(self, functionName: str, nLocals: int):
		"""
		writes a VM function command, e.g. 'function SimpleFunction.test 2'
		"""
		self.out.write(f'function {functionName} {nLocals}')


	def writeReturn(self):
		"""
		writes a VM return command
		"""
		self.out.write(f'return')


	def close(self):
		"""
		closes the output file
		"""
		self.out.close()









