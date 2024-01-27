from .util import ser_json, ser_json_r, get_file_json, set_file_json, fname_safe, ensure_dir
from .cfg import cfg_for
import inspect 
import re

from .logging import logm

#XXX:LOGM
CFG_MEMO_DIR= cfg_for("CACHE_MEMO_DIR", "/var/cache/memo" )
ensure_dir(CFG_MEMO_DIR)

def memo(fname, tunk, ser_proto="json"):
	fpath= f"{CFG_MEMO_DIR}/{fname_safe(fname)}"
	try:
		r = get_file_json(fpath, compressed=True)
		logm(f"CACHE MEMO hit {fname}",l=8)
	except FileNotFoundError as ex:
		logm(f"CACHE MEMO call {fname}",l=7)
		r = tunk()
		set_file_json(fpath, r, compressed=True)

	return r

def wrap(f, onCall=None):
	name= f.__module__+"."+f.__qualname__ #re.findall(r'<function (\S+)', str(f))[0]
	spec= inspect.getfullargspec(f)
	defaults_min= len(spec.args) - (len(spec.defaults) if spec.defaults!=None else 0)
	args_min= 1 if len(spec.args)>0 and spec.args[0]=="self" else 0
	logm(f"CACHE MEMO WRAP {name} a={args_min} d={defaults_min}")
	def fw(*args, **kwargs):
		eargs= []
		for i,k in enumerate(spec.args):
			if i>=args_min:
				eargs.append( args[i] if i<len(args) else kwargs.get(k, spec.defaults[i-defaults_min] if i>=  defaults_min else None) )

		return (onCall(f, args, kwargs, name, eargs) if onCall!=None else f(*args,**kwargs))

	return fw

def wrap_memo(f, fnameFormater= None):
	def wrap_memo_onCall(f, args, kwargs, name, eargs):
		fname= fnameFormater(name, eargs) if fnameFormater!=None else (name+'.'+ser_json(eargs)[1:-1])
		return memo(fname, lambda: f(*args, **kwargs))

	logm(f"CACHE MEMO WRAP FUNC {f}")
	return wrap(f, wrap_memo_onCall)

def wrap_memo_class(c, method_re= r'', fnameFormater=None):
	for n, v in inspect.getmembers(c):
		if callable(v) and re.match(method_re, n):
			try: 
				setattr(c, n, wrap_memo(v, fnameFormater))
			except Exception as ex:
				logm(f"CACHE MEMO WRAP CLASS EX {ex}")
				pass


