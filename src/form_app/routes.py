import json
import re

from fastapi import APIRouter, Depends, Request
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import RedirectResponse, StreamingResponse, HTMLResponse

from util.logging import logm
from util.db_cx_async import db_session, engine, save_instance
from util.db_cx_async import db_expand_moredata,db_expand_moredata_cols, db_read_any
from util.fastapi import DbSessionT, RefererAuthorizedT
from form_app.models import AnyForm, Entities, keys_for_validator

router= APIRouter()

@router.get("/data/")
async def read_data(db_session: DbSessionT, fmt: str="json", entity: str="any"):
	columns= None #DFLT
	more_data_idx= None
	a_select= select(AnyForm) #DFLT
	entity_cls= Entities.get(entity,None)
	if not entity_cls is None:
		(columns, more_data_idx)= db_expand_moredata_cols(keys_for_validator(AnyForm), keys_for_validator(entity_cls))
		a_select= a_select.where(AnyForm.entity	== entity)

	logm("read_data",entity_cls=entity_cls,columns=columns)
	return await db_read_any(a_select, fmt, db_session, mapf= db_expand_moredata, mapf_data= more_data_idx, columns=columns)

#SEE: https://stackoverflow.com/questions/74009210/how-to-create-a-fastapi-endpoint-that-can-accept-either-form-or-json-body
#SEE: https://fastapi.tiangolo.com/advanced/using-request-directly/
#SEE: https://www.starlette.io/requests/
@router.post("/asform/")
async def save_asform(req: Request, referer_data: RefererAuthorizedT, db_session: DbSessionT):
	error_msg= 'unknown' #DFLT fail
	dont_redirect= False #DFLT redirect
	url_mal= "/"
	try:
		form= await req.form()
		dont_redirect= form.get('o-o-form-dont-redirect',False) 
		url_bien = form.get("o-o-form-url-ok","/static/si_salio_bien.html")
		url_mal = form.get("o-o-form-url-error","/static/si_salio_mal.html")
		entity_name = form.get('o-o-form-entity','any') #XXX:include in authorization?
		#DBG: print("dont_redirect", dont_redirect)

		if referer_data.is_authorized: 
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
					site= referer_data.referer_host, referer= referer_data.referer_host, 
					entity= entity_name,
					more_data= json.dumps(data),
				), 
				db_session
			)

			if dont_redirect: 
				return HTMLResponse("ok") 
			return RedirectResponse(url_bien,status_code=303) #A: 303=see other, GET

	except Exception as ex:
		#DBG: print(ex)
		error_msg= str(ex)
	#A: something went wrong
	if dont_redirect: 
		return HTMLResponse("error "+error_msg)
	return RedirectResponse(url_mal,status_code=303) #A: 303=see other, GET

	
