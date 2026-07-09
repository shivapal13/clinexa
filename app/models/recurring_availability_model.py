from sqlalchemy import Column,String,Integer,ForeignKey,Boolean,Date,Time
from app.core.database import Base
import enum 
from sqlalchemy import Enum
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship

class DayOfWeek(str,enum.Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"



class RecurringAvailability(Base):
    __tablename__="recurringavailability"


    id=Column(Integer,primary_key=True,nullable=False)

    doctor_id=Column(Integer,ForeignKey("doctor_profiles.doctor_id"),nullable=False)

    day_of_week=Column(Enum(DayOfWeek),nullable=False)

    start_time=Column(Time,nullable=False)

    end_time=Column(Time,nullable=False)

    slot_duration=Column(Integer,nullable=False)

    is_active=Column(Boolean,default=True)

    doctor = relationship(
    "Doctor",
    back_populates="recurring_availability"
)

__table_args__ = (
    UniqueConstraint(
        "doctor_id",
        "day_of_week",
        name="uq_doctor_day"
    ),
)