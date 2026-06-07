from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker,declarative_base
from sqlalchemy import create_engine,text
from app.config import settings

DATABASE_URL=settings.DATABASE_URL

if 'localhost' or 'host.docker.internal' in DATABASE_URL:
    engine=create_engine(DATABASE_URL)

else:
    engine=create_engine(
        DATABASE_URL,
        connect_args={"sslmode":"require"}
    )
SessionLocal=sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine
)

Base=declarative_base()

def get_db():
    db=SessionLocal()

    try:
        yield db
    finally:
        db.close()    