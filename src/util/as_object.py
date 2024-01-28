class ObjectFromArrayAndIndex():
	def __init__(self, row, idx):
		self._row= row
		self._idx= idx

	def __getattr__(self, k):
		return self._row[self._idx[k]]	

"""
idx= {'a': 1, 'b': 2, 'c': 3}
o1= X("_ABC", idx)
print(f"o1 {o1.a} {o1.b} {o1.c}")

o2= X("_XYZ", idx)
print(f"o2 {o2.a} {o2.b} {o2.c}")
"""

