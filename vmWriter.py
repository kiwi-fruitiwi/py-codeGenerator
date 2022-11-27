# encapsulates all activities related to generating output from the compiler
#


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
		creates a new output .vm file and prepares it for writing.
		"""
		self.out = open(outputUri, 'w')


	def writePush(self, segment: SegType, index: int):
		"""
		writes a VM push command, e.g. 'push local 0'
		"""
		self.out.write(f'push {segment.value} {index}')


	def writePop(self, segment: SegType, index: int):
		"""
		writes a VM pop command
		"""
		self.out.write(f'pop {segment.value} {index}')


	def writeArithmetic(self, command: ArithType):
		"""
		writes a VM arithmetic-logical command
		"""
		self.out.write(f'{command.value}')


	def writeLabel(self, label: str):
		"""
		writes a VM label command
		"""
		pass


	def writeGoto(self, label: str):
		"""
		writes a VM goto command
		"""
		pass


	def writeIf(self, label: str):
		"""
		writes a VM if-goto command
		"""
		pass


	def writeCall(self, name: str, nArgs: int):
		"""
		writes a VM call command
		"""
		pass


	def writeFunction(self, name: str, nLocals: int):
		"""
		writes a VM function command
		"""
		pass


	def writeReturn(self):
		"""
		writes a VM return command
		"""
		pass


	def close(self):
		"""
		closes the output file
		"""
		pass









