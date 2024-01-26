#INFO: a simple logger function
import sys

def logm(msg,lvl=1,t="DBG",**kwargs):
	print(f"{lvl}:{t}:{msg}:{kwargs}", file=sys.stderr)

