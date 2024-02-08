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

#SEE: https://sqlmodel.tiangolo.com/tutorial/fastapi/simple-hero-api/#create-heroes-path-operation
#XXX: add routes for this app models