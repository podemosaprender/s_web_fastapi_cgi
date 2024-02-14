#FROM: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#advanced-usage-with-scopes
from typing import Optional, List
from passlib.context import CryptContext
from sqlmodel import SQLModel, Field, Column, String, select, delete
from util.db_cx_async import db_find, db_save, db_update
from sqlalchemy import UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy.exc import NoResultFound, IntegrityError

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

class AuthScope(SQLModel, table= True): #U: ej. @mauri/miservidorcito
	__table_args__ = (UniqueConstraint("name"), )

	id: Optional[int] = Field(default= None, primary_key=True)
	created_at: datetime = Field( default_factory=datetime.utcnow, )
	name: str = Field(default=None)
	allow_all: bool

class AuthScopeUser(SQLModel, table= True): #U: which users are allowed which scopes
	__table_args__ = (PrimaryKeyConstraint("authscope_id","username"),)
	created_at: datetime = Field( default_factory=datetime.utcnow, )
	authscope_id: Optional[int] = Field(default=None, foreign_key="authscope.id")
	username: Optional[str] = Field(default=None, foreign_key="user.username")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password): #U: console/admin only
	return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
	return pwd_context.verify(plain_password, hashed_password)

async def get_user(username: str, db_session, wantsCreate=False):
	return await db_find(UserInDB, dict(username=username), db_session, wantsCreate)	

async def authenticate_user(username: str, password: str, db_session):
	try:
		user = await get_user(username, db_session)
		if verify_password(f"{username} {password}", user.hashed_password):
			return user
	except NoResultFound as ex:
		pass	
	return false

async def update_user(username: str, new_values: dict, new_password: str, wantsCreate: False, db_session): #U: set pass, create if needed #SEC: don't expose to UI without validation!
	thisUserInDb= await db_update(UserInDB, dict(username=username), new_values, db_session, wantsCreate=True, wantsSave=False)
	thisUserInDb.hashed_password= get_password_hash(f"{username} {new_password}")
	return await db_save(thisUserInDb, db_session)

async def update_scope(active_user: UserInDB, scope_name: str, allow_all: bool, db_session, users_add: [], users_remove: [], wantsCreate: False): 
	#A: we are in a transaction, nothing will be saved until we commit

	if (scope_name.startswith( '@'+active_user.username+'/' )): #A: active user is allowed to edit this scope
		scope= await db_update(AuthScope, dict(name=scope_name), dict(allow_all=allow_all), db_session, wantsCreate=True, wantsSave=True)

		if len(users_remove)>0 :
			await db_session.exec( 
					delete( AuthScopeUser )
						.where( AuthScopeUser.authscope_id == scope.id )
						.where( AuthScopeUser.username.in_( users_remove ) )
			)
		#A: we removed usernames in the users_remove list

		existing= ( await db_session.exec( 
				select( AuthScopeUser.username )
					.where( AuthScopeUser.authscope_id == scope.id )
					.where( AuthScopeUser.username.in_( users_add ) )
			)).all()
		#A: existing is the list of usernames for this scope already in the db

		for uname in users_add:
			if not uname in existing:
				asu= AuthScopeUser(authscope_id= scope.id, username=uname)
				await db_save(asu, db_session)
		#A: new usernames in users_add were added to this scope

		await db_session.commit()

		return scope

	raise Exception("Unauthorized scope name")

async def validate_scopes_for_token(active_user: UserInDB, scopes: List[str], db_session): 
	existing= ( await db_session.exec( 
			select( AuthScope.name )
				.where( AuthScopeUser.authscope_id == AuthScope.id )
				.where( AuthScopeUser.username == active_user.username )
				.where( AuthScope.name.in_( scopes ) )
		)).all()
	#A: existing is the list of scopes authorized for this username
	not_existing= [s for s in scopes if not s in existing ]
	return existing, not_existing

