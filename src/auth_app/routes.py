#S: web
#FROM: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#advanced-usage-with-scopes

from typing import Annotated, Optional, List
from typing_extensions import Doc
import json

from fastapi import Depends, Form, Body, Header, APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import NoResultFound
from util.db_cx_async import db_session
from util.fastapi import DbSessionT, RefererT

from .models import User, authenticate_user, update_scope, AuthScope, validate_scopes_for_token
from .token_no_db import Token, TokenData, TokenDataT, token_create, HTTPExceptionUnauthorized
from .token import RequestUserT 

router= APIRouter(prefix="/auth")

@router.post("/token")
async def login_for_access_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
	db_session: DbSessionT,
	extra: Annotated[Optional[str], Form()]= None,
	referer: RefererT= None,
) -> Token:
	user = await authenticate_user(form_data.username, form_data.password, db_session)
	if not user:
		raise HTTPExceptionUnauthorized

	scopes= form_data.scopes #U: space separated 
	(scopes_auth, scopes_not_auth)= await validate_scopes_for_token(user, scopes, db_session)
	
	extra_dict= {}
	if not extra is None and len(extra)>0:
		try:
			d= json.loads(extra)
			if type(d)==dict:
				extra_dict= d
			else:
				extra_dict['data']= d
		except:
			extra_dict['data']= extra

	extra_dict['scope']= extra_dict.get('scope',[])+ scopes_not_auth

	access_token = token_create( data={"sub": user.username,"scope": scopes_auth, "not_auth": extra_dict} )

	if form_data.grant_type=="password":
		return Token(access_token=access_token, token_type="bearer")
	else:
		return RedirectResponse(url='http://mauriciocap.com/?code=123456780aa', status_code=status.HTTP_307_TEMPORARY_REDIRECT) #XXX:use redirect_uri from request, filter by client_id, etc.

@router.get("/token/data/")
async def read_token_data(
	token_data: TokenDataT
) -> TokenData:
	return token_data

@router.get("/users/me/", response_model=User)
async def read_users_me(
	request_user: RequestUserT
):
	return request_user

#S: authorization {
@router.put("/scope/{scope_name:path}")
async def scope_edit_or_create(
	scope_name: str,	
	request_user: RequestUserT,
	db_session: DbSessionT,
	allow_all: Annotated[bool, Body(embed=True)]=False,
	users_add: Annotated[List[str], Body(embed=True)]=[],
	users_remove: Annotated[List[str], Body(embed=True)]=[],
) -> AuthScope:
	if not request_user: #XXX:genealize
		raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED,)

	try:
		return await update_scope( request_user, scope_name, allow_all, db_session, users_add=users_add, users_remove=users_remove, wantsCreate=True)
	except Exception as ex:
		raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED,)

#S: authorization }
