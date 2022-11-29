# based on ⊼₂ unit 5.10 proposed implementation
# symbolTable example
#	class-level: reset every time we compile a new class
#		name		type	kind		#
#		x			int		field		0
#		y			int		field		1
#		pointCount	int		static		0
#	subroutine-level: reset upon compiling each new subroutine
# 		name		type	kind		#
#		this		Point	argument	0
#		other		Point	argument	1
#		dx			int		local		0
#		dy			int		local		1
#
# we give each variable a running index within its scope and kind
# the index starts at 0 and increments by 1 every new symbol
#	reset to 0 when we start a new scope
#
# when you compile error free Jack code, each identifier not found in the class
# or srt symbol tables can be assumed to be either a:
# 	subroutine or class name
#
# TODO create symbolTable.py tests

import enum
from typing import Dict


class VarKind(enum.Enum):
	STATIC = "static"
	FIELD = "field"
	ARG = "argument"
	VAR = "local"


class Entry:
	def __init__(self, varType: str, kind: VarKind, quantity: int):
		self.type = varType
		self.kind = kind
		self.quantity = quantity


class SymbolTable:
	def __init__(self):
		# use hash tables:


		# one for class scope
		self.classTable: Dict[str, Entry] = {}

		# and one for subroutine scope
		self.srtTable: Dict[str, Entry] = {}

		# counts for all variable kinds
		self.staticCount = 0
		self.fieldCount = 0
		self.argCount = 0
		self.varCount = 0


	def startSubroutine(self):
		"""
		starts a new subroutine scope, i.e. resets the subroutine's symbol table
		"""
		self.srtTable = {}


	def define(self, name: str, vType: str, kind: VarKind):
		"""
		defines a new identifier of the given name, type, and kind, and assigns
		it to a running index. STATIC and FIELD identifiers have a class scope,
		while ARG and VAR identifiers have a subroutine scope.

		:param name: e.g. x, y, this, pointCount
		:param vType: int, Point
		:param kind: STATIC, FIELD, ARG, VAR
		:return: nothing
		"""
		# assert no duplicate variable names


		# find how many of this kind we have so far
		currentCount = self.varCount(kind)

		if kind in [VarKind.STATIC, VarKind.FIELD]:
			self.classTable[name] = Entry(vType, kind, currentCount + 1)

		# assert arg var only go into srtTable, static field only → classTable

	def varCount(self, kind: VarKind) -> int:
		"""
		:param kind: STATIC, FIELD, ARG, VAR
		:return: the number of variables of the given →kind← already defined in
		the	current scope
		"""
		match kind:
			case VarKind.STATIC:
				return self.staticCount
			case VarKind.FIELD:
				return self.fieldCount
			case VarKind.ARG:
				return self.argCount
			case VarKind.VAR:
				return self.varCount

		raise ValueError(f'{kind} not found')


	def kindOf(self, name: str):
		"""
		returns the kind of the named identifier in the current scope. If the
		identifier is unknown in the current scope, returns 🌟 NONE 🌟
		:param name: identifier, e.g. x, y, pointCount, this
		:return: STATIC, FIELD, ARG, VAR
		"""

		# look in srt-level symbol table first
		if name in self.srtTable:
			return self.srtTable[name].kind

		# if not found, check class-level symbol table
		if name in self.classTable:
			return self.classTable[name].kind

		# throw error if name doesn't exist in either
		raise ValueError(f'{name} not found in either symbol table')


	def typeOf(self, name: str):
		"""
		:param name: identifier, e.g. x, y, pointCount, this
		:return: the type of the named identifier in the current scope
		"""

		# look in srt-level symbol table first
		if name in self.srtTable:
			return self.srtTable[name].type

		# if not found, check class-level symbol table
		if name in self.classTable:
			return self.classTable[name].type

		# throw error if name doesn't exist in either
		raise ValueError(f'{name} not found in either symbol table')


	def indexOf(self, name: str):
		"""
		:param name: identifier, e.g. x, y, pointCount, this
		:return: the index assigned to the named identifier. not count. count+1
		"""

		# look in srt-level symbol table first
		if name in self.srtTable:
			return self.srtTable[name].quantity

		# if not found, check class-level symbol table
		if name in self.classTable:
			return self.classTable[name].quantity

		# throw error if name doesn't exist in either
		raise ValueError(f'{name} not found in either symbol table')

	def __repr__(self):
		# iterate through both tables and display them
		# helper function: printSymbolTable(d: dict)

		pass








