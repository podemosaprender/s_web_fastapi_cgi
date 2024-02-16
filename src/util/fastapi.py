from typing import Annotated
import urllib
import re


from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends, Form, Body, Header, HTTPException, status
from util.cfg import cfg_for
from util.db_cx_async import db_session

def enc_uri(s):
	return urllib.parse.quote_plus(s)

DbSessionT= Annotated[AsyncSession, Depends(db_session)]
RefererT= Annotated[str | None, Header()]

AUTHORIZED_ORIGINS = cfg_for("AUTHORIZED_ORIGINS",[])

class RefererData:
	referer_hostfull: str
	referer_host: str
	is_authorized: bool

def referer_data(referer: RefererT) -> RefererData:
	#DBG: print("referer", referer);
	r = RefererData()
	r.is_authorized= False #DFLT
	r.referer_host= 'NO_HOST'
	referer_host_match = re.match(r'(https?://([^/]+))', referer)
	if not referer_host_match is None:
		r.referer_hostfull = referer_host_match.group(1)
		r.referer_host= referer_host_match.group(2)
		r.is_authorized= r.referer_hostfull in AUTHORIZED_ORIGINS

	#DBG: print(f"referer isAuthorized={is_authorized} {referer_host} {referer}")
	return r

def referer_authorized(referer: RefererT):
	r= referer_data(referer)
	if not r.is_authorized:
		raise HTTPException(
			status= status.HTTP_401_UNAUTHORIZED
		)
	return r

RefererDataT= Annotated[RefererData, Depends(referer_data)]
RefererAuthorizedT= Annotated[RefererData, Depends(referer_authorized)]

HostT= Annotated[str, Header()]
