from typing import Annotated

from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends, HTTPException, status
from util.db_cx_async import db_session

from .token_no_db import TokenDataT, HTTPExceptionUnauthorized
from .models import User, get_user

#S: validate
async def request_user(
	token_data: TokenDataT,
	db_session: AsyncSession = Depends(db_session)
):
	user = await get_user(token_data.username, db_session)
	if user is None:
		raise HTTPExceptionUnauthorized()

	if user.disabled:
		raise HTTPException(status_code=400, detail="Inactive user")

	return user

RequestUserT= Annotated[ User, Depends(request_user) ]
