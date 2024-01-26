#S: DB 
from typing import Optional
from pydantic import constr, EmailStr


from sqlmodel import String, create_engine, select
from sqlmodel import SQLModel, Field, Session, Column, String
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker

from datetime import datetime
import os

sqlite_file_name = os.environ.get("DB_SQLITE_PATH","database.db") #A: if DB_URL not defined
db_url = os.environ.get("DB_URL", f"sqlite+aiosqlite:///{sqlite_file_name}")

#S: Models

def keys_for_validator(validator):
	return list(validator.__annotations__.keys())

Entities= {} #U: name -> class

TstrNoVacia= constr(strip_whitespace=True, min_length=2) #A: type alias

class AnyForm(SQLModel, table=True): #U: Base for anything we store
	id: Optional[int] = Field(default=None, primary_key=True)
	created_at: datetime = Field( default_factory=datetime.utcnow, )
	site: str
	referer: str
	entity: str #U: specialized validator
	more_data: str #U: serialized as json

class ContactForm(SQLModel): #U: a specialized model/validator
	email: EmailStr= Field(sa_column=Column(String, index=True))
	name: TstrNoVacia
	subject: TstrNoVacia
	message: TstrNoVacia

Entities['contact']= ContactForm

#S: Connection
engine= AsyncEngine( create_engine(db_url, echo=False, future=True) )

async def db_init() -> None:
	async with engine.begin() as conn:
		await conn.run_sync(SQLModel.metadata.create_all)

async def db_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

async def save_instance(instance, session):
	session.add(instance)
	await session.commit()
	await session.refresh(instance)

#S: WEB
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles 
from fastapi.responses import RedirectResponse, StreamingResponse, HTMLResponse
from typing import Annotated
from util.csviter import CSVIter

import json
import re

app = FastAPI(root_path=os.environ.get("ROOT_PATH",None))

AUTHORIZED_ORIGINS = [
	"http://localhost:8000", "http://127.0.0.1:8000",
	"https://api1.o-o.fyi", "http://api1.o-o.fyi",
	"https://sebasego.github.io",
	"https://ventum.dev", "http://ventum.dev",
]


#S: CORS {
app.add_middleware(
    CORSMiddleware,
    allow_origins= AUTHORIZED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#S: CORS }

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def on_startup():
	await db_init()	

async def read_any(a_select, fmt: str, db_session: AsyncSession, mapf= None, columns= None):
		if (fmt=="csv"):
			async with engine.begin() as cx:
				results = await cx.execute(a_select) #A: not typed
				columns= results.keys() if columns is None else columns

				return StreamingResponse( CSVIter(results, mapf= mapf, columns=columns), media_type="text/csv" )
		else:
			results = await db_session.exec(a_select) #A: typed!
			return results.all()

def expand_moredata(kv_or_arr, columns):
	if type(kv_or_arr)==dict:
		if 'more_data' in kv:
			kv={ **kv, **json.loads(kv['more_data']) }
			kv.pop('more_data',None)
		return kv	
	else:
		try:
			idx= list(columns).index('more_data')
			json_str= kv_or_arr[idx]
			return list(kv_or_arr[:idx])+list(kv_or_arr[(idx+1):])+list(json.loads(json_str).values())
		except Exception as ex:
			#DBG: print("expand_moredata",columns,ex)
			pass

	return kv_or_arr #DFTL, unchanged

def expand_moredata_cols(columns, expanded):
	idx= list(columns).index('more_data')
	return list(columns[:idx])+list(columns[(idx+1):])+list(expanded)

@app.get("/data/")
async def read_data(fmt: str="json", entity: str="any", db_session: AsyncSession = Depends(db_session)):
	columns= None #DFLT
	a_select= select(AnyForm) #DFLT
	entity_cls= Entities.get(entity,None)
	if not entity_cls is None:
		columns= expand_moredata_cols(keys_for_validator(AnyForm), keys_for_validator(entity_cls))
		a_select= a_select.where(AnyForm.entity	== entity)

	return await read_any(a_select, fmt, db_session, mapf= expand_moredata, columns=columns)

#SEE: https://stackoverflow.com/questions/74009210/how-to-create-a-fastapi-endpoint-that-can-accept-either-form-or-json-body
#SEE: https://fastapi.tiangolo.com/advanced/using-request-directly/
#SEE: https://www.starlette.io/requests/
@app.post("/asform/")
async def save_asform(req: Request, db_session: AsyncSession = Depends(db_session)):
	error_msg= 'unknown' #DFLT fail
	dont_redirect= False #DFLT redirect
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

		if is_authorized: 
			#DBG: print(f"referer isAuthorized={is_authorized} {referer_host} {referer}")
			form= await req.form()
			dont_redirect= form.get('o-o-form-dont-redirect',False) 
			url_bien = form.get("o-o-form-url-ok","/static/si_salio_bien.html")
			url_mal = form.get("o-o-form-url-error","/static/si_salio_mal.html")
			entity_name = form.get('o-o-form-entity','any') #XXX:include in authorization?
			#DBG: print("dont_redirect", dont_redirect)
			
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

	
