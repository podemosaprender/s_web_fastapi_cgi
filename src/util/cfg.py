#INFO: minimas dependencias para que otros modulos lean su configuracion

from .util import json_to_env #U: para cargar config via json
from pathlib import Path
import os
import json
import re

from .logging import logm

BASE_DIR_ = Path(__file__).resolve().parent.parent #U: la raiz del proyecto
ENV_FNAME_= os.getenv('ENV','.env')
ENV_BASEDIR_= Path(ENV_FNAME_).parent
CFG_ = "NOT_LOADED"

NOT_FOUND= {} #U: un id unico para comparar con is

def cfg_init(from_fname=None, base_dir= None, reload=False): #U: init
	global CFG_, BASE_DIR_, ENV_FNAME_
	if CFG_=="NOT_LOADED" or reload:
		if base_dir!=None:
			BASE_DIR_ = base_dir
		if from_fname!=None:
			ENV_FNAME_= from_fname
			ENV_BASEDIR_= Path(ENV_FNAME_).parent

		logm(f'CFG Reading env from {ENV_FNAME_} at {str(BASE_DIR_)}')
		CFG_= json_to_env(ENV_FNAME_,str(BASE_DIR_))
		try:
			CFG_= json_to_env(ENV_FNAME_,str(BASE_DIR_))
			if CFG_==None:
				logm(f'CFG Reading env from {ENV_FNAME_} at {str(BASE_DIR_)} EMPTY', t="ERR")
				exit(1)
		except Exception as ex:
			logm(f'CFG Reading env from {ENV_FNAME_} at {str(BASE_DIR_)} {ex}', t="ERR")
			exit(1)


def cfg_for(k, dflt=None, paths= None, no_base= False, may_be_empty=False, read_file=False): #U: SOLAMENTE 
	global CFG_, BASE_DIR_

	r= None

	if k=="BASE_DIR":
		r= str(BASE_DIR_)
	elif paths==None:
		r= CFG_.get(k, dflt) 

	if r==None and not may_be_empty and paths!=None:
		for p in paths:
			v = CFG_.get(p + "/" + k, NOT_FOUND)
			if not v is NOT_FOUND:
				r=v	
				break

	if r==None and not no_base:
		r= CFG_.get(k, dflt)

	if r==None:
		r= dflt

	if not r is None and read_file and r.startswith('FILE:'):
		fname= r[5:]
		fname= re.sub(r'^\$ENV',str(ENV_BASEDIR_),fname)
		fname= re.sub(r'^\$BASE',str(BASE_DIR_),fname)
		with open(fname,'rt') as f:
			r= f.read()
	
	if r==None and not may_be_empty:
		raise Exception(f"CFG {k} EMPTY in file {ENV_FNAME_} {paths}") 

	return r
