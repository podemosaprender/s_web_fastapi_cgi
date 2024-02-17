#INFO: OAuth2 token, DB independent code to use e.g. where JWT validations is enough

from datetime import datetime, timedelta, timezone
from typing import Annotated, List
from pydantic import BaseModel

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from util.cfg import cfg_for

ALGORITHM = cfg_for("AUTH_ALGORITHM","RSA")
SECRET_KEY = cfg_for("AUTH_SECRET_KEY", "", read_file=True)
PUBLIC_KEY = cfg_for("AUTH_PUBLIC_KEY", SECRET_KEY, read_file=True) #DFLT for symetic algorithms

ACCESS_TOKEN_EXPIRE_MINUTES = cfg_for("AUTH_EXPIRES_MINS",30)

class Token(BaseModel):
	access_token: str
	token_type: str

class TokenData(BaseModel):
	username: str | None = None
	scopes: List[str]
	payload: dict

def token_create(data: dict, expires_delta: timedelta | None = None):
	to_encode = data.copy()

	expires_delta= expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
	expire = datetime.now(timezone.utc) + expires_delta

	to_encode.update({"exp": expire})
	encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	return encoded_jwt

#S: validate
Oauth2Scheme= OAuth2PasswordBearer(tokenUrl="auth/token") #XXX:CFG #U: e.g. for SwaggerUI "Authorize" buton
TokenT= Annotated[str, Depends(Oauth2Scheme)] #U: def mifun(token: TokenT): ...

class HTTPExceptionUnauthorized(HTTPException):
	def __init__(self, **kwargs):
		super(HTTPExceptionUnauthorized, self).__init__(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Could not validate credentials",
			headers={"WWW-Authenticate": "Bearer"},
			**kwargs
		)

def token_data_novalidate_user(token: TokenT):
	try:
		#CGI: print("TK",token)
		return jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
	except JWTError as ex:
		#CGI: print("TK",token)
		pass #A: handled below	

	raise HTTPExceptionUnauthorized()

async def token_data(token: TokenT):
	try:
		payload = token_data_novalidate_user(token)
		username: str = payload.get("sub")
		if not username is None:
			return TokenData(username=username, scopes= payload.get('scope',[]), payload= payload)
	except JWTError as ex:
		pass #A: handled below

	raise HTTPExceptionUnauthorized()

TokenDataT= Annotated[TokenData, Depends(token_data)]
