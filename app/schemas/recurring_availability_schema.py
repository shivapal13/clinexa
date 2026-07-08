from pydantic import BaseModel
from datetime import time
import enum
from sqlalchemy import Enum

class DayOfWeek(str, enum.Enum):

    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class RecurringAvailabilityCreate(BaseModel):
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    slot_duration: int

    class Config:
        from_attributes=True

class RecurringAvailabilityResponse(BaseModel):
    id: int
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    slot_duration: int

    class Config:
        from_attributes = True

class RecurringAvailabilityUpdate(BaseModel):
    day_of_week: DayOfWeek |None=None
    start_time: time|None=None
    end_time: time|None=None
    slot_duration: int|None=None
    class Config:
        from_attributes = True
