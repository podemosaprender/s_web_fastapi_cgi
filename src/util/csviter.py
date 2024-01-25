#INFO: iterable csv from iterable of rows, e.g. for FastAPI StreamResponse with SQLModel results

"""
emu_rows= [ (i,f'el cuadrado es "{i*2}" que tal?') for i in range(10) ]

for r in CSVIter(emu_rows, dialect="excel", delimiter=";" ):
	print(r,end="")
"""

from collections import deque
import csv

class CSVIter:
	def __init__(self, iterable, columns=None, **csvparams):
		self.iter= iterable.__iter__() #U: we consume from iter
		self.q= deque() #U: csv writes to queue (may call write many times for one writerow)
		self.csvw= csv.writer(self,**csvparams) #U: we are the "file" XXX: pass options
		if not columns is None:
			self.csvw.writerow(columns)	

	def write(self, s): #U: csv needs a writer
		self.q.append(s)

	def __iter__(self):
		return self

	def __next__(self):
		if len(self.q)==0:
			self.csvw.writerow( self.iter.__next__() )
		
		return self.q.popleft()


