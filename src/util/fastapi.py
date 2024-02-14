from typing import Annotated
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends, HTTPException
from util.db_cx_async import db_session

DbSessionT= Annotated[AsyncSession, Depends(db_session)]


