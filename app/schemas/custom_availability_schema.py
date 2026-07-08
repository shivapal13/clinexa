from pydantic import BaseModel
from datetime import date,time

class CreateCustomAvailability(BaseModel):

    start_date:date
    start_time:time |None=None
    end_time:time |None=None
    slot_duration:int |None=None
    is_available:bool =True
    class Config:
        from_attributes=True
