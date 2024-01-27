#S: Connection
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker

import os

sqlite_file_name = os.environ.get("DB_SQLITE_PATH","database.db") #A: if DB_URL not defined
db_url = os.environ.get("DB_URL", f"sqlite+aiosqlite:///{sqlite_file_name}")
engine= AsyncEngine( create_engine(db_url, echo=False, future=True) )

async def db_init() -> None:
	async with engine.begin() as conn:
		await conn.run_sync(SQLModel.metadata.create_all)

async def db_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session



