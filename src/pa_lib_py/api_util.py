from contextlib import contextmanager
import gzip
import re
from time import time, sleep
import os

from .util import ser_json, ser_json_r, fname_safe, ensure_dir, get_file_json, set_file_json
from .cfg import cfg_for
from pa_lib_py.logging import logm

CFG_MEMO_DIR= cfg_for("CACHE_MEMO_DIR", "/var/cache/memo" )
ensure_dir(CFG_MEMO_DIR)

CFG_API_STATE_DIR= cfg_for("API_STATE_DIR", "/var/run/api" )
ensure_dir(CFG_API_STATE_DIR)

WAIT_MIN_ABSOLUTE_S= 10 #U: como minimo esperamos un minuto entre llamadas para cualquier plataforma
USAGE_MAX= 40 #U: maximo % de utilizacion de lo que nos dan por hora


def usageAndWaitTimeItemsFromHeaders(headers):
	keepLessThan100 = []
	minWaitTime = []
	for k,v in headers.items():
		keepLessThan100 = keepLessThan100 + re.findall(r'"(call_count|total_cputime|total_time|.*?util_pct)"\s*:\s*(\d+)', v)
		minWaitTime = minWaitTime + re.findall(r'"(estimated_time_to_regain_access)"\s*:\s*(\d+)', v)
	return (keepLessThan100, minWaitTime)

def usageAndWaitTimeFromHeaders(headers):
	(keepLessThan100Items, minWaitTimeItems)= usageAndWaitTimeItemsFromHeaders(headers)
	usage = max([0] + [float(x[1]) for x in keepLessThan100Items])
	wait_min = max([0] + [float(x[1]) for x in minWaitTimeItems])
	return (usage, wait_min)

ProviderStats = {}
@contextmanager
def provider_stats(provider, dontSave=False):
	fpath = CFG_API_STATE_DIR+"/"+provider+".json"
	stats = ProviderStats.get(provider, get_file_json(fpath, default={}) )
	ProviderStats[provider]= stats
	try:
		yield stats
	finally:
		if dontSave!=False:
			set_file_json(fpath, ProviderStats[provider])

def calcOpenTimeToKeepAPIHappy(provider, task, headers=None, ex_s=None): #A: se llama DESPUES de una tarea
	with provider_stats(provider) as stats:
		(usage, wait_min_h) = usageAndWaitTimeFromHeaders(headers) if headers else (1,0)
		over_usage = max(0, usage - USAGE_MAX)
		wait_bc_usage = 60 * 60 * over_usage / 100 #A: para reestablecer el maximo por hora
		wait_bc_ex = 60 * 60 if ex_s != None else 0 #A: si hubo excepcion esperamos mucho para que no nos baneen
		wait_min = max(WAIT_MIN_ABSOLUTE_S, wait_min_h, wait_bc_usage, wait_bc_ex)
		open_t = time()+ wait_min
		stats_dt = time() - stats.get("open_t",0) if stats.get("open_t",0)>0 else '?'
		logm("API stats", provider=provider, wait_min=wait_min, over_usage=over_usage, usage=usage, dt= stats_dt, task=stats.get("task","?"))
		
		ProviderStats[provider]= { 'open_t': open_t, 'task': task }

def sleepToKeepAPIHappy(provider, task):
	with provider_stats(provider) as stats:
		wait_t= max(0, stats.get('open_t',0) -time())
		if wait_t>0:
			logm("API sleep", provider=provider, wait_t=wait_t)
			sleep(wait_t)

"""
H= {'Content-Encoding': 'gzip', 'ETag': '"c128883f0abe97210e902094ec33ed768b3d8e32"', 'Content-Type': 'application/json; charset=UTF-8', 'Vary': 'Origin, Accept-Encoding', 'x-business-use-case-usage': '{"750530335844724":[{"type":"ads_management","call_count":19,"total_cputime":5,"total_time":4,"estimated_time_to_regain_access":10},{"type":"ads_insights","call_count":1,"total_cputime":3,"total_time":3,"estimated_time_to_regain_access":0}]}', 'x-fb-rlafr': '0', 'x-fb-ads-insights-throttle': '{"app_id_util_pct": 0.00,"acc_id_util_pct": 0.00}', 'Access-Control-Allow-Origin': '*', 'facebook-api-version': 'v12.0', 'Strict-Transport-Security': 'max-age=15552000; preload', 'Pragma': 'no-cache', 'Cache-Control': 'private, no-cache, no-store, must-revalidate', 'Expires': 'Sat, 01 Jan 2000 00:00:00 GMT', 'x-fb-request-id': 'AaePYqXMptkoPl2qh1siWSd', 'x-fb-trace-id': 'FTUzNOWPP8Y', 'x-fb-rev': '1005031602', 'X-FB-Debug': '7h13M/u4Hcl+va096XKdhAHuBRynDLzk6A5BSWPcY+8gbdnlpMPSEKNU1ggnq/k3E3LSNihi04Jj9Xv0+QQ+dQ==', 'Date': 'Sun, 06 Feb 2022 16:29:30 GMT', 'Priority': 'u=3,i', 'Alt-Svc': 'h3=":443"; ma=3600, h3-29=":443"; ma=3600', 'Connection': 'keep-alive', 'Content-Length': '3828'}

calcOpenTimeToKeepAPIHappy('facebook','paso1',H)
t0= time()
sleepToKeepAPIHappy('facebook','paso2')
print(time()-t0)
"""

