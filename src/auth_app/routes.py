#S: web
#FROM: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#advanced-usage-with-scopes

from typing import Annotated

from fastapi import Depends, Body, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import NoResultFound
from util.db_cx_async import db_session

from .models import User, authenticate_user, update_scope
from .token_no_db import Token, create_access_token
from .token import get_current_active_user

router= APIRouter(prefix="/auth")

@router.post("/token")
async def login_for_access_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
	db_session: AsyncSession = Depends(db_session)
) -> Token:
	user = await authenticate_user(form_data.username, form_data.password, db_session)
	if not user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Bearer"},
		)
	access_token = create_access_token( data={"sub": user.username} )
	return Token(access_token=access_token, token_type="bearer")

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

#S: authorization }
