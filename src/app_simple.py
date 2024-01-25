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

class Hero(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	name: TstrNoVacia= Field(index=True)
	secret_name: TstrNoVacia
	age: Optional[int] = Field(default=None, index=True)

class Contacto(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	email: EmailStr= Field(sa_column=Column(String, index=True))
	name: TstrNoVacia
	subject: TstrNoVacia
	message: TstrNoVacia

engine= AsyncEngine( create_engine(db_url, echo=True, future=True) )

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
from fastapi.staticfiles import StaticFiles 
from fastapi.responses import RedirectResponse, StreamingResponse
from typing import Annotated
from util.csviter import CSVIter

app = FastAPI(root_path=os.environ.get("ROOT_PATH",None))
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

@app.post("/heroes/")
async def create_hero(hero: Hero, db_session: AsyncSession = Depends(db_session)):
	await save_instance(hero, db_session)
	return hero

@app.get("/heroes/")
async def read_heroes(fmt: str="json", db_session: AsyncSession = Depends(db_session)):
	return await read_any(Hero, fmt, db_session)

#SEE: https://stackoverflow.com/questions/74009210/how-to-create-a-fastapi-endpoint-that-can-accept-either-form-or-json-body
#SEE: https://fastapi.tiangolo.com/advanced/using-request-directly/
#SEE: https://www.starlette.io/requests/
@app.post("/heroes_form/")
async def create_hero_form(req: Request, db_session: AsyncSession = Depends(db_session)):
	try:
		form= await req.form()
		hero= Hero.model_validate(dict(
			id= int(form.get('id')),
			name= form.get('name'),
			secret_name= form.get('secret_name'),
			age= int(form.get('age')),
		), strict=True) #A: raise on error
		#A: si algo estaba mal lanzo excepcion, OjO! validar bien todos los inputs con tipos o a mano
		await save_instance(hero, db_session)
		return RedirectResponse("/static/si_salio_bien.html",status_code=303) #A: 303=see other, GET
	except:
		return RedirectResponse("/static/si_salio_mal.html",status_code=303) #A: 303=see other, GET

@app.get("/contacto/")
async def read_contactos(fmt: str="json", db_session: AsyncSession = Depends(db_session)):
	return await read_any(Contacto, fmt, db_session)

@app.post("/contacto_form/")
async def contacto_form(req: Request, db_session: AsyncSession = Depends(db_session)):
	try:
		form= await req.form()
		contacto= Contacto.model_validate(dict(
			email= form.get('email'),
			name= form.get('name'),
			subject= form.get('subject'),
			message= form.get('message'),
		), strict=True) #A: raise on error
		#A: si algo estaba mal lanzo excepcion, OjO! validar bien todos los inputs con tipos o a mano
		await save_instance(contacto, db_session)
		return RedirectResponse("/static/si_salio_bien.html",status_code=303) #A: 303=see other, GET
	except Exception as ex:
		print(ex)
		return RedirectResponse("/static/si_salio_mal.html",status_code=303) #A: 303=see other, GET

	