class MaxRowsEx(Exception): pass

def facebook_cursor_each(task, init_tunk, eachrow_f, max_rows= 55, eachrow_map_f= None, cleanup_tunk=None):
	sleepToKeepAPIHappy("facebook", task)
	try:
		cursor = init_tunk()
	
		cnt= 0
		lenLast= 0
		for row in cursor:
			if len(cursor)> lenLast: #A: leimos una pagina nueva
				calcOpenTimeToKeepAPIHappy("facebook", task+"_page",cursor.headers()) #A: actualizamos timers en la API
			lenLast= len(cursor)

			eachrow_f( eachrow_map_f(row) if callable(eachrow_map_f) else row)	

			cnt= cnt + 1
			if cnt > max_rows:
				logm(type_="ERR",msg="API facebook_cursor_eachWithMemo MAX_ROWS reached",max_rows=max_rows,task=task)
				raise MaxRowsEx
				break #XXX:avisar

			if len(cursor)==0 and not getattr(cursor,"_finished_iteration", cnt % 50 == 0): #A: la proxima cargamos otra pagina
				#VER: https://github.com/facebook/facebook-python-business-sdk/blob/5ca91fab03ca2d9473d6937e469e5c87ca289206/facebook_business/api.py#L854
				sleepToKeepAPIHappy("facebook", task+"_page")  #A: antes de la proxima llamada
	except MaxRowsEx:
		pass
	except Exception as ex:
		#VER: https://github.com/facebook/facebook-python-business-sdk/blob/5ca91fab03ca2d9473d6937e469e5c87ca289206/facebook_business/exceptions.py#L95
		ex_s = str(ex).lower()
		if "rate" in ex_s or "limit" in ex_s or "many" in ex_s or "wait" in ex_s:
			h = getattr(ex, 'http_headers', None)
			headers = h() if callable(h) else None

			calcOpenTimeToKeepAPIHappy('facebook', task, headers, ex_s)

		if callable(cleanup_tunk):
			cleanup_tunk()

		raise ex	

	if callable(cleanup_tunk):
		cleanup_tunk()

def google_ads_cursor_each(task, init_tunk, eachrow_f, max_rows= 55, eachrow_map_f= None, cleanup_tunk=None):
	sleepToKeepAPIHappy("google", task)
	try:
		cursor = init_tunk()
		
		cnt= 0
		lenLast= 0
		for page in cursor:
			calcOpenTimeToKeepAPIHappy("google", task+"_page") #A: actualizamos timers en la API

			for row in page.results:
				eachrow_f( eachrow_map_f(row) if callable(eachrow_map_f) else row)	

				cnt= cnt + 1
				if cnt > max_rows:
					logm(type_="ERR",msg="API ads_cursor_each MAX_ROWS reached",max_rows=max_rows,task=task)
					raise MaxRowsEx
					break

			sleepToKeepAPIHappy("google", task+"_page")  #A: antes de la proxima llamada

	except MaxRowsEx:
		pass
	except Exception as ex:
		#XXX:excepciones google?
		ex_s = str(ex).lower()
		if "rate" in ex_s or "limit" in ex_s or "many" in ex_s or "wait" in ex_s:
			h = getattr(ex, 'http_headers', None)
			headers = h() if callable(h) else None

			calcOpenTimeToKeepAPIHappy('google', task, headers, ex_s)

		if callable(cleanup_tunk):
			cleanup_tunk()
	
		raise ex	

	if callable(cleanup_tunk):
		cleanup_tunk()


