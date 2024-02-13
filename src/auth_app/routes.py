#S: web
#FROM: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#advanced-usage-with-scopes

from typing import Annotated

from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from util.db_cx_async import db_session, engine, save_instance

from .models import User, authenticate_user
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

