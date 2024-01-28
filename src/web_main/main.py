#S: WEB
from util.cfg import cfg_init, cfg_for
cfg_init() #A: other modules may depend

from form_app.routes import router
from util.db_cx_async import db_init, db_session

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles 

import os

app = FastAPI(root_path= cfg_for("ROOT_PATH",""))

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

@app.on_event("startup")
async def on_startup():
	await db_init()	

app.include_router(router)
