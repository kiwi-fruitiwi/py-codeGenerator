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

import enum


class VarType(enum.Enum):
	STATIC = 1
	FIELD = 2
	ARG = 3
	VAR = 4


class SymbolTable:
	# start new subroutine scope
	def __init__(self):
		pass

	def define(self, name: str, vType: str, kind: VarType):
		"""
		defines a new identifier of the given name, type, and kind, and assigns
		it to a running index. STATIC and FIELD identifiers have a class scope,
		while ARG and VAR identifiers have a subroutine scope.

		:param name: e.g. x, y, this, pointCount
		:param vType: int, Point
		:param kind: STATIC, FIELD, ARG, VAR
		:return: nothing
		"""
		pass

	def varCount(self, kind: VarType):
		"""
		:param kind: STATIC, FIELD, ARG, VAR
		:return: the number of variables of the given kind already defined in the
		current scope
		"""
		pass

	def kindOf(self, name: str):
		"""
		returns the kind of the named identifier in the current scope. If the
		identifier is unknown in the current scope, returns 🌟 NONE 🌟
		:param name: identifier, e.g. x, y, pointCount, this
		:return: STATIC, FIELD, ARG, VAR
		"""
		pass

	def typeOf(self, name: str):
		"""
		:param name: identifier, e.g. x, y, pointCount, this
		:return: the type of the named identifier in the current scope
		"""
		pass

	def indexOf(self, name: str):
		"""
		:param name: identifier, e.g. x, y, pointCount, this
		:return: the index assigned to the named identifier
		"""
		pass













