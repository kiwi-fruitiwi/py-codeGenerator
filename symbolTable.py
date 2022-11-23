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

class SymbolTable:
	# start new subroutine scope
	def __init__(self):
		pass