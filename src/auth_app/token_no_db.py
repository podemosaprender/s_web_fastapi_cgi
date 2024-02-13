from datetime import datetime, timedelta, timezone
from typing import Annotated
from pydantic import BaseModel

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from util.cfg import cfg_for

# to get a string like this run:
# openssl rand -hex 32
ALGORITHM = cfg_for("AUTH_ALGORITHM","RSA")

SECRET_KEY = cfg_for("AUTH_SECRET_KEY", read_file=True)
PUBLIC_KEY = cfg_for("AUTH_PUBLIC_KEY", SECRET_KEY, read_file=True) #DFLT for symetic algorithms

ACCESS_TOKEN_EXPIRE_MINUTES = cfg_for("AUTH_EXPIRES_MINS",30)

class Token(BaseModel):
	access_token: str
	token_type: str

class TokenData(BaseModel):
	username: str | None = None

def create_access_token(data: dict, expires_delta: timedelta | None = None):
	to_encode = data.copy()

	expires_delta= expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
	expire = datetime.now(timezone.utc) + expires_delta

	to_encode.update({"exp": expire})
	encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	return encoded_jwt

#S: validate
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
async def get_token_data(token: Annotated[str, Depends(oauth2_scheme)]):
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		username: str = payload.get("sub")
		if username is None:
			raise credentials_exception
		token_data = TokenData(username=username)
	except JWTError:
		raise credentials_exception

	return token_data

