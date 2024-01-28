import logging
import threading
from inspect import isclass
from .debug import debug

LOGM_FORMAT = '%(asctime)s:%(process)d:%(message)s'
LOGM_FORMAT_THREAD = '%(asctime)s:%(process)d_%(my_thread_id)s:%(message)s'
LOG_DATEFMT= "%m%d.%H%M%S"

#S: inicializar, agregar info contextual
class ContextFilter(logging.Filter):
	def filter(self, record):
		record.my_thread_id = str(threading.current_thread().getName()).replace("Thread","")
		return True 

contextFilter= ContextFilter()
formatter= logging.Formatter(LOGM_FORMAT_THREAD, datefmt=LOG_DATEFMT)
formatter.patched= True

def patch_logger(l):
	global contextFilter
	global formatter
	if getattr(l,"patched",False)!=True:
		l.datefmt= LOG_DATEFMT
		if getattr(l,'addFilter',None)!=None:
			l.addFilter(contextFilter)
		if getattr(l,'setStyle',None)!=None:
			l.setStyle('%')
		if getattr(l,'formatter',None)!=None:
			l.formatter=formatter
		print(f"Logging patched {l}")

		l.patched= True

	if getattr(l,'handlers',None)!=None:
		for h in l.handlers:
			if getattr(h,"patched",False)!=True:
				h.formatter= formatter	
				h.filters= [contextFilter]

def init_logging():

	logging.captureWarnings(True)

	def monkey_patched_getLogger(self, key):
		result = self.old_getLogger(key)
		patch_logger(l)	
		return result

	logging.basicConfig(format=LOGM_FORMAT, datefmt=LOG_DATEFMT)
	#VER: https://docs.python.org/3/library/logging.html#logging.basicConfig

	logging.Logger.old_getLogger = logging.Logger.addHandler
	logging.Logger.getLogger = monkey_patched_getLogger
	
	for k, l in [ ("root", logging.Logger.root) ] + list( logging.Logger.manager.loggerDict.items() ):
		patch_logger(l)

init_logging()

#S: implementacion
LogLvlMax = 3 #U: usar set_logLvlMax para cambiar por sideEffects, este para logging.LogLvlMax>8 and llamada_que_harias_muchas_veces
LogLvlMaxObservers_ = [] #U: modulos que necesitan ej. registrar cosas para loguear como djongo_util

Loggers= {}

def getLogger(channel=""):
	lg = Loggers.get(channel)
	if lg == None:
		lg = logging.getLogger(channel)
		Loggers[channel]= lg

	patch_logger(lg)
	return lg

def onLogLvlMaxChange(f):
	LogLvlMaxObservers_.append(f)

def willLog(lvl, channel): #U: para modulos que necesitan activar/desactivar cosas
	if lvl>LogLvlMax:
		return False
	return getLogger(channel).hasHandlers()
	
def set_logLvlMax(n): #U: usar esta funcion por si hacen falta efectos colaterales
	LogLvlMax= n
	for f in LogLvlMaxObservers_:
		f()
	
def logm(m="LOG", ch="", t="DBG",l=1,ex=None,**kwargs):
	if l > LogLvlMax:
		return

	logger = getLogger(ch)
	#debug(globals(),locals())
	data = {}
	for k,v in kwargs.items():
		print(f"{k}=={type(k)}")
		data[k]= v(kwargs) if callable(v) and not isclass(v) else v #U: podes pasar una funcion o lambda para parametros costosos de computar, pero las clases no seran invocadas

	#U: logm(hola=20, mau="texto", fu=lambda a: a.get("hola",100)+30)

	m = f"{t}:{l}:{m}:{data}"
	log_f= logger.debug
	if l<1:
		log_f= logger.critical
	elif l<3:
		log_f= logger.error #U: usamos error como un numero, puede ser ej. que arranco el programa
	elif l<6:
		log_f= logger.warning #U: usamos como un numero, puede ser ej. que arranco el programa
	elif l<8:
		log_f= logger.info #U: usamos como un numero, puede ser ej. que conextamos a un servidor
	else:
		log_f= logger.debug #U: usamos error como un numero, puede ser ej. que arranco el programa

	log_f(m, exc_info=ex)

	#A: map de nuestro level 1=mas urgente, 9=mas verborragico a python 50=critico, 0=No loguear	
	#VER: https://docs.python.org/3/library/logging.html#logging-levels
	

