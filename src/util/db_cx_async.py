#S: DB Connection, async
from .cfg import cfg_for
from .logging import logm

from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker

sqlite_file_name = cfg_for("DB_SQLITE_PATH","database.db") #A: if DB_URL not defined
db_url = cfg_for("DB_URL", f"sqlite+aiosqlite:///{sqlite_file_name}")
logm("DB init connecting to", db_url=db_url)
engine= AsyncEngine( create_engine(db_url, echo=False, future=True) )
session_async= sessionmaker( engine, class_=AsyncSession, expire_on_commit=False)

async def db_init() -> None:
	async with engine.begin() as conn:
		await conn.run_sync(SQLModel.metadata.create_all)
		logm("db_init DONE")

async def db_session() -> AsyncSession:
	async with session_async() as session:
		yield session

async def save_instance(instance, session):
	session.add(instance)
	await session.commit()
	await session.refresh(instance)

