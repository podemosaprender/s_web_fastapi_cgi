#!/usr/bin/env python

from a2wsgi import ASGIMiddleware
from fastapi import FastAPI
from wsgiref.handlers import CGIHandler

if False: #U: super simple
    app = FastAPI()

    @app.get("/")
    async def root():
        return {"message": "Hello World 👋"}
else:
    from app_simple import app

wsgi_application = ASGIMiddleware(app) #A provide it as wsgi application
CGIHandler().run(wsgi_application) #A: use wsgi handler to run as cgi
