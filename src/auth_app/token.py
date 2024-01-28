from typing import Annotated

from fastapi import Depends, HTTPException, status
from .token_no_db import get_token_data, oauth2_scheme
from .models import User, get_user

#S: validate
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)
	token_data= await get_token_data(token)
	user = get_user(username= token_data.username)
	if user is None:
		raise credentials_exception
	return user

async def get_current_active_user(
	current_user: Annotated[User, Depends(get_current_user)]
):
	if current_user.disabled:
		raise HTTPException(status_code=400, detail="Inactive user")
	return current_user


