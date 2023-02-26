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
# ☒ create symbolTable.py tests

import enum
from typing import Dict


class VarKind(enum.Enum):
	STATIC = "static"
	FIELD = "this"
	ARG = "argument"
	VAR = "local"


class Entry:
	def __init__(self, varType: str, kind: VarKind, quantity: int):
		self.type = varType
		self.kind = kind
		self.quantity = quantity

	def __eq__(self, other):
		return \
			self.type == other.type and \
			self.kind == other.kind and \
			self.quantity == other.quantity

	def __repr__(self):
		return f'[{self.type}, {self.kind}, {self.quantity}]'


def testSymbolTables():
	st = SymbolTable()

	st.define('x', 'int', VarKind.FIELD)
	st.define('y', 'int', VarKind.FIELD)
	st.define('z', 'int', VarKind.FIELD)
	st.define('pointCount', 'int', VarKind.STATIC)

	st.define('this', 'Point', VarKind.ARG)
	st.define('other', 'Point', VarKind.ARG)
	st.define('dx', 'int', VarKind.VAR)
	st.define('dy', 'int', VarKind.VAR)
	st.define('dz', 'int', VarKind.VAR)
	print(st)

	print(st.varCount(VarKind.VAR))
	print(st.kindOf('dx'))
	print(st.typeOf('this'))


class SymbolTable:
	def __init__(self):
		# use hash tables:


		# one for class scope
		self.classTable: Dict[str, Entry] = {}

		# and one for subroutine scope
		self.srtTable: Dict[str, Entry] = {}

		# counts for all variable kinds
		self.staticCount = 0	# class-level
		self.fieldCount = 0		# class-level
		self.argCount = 0		# subroutine-level
		self.localCount = 0		# subroutine-level

	def startSubroutine(self):
		"""
		starts a new subroutine scope, i.e. resets the subroutine's symbol table
		"""
		self.srtTable = {}
		self.argCount = 0
		self.localCount = 0

	# returns True if variable exists in either class or srt-level tables
	def hasVar(self, keyName: str) -> bool:
		existsInClass: bool = keyName in self.classTable.keys()
		existsInSubroutine: bool = keyName in self.srtTable.keys()

		return existsInSubroutine or existsInClass


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
		assert name not in self.classTable.keys(), f'duplicate id: {name}'
		assert name not in self.srtTable.keys(), f'{name} duplicate found'

		# find how many of this kind we have so far
		currentCount = self.varCount(kind)

		match kind:
			case VarKind.STATIC:
				self.staticCount += 1
				self.classTable[name] = Entry(vType, kind, currentCount)
				return
			case VarKind.FIELD:
				self.fieldCount += 1
				self.classTable[name] = Entry(vType, kind, currentCount)
				return
			case VarKind.ARG:
				self.argCount += 1
				self.srtTable[name] = Entry(vType, kind, currentCount)
				return
			case VarKind.VAR:
				self.localCount += 1
				self.srtTable[name] = Entry(vType, kind, currentCount)
				return

		# assert arg var only go into srtTable, static field only → classTable
		raise ValueError(f'{kind} not found')


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
				return self.localCount

		raise ValueError(f'{kind} not found')

	def kindOf(self, name: str) -> VarKind:
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


	def typeOf(self, name: str) -> str:
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


	def indexOf(self, name: str) -> int:
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
		result = self.getClassLevelSymTableRepr() + '\n'
		result += self.getSrtLevelSymTableRepr('unspecified')
		return result

	def getClassLevelSymTableRepr(self) -> str:
		result = '🔥 class-level symbol table:\n'
		result += displaySymbolTable(self.classTable)
		return result

	# returns subroutine-level symbol table with srt's name
	def getSrtLevelSymTableRepr(self, srtName: str) -> str:
		# iterate through both tables and display them
		# helper function: printSymbolTable(d: dict)
		result = f'🐳 subroutine-level symbol table: {srtName}\n'
		result += displaySymbolTable(self.srtTable)
		return result


def displaySymbolTable(table: Dict):
	result = ''

	# TODO: variable width indented table
	#   iterate through keys and record max key length
	#   use this as the padding value

	for key in table.keys():
		result += f'\t{key: >14} → {table[key]}\n'
	if result == '':
		return '\tempty\n'
	else:
		return result


# testSymbolTables()