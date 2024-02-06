#S: WEB
from util.logging import logm
from util.cfg import cfg_init, cfg_for
cfg_init() #A: other modules may depend

from importlib import import_module
APPS= cfg_for('APPS',[]) #XXX:auto discover
logm("WEB",APPS=APPS)
APPS_ROUTERS= {an_app:import_module(an_app+".routes") for an_app in APPS } 

#A: all models registered in metadata
from util.db_cx_async import db_init, db_session

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles 

import os

@asynccontextmanager
async def lifespan(app: FastAPI):
	await db_init()	
	logm("DB_INIT DONE")
	yield

app = FastAPI(root_path= cfg_for("ROOT_PATH",""), lifespan=lifespan)

AUTHORIZED_ORIGINS = cfg_for("AUTHORIZED_ORIGINS", [
	"http://localhost:8000", "http://127.0.0.1:8000",
])

#S: CORS {
app.add_middleware(
    CORSMiddleware,
    allow_origins= AUTHORIZED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#S: CORS }

app.mount("/static", StaticFiles(directory="static"), name="static") #XXX:CFG

for k,routes in APPS_ROUTERS.items():
	app.include_router(routes.router)


#XXX:to util
if __name__=="__main__":
	import asyncio
	from a2wsgi import ASGIMiddleware
	from fastapi import FastAPI
	from wsgiref.handlers import CGIHandler
	wsgi_application = ASGIMiddleware(app) #A provide it as wsgi application
	CGIHandler().run(wsgi_application) #A: use wsgi handler to run as cgi
