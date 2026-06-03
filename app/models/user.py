from sqlalchemy import Column,String,Boolean,Integer,DateTime
from app.database import Base
from sqlalchemy.sql import func

class User(Base):
    __tablename__="users"

    id=Column(Integer,primary_key=True,nullable=False,unique=True)
    name=Column(String,nullable=False)
    email=Column(String,nullable=False,unique=True)
    password=Column(String,nullable=False)
    role=Column(String,nullable=False)
    is_active=Column(Boolean,default=True)
    is_created=Column(DateTime(timezone=True),server_default=func.now())