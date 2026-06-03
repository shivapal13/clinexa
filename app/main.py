from fastapi import FastAPI
from app.database import Base,engine
from app.routes import router




app=FastAPI()



app.include_router(router.api_router)