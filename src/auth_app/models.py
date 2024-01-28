#FROM: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#advanced-usage-with-scopes
from passlib.context import CryptContext
from pydantic import BaseModel

class User(BaseModel):
	username: str
	email: str | None = None
	full_name: str | None = None
	disabled: bool | None = None

class UserInDB(User):
	hashed_password: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password): #U: console/admin only
	return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
	return pwd_context.verify(plain_password, hashed_password)

EMU_PASS = get_password_hash('secreto'); #XXX:EMU
EMU_DB = { #XXX:EMU
	"johndoe": {
		"username": "johndoe",
		"full_name": "John Doe",
		"email": "johndoe@example.com",
		"hashed_password": EMU_PASS,
		"disabled": False,
	}
}

def get_user(username: str):
	if username in EMU_DB:
		user_dict = EMU_DB[username]
		return UserInDB(**user_dict)

def authenticate_user(username: str, password: str):
	user = get_user(username)
	if not user:
		return False
	if not verify_password(password, user.hashed_password):
		return False
	return user


