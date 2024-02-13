#FROM: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#advanced-usage-with-scopes
from passlib.context import CryptContext
from sqlmodel import SQLModel, Field, Column, String, select
from util.db_cx_async import save_instance
from sqlalchemy.exc import NoResultFound

from datetime import datetime

class User(SQLModel): 
	username: str = Field(default=None, primary_key=True)
	email: str | None = None
	created_at: datetime = Field( default_factory=datetime.utcnow, )
	full_name: str | None = None
	disabled: bool | None = None

class UserInDB(User, table = True): 
	__tablename__="user"

	hashed_password: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password): #U: console/admin only
	return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
	return pwd_context.verify(plain_password, hashed_password)

async def get_user(username: str, db_session):
	res= await db_session.exec(
		select(UserInDB).where(UserInDB.username == username)
	)
	return res.one()

async def authenticate_user(username: str, password: str, db_session):
	user = await get_user(username, db_session)
	if not user:
		return False
	if not verify_password(f"{username} {password}", user.hashed_password):
		return False
	return user

async def update_user(username: str, new_values: dict, new_password: str, wantsCreate: False, db_session): #U: set pass, create if needed #SEC: don't expose to UI without validation!
	thisUserInDb= None #DFLT
	try:
		thisUserInDb= await get_user(username, db_session)
	except NoResultFound as ex:
		if not wantsCreate:
			raise ex
		else:
			thisUserInDb= UserInDB(username=username)

	for (k,v) in new_values.items():
		setattr(thisUserInDb, k, v)

	if not new_password is None:
		thisUserInDb.hashed_password= get_password_hash(f"{username} {new_password}")

	await save_instance(thisUserInDb, db_session)
	await db_session.refresh(thisUserInDb)
	return thisUserInDb
