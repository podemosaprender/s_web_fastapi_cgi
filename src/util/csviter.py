#INFO: iterable csv from iterable of rows, e.g. for FastAPI StreamResponse with SQLModel results

"""
emu_rows= [ (i,f'el cuadrado es "{i*2}" que tal?') for i in range(10) ]

for r in CSVIter(emu_rows, dialect="excel", delimiter=";" ):
	print(r,end="")
"""

from collections import deque
import csv

class CSVIter:
	def __init__(self, iterable, mapf=None, columns=None, **csvparams):
		self.iter= iterable.__iter__() #U: we consume from iter
		self.mapf= mapf #U: we may apply a map function
		self.q= deque() #U: csv writes to queue (may call write many times for one writerow)
		self.csvw= csv.writer(self,**csvparams) #U: we are the "file" XXX: pass options
		self.columns= columns
		if not columns is None:
			self.csvw.writerow(columns)	

	def write(self, s): #U: csv needs a writer
		self.q.append(s)

	def __iter__(self):
		return self

	def __next__(self):
		if len(self.q)==0:
			row = None
			while row is None: 
				row= self.iter.__next__() #A: rases Exception if no more elements
				if self.mapf:
					row= self.mapf(row, self.columns)
					#DBG: print("X mapf",self.mapf,row)

			self.csvw.writerow(row)
		
		return self.q.popleft()


