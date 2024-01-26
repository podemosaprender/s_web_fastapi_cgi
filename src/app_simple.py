#S: DB 
from typing import Optional
from pydantic import constr, EmailStr

from sqlmodel import Field, Session, SQLModel, Column, String, create_engine, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker

import asyncio
import os

sqlite_file_name = os.environ.get("DB_SQLITE_PATH","database.db") #A: if DB_URL not defined
db_url = os.environ.get("DB_URL", f"sqlite+aiosqlite:///{sqlite_file_name}")

TstrNoVacia= constr(strip_whitespace=True, min_length=2) #A: type alias

class Contacto(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	email: EmailStr= Field(sa_column=Column(String, index=True))
	name: TstrNoVacia
	subject: TstrNoVacia
	message: TstrNoVacia

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

app = FastAPI(root_path=os.environ.get("ROOT_PATH",None))

#S: CORS {
origins = [
	"http://localhost:8000", "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#S: CORS }

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def on_startup():
	await db_init()	

async def read_any(cls, fmt: str, db_session: AsyncSession):
		if (fmt=="csv"):
			async with engine.begin() as cx:
				results = await cx.execute(select(cls)) #A: not typed
				return StreamingResponse( CSVIter(results, columns=results.keys()) )
		else:
			results = await db_session.exec(select(cls)) #A: typed!
			return results.all()

@app.get("/contacto/")
async def read_contactos(fmt: str="json", db_session: AsyncSession = Depends(db_session)):
	return await read_any(Contacto, fmt, db_session)

#SEE: https://stackoverflow.com/questions/74009210/how-to-create-a-fastapi-endpoint-that-can-accept-either-form-or-json-body
#SEE: https://fastapi.tiangolo.com/advanced/using-request-directly/
#SEE: https://www.starlette.io/requests/
@app.post("/contacto_form/")
async def contacto_form(req: Request, db_session: AsyncSession = Depends(db_session)):
	dontRedirect= False
	try:
		form= await req.form()
		dontRedirect= form.get('dontRedirect',False) 
		url_bien = form.get("url_bien","/static/si_salio_bien.html")
		url_mal = form.get("url_mal","/static/si_salio_mal.html")
		#DBG: print("dontRedirect", dontRedirect)

		contacto_data= dict(
			email= form.get('email'),
			name= form.get('name'),
			subject= form.get('subject'),
			message= form.get('message'),
		)
		#DBG: print("CONTACTO FORM", contacto_data);

		contacto= Contacto.model_validate(contacto_data, strict=True) #A: raise on error
		#A: si algo estaba mal lanzo excepcion, OjO! validar bien todos los inputs con tipos o a mano
		await save_instance(contacto, db_session)

		if dontRedirect: 
			return HTMLResponse("ok") 
		return RedirectResponse(url_bien,status_code=303) #A: 303=see other, GET
	except Exception as ex:
		print(ex)
		if dontRedirect: 
			return HTMLResponse("error "+str(ex)) 
		return RedirectResponse(url_mal,status_code=303) #A: 303=see other, GET

	
