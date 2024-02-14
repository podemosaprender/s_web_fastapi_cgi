#S: DB Connection, async
from .cfg import cfg_for
from .logging import logm

from sqlmodel import SQLModel, create_engine, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoResultFound

sqlite_file_name = cfg_for("DB_SQLITE_PATH","database.db") #A: if DB_URL not defined
db_url = cfg_for("DB_URL", f"sqlite+aiosqlite:///{sqlite_file_name}")
logm("DB init connecting to", db_url=db_url)
engine= AsyncEngine( create_engine(db_url, echo=(cfg_for("DB_DBG","NO")=="YES"), future=True) )
session_async= sessionmaker( engine, class_=AsyncSession, expire_on_commit=False)

async def db_init() -> None:
	async with engine.begin() as conn:
		await conn.run_sync(SQLModel.metadata.create_all)
		logm("db_init DONE")

async def db_session() -> AsyncSession:
	async with session_async() as session:
		yield session

async def db_save(instance, db_session):
	db_session.add(instance)
	await db_session.commit()
	await db_session.refresh(instance)
	return instance

async def save_instance(instance, session): #DEPRECATED, use db_sabe
	return await db_save(instance, session)

async def db_find(cls, kv: dict, db_session, wantsCreate= False):
	inDb= None	
	q= [ ( getattr(cls, k) == v ) for (k,v) in kv.items() ]
	try:
		res= await db_session.exec( select(cls).where(*q) )
		inDb= res.one()
	except NoResultFound as ex:
		if not wantsCreate:
			raise ex
		else:
			inDb=	cls( **kv )

	return inDb

async def db_update(cls, key_kv: dict, new_values_kv: dict, db_session, wantsCreate= False, wantsSave= True):
	inDb= await db_find(cls, key_kv, db_session, wantsCreate)
	for (k,v) in new_values_kv.items():
		setattr(inDb, k, v)

	if wantsSave:
		return await db_save(inDb, db_session)

	return inDb
