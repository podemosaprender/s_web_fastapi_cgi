#S: web
#FROM: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#advanced-usage-with-scopes

from typing import Annotated, Optional, List
import json

from fastapi import Depends, Form, Body, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import NoResultFound
from util.db_cx_async import db_session

from .models import User, authenticate_user, update_scope, AuthScopeUser, validate_scopes_for_token
from .token_no_db import Token, create_access_token
from .token import get_current_active_user, get_token_data_web

router= APIRouter(prefix="/auth")

@router.post("/token")
async def login_for_access_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
	extra: Annotated[Optional[str], Form()]= None,
	db_session: AsyncSession = Depends(db_session)
) -> Token:
	user = await authenticate_user(form_data.username, form_data.password, db_session)
	if not user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Bearer"},
		)

	scopes= form_data.scopes #U: space separated #XXX:validate
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

	access_token = create_access_token( data={"sub": user.username,"scope": scopes_auth, "not_auth": extra_dict} )
	return Token(access_token=access_token, token_type="bearer")

@router.get("/token/data/")
async def read_token_data(
	token_data: Annotated[User, Depends(get_token_data_web)]
):
	return token_data

@router.get("/users/me/", response_model=User)
async def read_users_me(
	current_user: Annotated[User, Depends(get_current_active_user)]
):
	return current_user

#S: authorization {
@router.post("/scope/{scope_name:path}")
async def scope_edit_or_create(
	scope_name: str,	
	current_user: Annotated[User, Depends(get_current_active_user)],
	allow_all: Annotated[bool, Body(embed=True)]=False,
	db_session: AsyncSession = Depends(db_session)
):
	if not current_user: #XXX:genealize
		raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED,)

	try:
		return await update_scope( current_user, scope_name, allow_all, db_session, wantsCreate=True)
	except Exception as ex:
		raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED,)

@router.put("/scope/{scope_name:path}")
async def scope_edit_or_create(
	scope_name: str,	
	current_user: Annotated[User, Depends(get_current_active_user)],
	allow_all: Annotated[bool, Body(embed=True)]=False,
	users_add: Annotated[List[str], Body(embed=True)]=[],
	users_remove: Annotated[List[str], Body(embed=True)]=[],
	db_session: AsyncSession = Depends(db_session)
):
	if not current_user: #XXX:genealize
		raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED,)

	try:
		return await update_scope( current_user, scope_name, allow_all, db_session, users_add=users_add, users_remove=users_remove, wantsCreate=True)
	except Exception as ex:
		raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED,)

#S: authorization }
