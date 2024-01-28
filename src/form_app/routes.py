from form_app.models import AnyForm, Entities, keys_for_validator
from util.db_cx_async import db_session, engine, save_instance
from util.cfg import cfg_for
from util.csviter import CSVIter
from util.logging import logm

from fastapi import APIRouter, Depends, Request
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import RedirectResponse, StreamingResponse, HTMLResponse

import json
import re

router= APIRouter()
AUTHORIZED_ORIGINS = cfg_for("AUTHORIZED_ORIGINS",[])

async def read_any(a_select, fmt: str, db_session: AsyncSession, mapf= None, mapf_data= None, columns= None):
		if (fmt=="csv"):
			async with engine.begin() as cx:
				results = await cx.execute(a_select) #A: not typed
				columns= results.keys() if columns is None else columns

				return StreamingResponse( CSVIter(results, mapf= mapf, mapf_data= mapf_data, columns=columns), media_type="text/csv" )
		else:
			results = await db_session.exec(a_select) #A: typed!
			return results.all()

def expand_moredata(kv_or_arr, columns, more_data_idx):
	if type(kv_or_arr)==dict:
		if 'more_data' in kv:
			kv={ **kv, **json.loads(kv['more_data']) }
			kv.pop('more_data',None)
		return kv	
	else:
		try:
			json_str= kv_or_arr[more_data_idx]
			return list(kv_or_arr[:more_data_idx])+list(kv_or_arr[(more_data_idx+1):])+list(json.loads(json_str).values())
		except Exception as ex:
			logm("expand_moredata",columns=columns,ex=ex)
			pass

	return kv_or_arr #DFTL, unchanged

def expand_moredata_cols(columns, expanded):
	idx= list(columns).index('more_data')
	return list(columns[:idx])+list(columns[(idx+1):])+list(expanded), idx

@router.get("/data/")
async def read_data(fmt: str="json", entity: str="any", db_session: AsyncSession = Depends(db_session)):
	columns= None #DFLT
	more_data_idx= None
	a_select= select(AnyForm) #DFLT
	entity_cls= Entities.get(entity,None)
	if not entity_cls is None:
		(columns, more_data_idx)= expand_moredata_cols(keys_for_validator(AnyForm), keys_for_validator(entity_cls))
		a_select= a_select.where(AnyForm.entity	== entity)

	logm("read_data",entity_cls=entity_cls,columns=columns)
	return await read_any(a_select, fmt, db_session, mapf= expand_moredata, mapf_data= more_data_idx, columns=columns)

#SEE: https://stackoverflow.com/questions/74009210/how-to-create-a-fastapi-endpoint-that-can-accept-either-form-or-json-body
#SEE: https://fastapi.tiangolo.com/advanced/using-request-directly/
#SEE: https://www.starlette.io/requests/
@router.post("/asform/")
async def save_asform(req: Request, db_session: AsyncSession = Depends(db_session)):
	error_msg= 'unknown' #DFLT fail
	dont_redirect= False #DFLT redirect
	url_mal= "/"
	try:
		#XXX:LIB as middleware? {
		referer = req.headers.get('referer','')
		#DBG: print("referer", referer);
		is_authorized= False #DFLT
		referer_host= 'NO_HOST'
		referer_host_match = re.match(r'(https?://([^/]+))', referer)
		if not referer_host_match is None:
			referer_hostfull = referer_host_match.group(1)
			referer_host= referer_host_match.group(2)
			is_authorized= referer_hostfull in AUTHORIZED_ORIGINS
		#XXX:LIB as middleware? }

		#DBG: print(f"referer isAuthorized={is_authorized} {referer_host} {referer}")
		form= await req.form()
		dont_redirect= form.get('o-o-form-dont-redirect',False) 
		url_bien = form.get("o-o-form-url-ok","/static/si_salio_bien.html")
		url_mal = form.get("o-o-form-url-error","/static/si_salio_mal.html")
		entity_name = form.get('o-o-form-entity','any') #XXX:include in authorization?
		#DBG: print("dont_redirect", dont_redirect)

		if is_authorized: 
			validator= Entities.get(entity_name, None)
			if not validator is None:
				data= { k: form.get(k, None) for k in keys_for_validator(validator) }
				obj= validator.model_validate(data, strict=True) #A: raise on error
			else:
				data= { k:form.get(k) for k in form.keys() if not k.startswith("o-o-form-") }
			#DBG: print("ASFORM", data);

			#A: si algo estaba mal lanzo excepcion, OjO! validar bien todos los inputs con tipos o a mano
			await save_instance(
				AnyForm( 
					site= referer_host, referer= referer, 
					entity= entity_name,
					more_data= json.dumps(data),
				), 
				db_session
			)

			if dont_redirect: 
				return HTMLResponse("ok") 
			return RedirectResponse(url_bien,status_code=303) #A: 303=see other, GET

	except Exception as ex:
		print(ex)
		error_msg= str(ex)

	#A: something went wrong
	if dont_redirect: 
		return HTMLResponse("error "+error_msg)
	return RedirectResponse(url_mal,status_code=303) #A: 303=see other, GET

	