def google_analytics_cursor_each(task, page_f, eachrow_f, max_rows= 55, eachrow_map_f= None, cleanup_tunk=None):
	cnt= 0
	next_page_token = ''

	try:
		while next_page_token is not None:
			next_page_token=None #DFLT

			sleepToKeepAPIHappy("google", task)
			response = page_f(next_page_token)
	
			calcOpenTimeToKeepAPIHappy("google", task+"_page") #A: actualizamos timers en la API

			report = response.get('reports', [])
			if not report:
					return

			for row in report[0].get('data', {}).get('rows', []):
				eachrow_f( eachrow_map_f(row) if callable(eachrow_map_f) else row )
				cnt= cnt + 1
				if cnt > max_rows:
					logm(type_="ERR",msg="API google_analytics_cursor_each MAX_ROWS reached",max_rows=max_rows,task=task)
					raise MaxRowsEx
					break

			next_page_token = report[0].get('nextPageToken', None)

	except MaxRowsEx:
		pass
	except Exception as ex:
		calcOpenTimeToKeepAPIHappy("google", task+"_page",ex_s=getattr(ex,"content",str(ex))) #A: actualizamos timers en la API

		if callable(cleanup_tunk):
			cleanup_tunk()
	
		raise ex	

	if callable(cleanup_tunk):
		cleanup_tunk()

	
def google_dv360_cursor_each(task, init_tunk, eachrow_f, max_rows= 55, eachrow_map_f= None, cleanup_tunk=None):
	sleepToKeepAPIHappy("google", task)
	try:
		cursor = init_tunk()

		cnt= 0
		for row in cursor:
			eachrow_f( eachrow_map_f(row) if callable(eachrow_map_f) else row )
			cnt= cnt + 1
			if cnt > max_rows:
				logm(type_="ERR",msg="API google_dv360_cursor_each MAX_ROWS reached",max_rows=max_rows,task=task)
				raise MaxRowsEx
				break

	except MaxRowsEx:
		pass
	except Exception as ex:
		#XXX:excepciones google?
		ex_s = str(ex).lower()
		if "rate" in ex_s or "limit" in ex_s or "many" in ex_s or "wait" in ex_s:
			h = getattr(ex, 'http_headers', None)
			headers = h() if callable(h) else None

			calcOpenTimeToKeepAPIHappy('google', task, headers, ex_s)

		if callable(cleanup_tunk):
			cleanup_tunk()

		raise ex	
	
	if callable(cleanup_tunk):
		cleanup_tunk()

#XXX:mover a memo
def any_cursor_eachWithMemo(cursor_each_f, task, init_tunk, eachrow_f, memo_fname, max_rows= 55, eachrow_map_f= None, cleanup_tunk=None):
	memo_path= CFG_MEMO_DIR+"/"+fname_safe(memo_fname)
	#XXX:logm
	try:
		with gzip.open(memo_fname,"rt", encoding='utf-8') as fin:
			for l in fin:
				try:
					eachrow_f( ser_json_r( l ))	
				except Exception as ex:
					logm(type_="ERR",msg="API cursor_eachWithMemo writing {ex}", task=task, fname=memo_fname)
					os.remove(memo_fname)	
					raise ex

			return #A: terminamos de procesar
	except FileNotFoundError:
		pass

	#A: no existia archivo memo
	with gzip.open(memo_path+".tmp","wt", encoding='utf-8') as fout:
		def write_and_proc_row(row):
			fout.write( (ser_json(row)+"\n") )
			eachrow_f(row)

		cursor_each_f(
			task,
			init_tunk,
			write_and_proc_row,
			max_rows = max_rows,
			eachrow_map_f = eachrow_map_f,
			cleanup_tunk = cleanup_tunk,
		)	

		os.rename(memo_path+".tmp", memo_path)


def facebook_cursor_eachWithMemo(task, init_tunk, eachrow_f, memo_fname, max_rows= 55, eachrow_map_f= None, cleanup_tunk=None):
	return any_cursor_eachWithMemo(facebook_cursor_each, task, init_tunk, eachrow_f, memo_fname, max_rows, eachrow_map_f, cleanup_tunk)

def google_ads_cursor_eachWithMemo(task, init_tunk, eachrow_f, memo_fname, max_rows= 55, eachrow_map_f= None, cleanup_tunk=None):
	return any_cursor_eachWithMemo(google_ads_cursor_each, task, init_tunk, eachrow_f, memo_fname, max_rows, eachrow_map_f, cleanup_tunk)

def google_analytics_cursor_eachWithMemo(task, page_f, eachrow_f, memo_fname, max_rows= 55, eachrow_map_f= None, cleanup_tunk=None):
	return any_cursor_eachWithMemo(google_analytics_cursor_each, task, page_f, eachrow_f, memo_fname, max_rows, eachrow_map_f, cleanup_tunk)

def google_dv360_cursor_eachWithMemo(task, init_tunk, eachrow_f, memo_fname, max_rows= 55, eachrow_map_f= None, cleanup_tunk=None):
	return any_cursor_eachWithMemo(google_dv360_cursor_each, task, init_tunk, eachrow_f, memo_fname, max_rows, eachrow_map_f, cleanup_tunk)

