#FROM: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#advanced-usage-with-scopes
from passlib.context import CryptContext
from sqlmodel import SQLModel, Field, Column, String, select
from util.db_cx_async import save_instance
from sqlalchemy.exc import NoResultFound

class User(SQLModel): 
	username: str = Field(default=None, primary_key=True)
	email: str | None = None
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

EMU_PASS = get_password_hash('xtestuser secreto'); #XXX:EMU
#TEST: 
print(EMU_PASS)

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

async def set_user_password(user: User, new_password: str, wantsCreate: False, db_session): #U: set pass, create if needed #SEC: don't expose to UI without validation!
	thisUserInDb= None #DFLT
	try:
		thisUserInDb= await get_user(user.username, db_session)
	except NoResultFound as ex:
		if not wantsCreate:
			raise ex
		else:
			thisUserInDb= UserInDB(**user.dict())

	thisUserInDb.hashed_password= get_password_hash(f"{user.username} {new_password}")
	await save_instance(thisUserInDb, db_session)
