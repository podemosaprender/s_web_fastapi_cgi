import os
import re
import glob
import gzip
import json
import multiprocessing
import hashlib

CFG= {} #A: global para configuracion

#XXX:eliminar
APP_DIR= os.path.dirname(os.path.abspath(__file__))
CFG_out_dir= "/MUST_FAIL" #APP_DIR+'/../data'
CFG_data_dir= "/MUST_FAIL" #APP_DIR+'/../data'

NOT_FOUND= {} #U: id unico para comparar con is

#S:
def ser_json_fmt(x):
	return (x.isoformat() if hasattr(x,'isoformat') else str(x))

def ser_json(o, pretty=False): 
	return json.dumps(o, default=ser_json_fmt, separators=None if pretty else (',', ':') )

def ser_json_r(s):	
	return json.loads(s)

def fname_safe(s):
	s_clean= re.sub(r'[^0-9a-zA-Z\.,"\' -]', lambda m: f"_{hex(ord(m.group(0)))[2:]}", s)
	if len(s_clean)>68: #XXX:CFG
		h= hashlib.md5("hola".encode('utf-8')).hexdigest()
		s_clean= s_clean[0:68]+h
	return s_clean

#S: fs
def ensure_dir(path):
	os.makedirs(path,exist_ok= True)

def get_file(fname, compressed= None, default= None):
	compressed= fname[-3:]=='.gz' if compressed==None and len(fname)>3 else compressed

	try:
		if compressed:
			with gzip.open(fname,'rt', encoding='utf-8') as f:
				return f.read()
		else:
			with open(fname,'rt') as f:
				return f.read()
	except FileNotFoundError as ex:
		if default != None:
			return default
		else:
			raise ex

def set_file(fname, data, compressed= None):
	compressed= fname[-3:]=='.gz' if compressed==None and len(fname)>3 else compressed

	if compressed:
		with gzip.open(fname, 'wt', encoding='utf-8') as fout:
			fout.write(data)
	else:
		with open(fname, 'wt') as fout:
			fout.write(data)

def get_file_json(fname, compressed=None, default=None):
	s= get_file(fname, compressed=compressed,default=NOT_FOUND if default!=None else None)
	return ser_json_r(s) if s!=NOT_FOUND else default

def set_file_json(fname, data, compressed=None):
	set_file( fname, ser_json(data), compressed)

#S: fs

def set_env(k,v, overwrite= True):
	if overwrite or os.environ.get(k) is None:
		os.environ[k]= str(v) #A: python espera solo strings

def dict_to_env(aDict, overwrite= True):
	if aDict!= None:
		for k in aDict.keys():
			set_env(k, aDict[k], overwrite)

def json_to_env(fname= '.env', overwrite= True):
	d= get_file_json(fname)
	dict_to_env(d, overwrite)
	return d
		

############################################################
#S: deprecated
def read_file(fname, prefix_dir=CFG_data_dir, compressed= None): #DEPRECATED
	compressed= fname[-3:]=='.gz' if compressed==None and len(fname)>3 else compressed

	if compressed:
		with gzip.open(prefix_dir+'/'+fname,'r') as f:
			return f.read().decode('utf-8')
	else:
		with open(prefix_dir+'/'+fname,'rt') as f:
			return f.read()


def write_file(data,fname, compressed= None): #DEPRECATED
	compressed= fname[-3:]=='.gz' if compressed==None and len(fname)>3 else compressed

	if compressed:
		with gzip.open(+fname, 'w') as fout:
			fout.write(data.encode('utf-8'))
	else:
		with open(fname, 'wt') as fout:
			fout.write(data)

def write_json(data,fname, compressed= None, ext= None):
	ext = (".json" if compressed==None else ".json.gz") if ext == None else ext
	write_file( ser_json(data), fname+ext, compressed=compressed)

def read_json(fname, prefix_dir=CFG_data_dir, compressed= None, ext= '.json.gz'):
	fname= fname+ext
	r = json.loads( read_file(fname, prefix_dir, compressed) )
	return r

def read_gzip(fname):
	with gzip.open(fname,'rt') as f:
		return f.read()


