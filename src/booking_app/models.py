#S: Models

from typing import Optional
from pydantic import constr, EmailStr
from sqlmodel import SQLModel, Field, Column, String

from datetime import datetime

TstrNoVacia= constr(strip_whitespace=True, min_length=1) #A: type alias

class Resource(): #U: A room, vehicle, etc
	id: Optional[int] = Field(default=None, primary_key=True)
	pass #XXX: implement

#SEE: https://sqlmodel.tiangolo.com/tutorial/relationship-attributes/define-relationships-attributes/#declare-relationship-attributes
class Availability(): #U: Time, capacity, etc. When a resource will be available
	id: Optional[int] = Field(default=None, primary_key=True)
	resource_id: Optional[int] = Field(default=None, foreign_key="resource.id") 
	from_ts: datetime
	to_ts: datetime
	pax_max: int
	luggage_max: int
	pax_used: int #A: we keep it in this table to make it easier and ensure consistency
	luggage_used: int
	pass #XXX: implement

class Booking(): #U: as requested by the client
	id: Optional[int] = Field(default=None, primary_key=True)
	pass #XXX: status=pending, confirmed AND all relevant data pax, contact info, pick up time, location

"""
passenger goes to the page, select from Availability
passenger fills booking data
system discounts from Availability, registers Booking
operator checks Bookings with status=pending, and confirms
provider (taxi driver) checks Bookings with status=confirmed (report for the next 24h)
"""




