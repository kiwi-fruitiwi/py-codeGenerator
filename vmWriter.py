# encapsulates all activities related to generating output from the compiler
#


import enum


class SegType(enum.Enum):
	CONST = 1
	ARG = 2
	LOCAL = 3
	STATIC = 4
	THIS = 5
	THAT = 6
	POINTER = 7
	TEMP = 8


class ArithType(enum.Enum):
	ADD = 1
	SUB = 2
	NEG = 3
	EQ = 4
	GT = 5
	LT = 6
	AND = 7
	OR = 8
	NOT = 9


class VMWriter:
	def __init__(self):
		"""
		creates a new output .vm file and prepares it for writing.
		"""
		pass

	def writePush(self, segment: SegType, index: int):
		"""
		writes a VM push command, e.g. 'push local 0'
		"""
		pass

	def writePop(self, segment: SegType, index: int):
		"""
		writes a VM pop command
		"""
		pass

	def writeArithmetic(self, command: ArithType):
		"""
		writes a VM arithmetic-logical command
		"""
		pass

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







