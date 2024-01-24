#S: DB 
from typing import Optional
from pydantic import constr
from sqlmodel import Field, Session, SQLModel, create_engine, select

TstrNoVacia= constr(strip_whitespace=True, min_length=2) #A: type alias

class Hero(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	name: TstrNoVacia= Field(index=True)
	secret_name: TstrNoVacia
	age: Optional[int] = Field(default=None, index=True)


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)

def create_db_and_tables():
	SQLModel.metadata.create_all(engine)

def save_hero(hero):
	with Session(engine) as session:
		session.add(hero)
		session.commit()
		session.refresh(hero)

#S: WEB
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles 
from fastapi.responses import RedirectResponse
from typing import Annotated

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def on_startup():
	create_db_and_tables()


@app.post("/heroes/")
def create_hero(hero: Hero):
	save_hero(hero)
	return hero


@app.get("/heroes/")
def read_heroes():
	with Session(engine) as session:
		heroes = session.exec(select(Hero)).all()
		return heroes

#SEE: https://stackoverflow.com/questions/74009210/how-to-create-a-fastapi-endpoint-that-can-accept-either-form-or-json-body
#SEE: https://fastapi.tiangolo.com/advanced/using-request-directly/
#SEE: https://www.starlette.io/requests/
@app.post("/heroes_form/")
async def create_hero_form(req: Request):
	try:
		form= await req.form()
		hero= Hero.model_validate(dict(
			id= int(form.get('id')),
			name= form.get('name'),
			secret_name= form.get('secret_name'),
			age= int(form.get('age')),
		), strict=True) #A: raise on error
		#A: si algo estaba mal lanzo excepcion, OjO! validar bien todos los inputs con tipos o a mano
		save_hero(hero)
		return RedirectResponse("/static/si_salio_bien.html",status_code=303) #A: 303=see other, GET
	except:
		return RedirectResponse("/static/si_salio_mal.html",status_code=303) #A: 303=see other, GET

	
