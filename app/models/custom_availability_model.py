from sqlalchemy import Column,Integer,String,ForeignKey,Date,Time,Boolean,UniqueConstraint
from app.core.database import Base
from sqlalchemy.orm import relationship


class CustomAvailability(Base):
    __tablename__="customavailability"

    id=Column(Integer,primary_key=True,nullable=False)

    doctor_id=Column(Integer,ForeignKey("doctor_profiles.doctor_id"),nullable=False)

    date = Column(Date, nullable=False)

    start_time = Column(Time, nullable=True)

    end_time = Column(Time, nullable=True)

    slot_duration = Column(Integer, nullable=True)

    is_available = Column(Boolean, default=True)

    doctor=relationship(
        "Doctor",
        back_populates="custom_availability"
    )

__table_args__ = (
    UniqueConstraint(
        "doctor_id",
        "date",
        name="uq_doctor_date"
    ),
)