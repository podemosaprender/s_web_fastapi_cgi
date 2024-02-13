#FROM: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#advanced-usage-with-scopes
from passlib.context import CryptContext
from sqlmodel import SQLModel, Field, Column, String, select


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

EMU_PASS = get_password_hash('secreto'); #XXX:EMU
#TEST: print(EMU_PASS)


async def get_user(username: str, db_session):
	res= await db_session.exec(
		select(UserInDB).where(UserInDB.username == username)
	)
	return res.one()

async def authenticate_user(username: str, password: str, db_session):
	user = await get_user(username, db_session)
	if not user:
		return False
	if not verify_password(password, user.hashed_password):
		return False
	return user


