#S: Models

from typing import Optional
from pydantic import constr, EmailStr
from sqlmodel import SQLModel, Field, Column, String

from datetime import datetime

def keys_for_validator(validator):
	return list(validator.__annotations__.keys())

Entities= {} #U: name -> class

TstrNoVacia= constr(strip_whitespace=True, min_length=1) #A: type alias

class AnyForm(SQLModel, table=True): #U: Base for anything we store
	id: Optional[int] = Field(default=None, primary_key=True)
	created_at: datetime = Field( default_factory=datetime.utcnow, )
	site: str
	referer: str
	entity: str #U: specialized validator
	more_data: str #U: serialized as json

class ContactForm(SQLModel): #U: a specialized model/validator
	email: EmailStr= Field(sa_column=Column(String, index=True))
	name: TstrNoVacia
	subject: TstrNoVacia
	message: TstrNoVacia

Entities['contact']= ContactForm



