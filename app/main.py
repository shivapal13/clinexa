from fastapi import FastAPI
from app.core.database import Base,engine
from app.routes import router
from fastapi.middleware.cors import CORSMiddleware
from app.core.limiter import limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

app=FastAPI()

app.state.limiter=limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

app.add_middleware(SlowAPIMiddleware)

origins=[
    "http://127.0.0.1:5500",
    "https://clinexa-pauo.onrender.com"
]

@app.get("/")
def testfunc():
    return {"message":"Clinexa is working"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(router.api_router)