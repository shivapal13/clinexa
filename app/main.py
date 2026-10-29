from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.routes import router
from fastapi.middleware.cors import CORSMiddleware
from app.core.limiter import limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
import logging

logger = logging.getLogger("clinexa")

app = FastAPI(
    title="Clinexa Healthcare API",
    description="Backend API for Doctor-Patient appointment scheduling and medical records.",
    version="1.0.0",
)

app.state.limiter = limiter

# Rate limiting handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ---------------------------------------------------------------------------
# Global Exception Handlers for Robust Error Handling
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Format request validation errors (Pydantic / path / query / body)
    into a clean, predictable response.
    """
    formatted_errors = []
    for error in exc.errors():
        loc = " -> ".join(str(l) for l in error.get("loc", []))
        formatted_errors.append({
            "field": loc,
            "message": error.get("msg", "Invalid value"),
            "type": error.get("type", "value_error"),
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed",
            "errors": formatted_errors,
        },
    )


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    """
    Handle database unique or foreign key constraint collisions that escape
    endpoint-level handling, preventing raw 500 errors.
    """
    logger.warning("Database IntegrityError at %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "A database integrity conflict occurred (duplicate entry or invalid reference)."},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handle database operational errors (disconnects, timeouts, deadlocks).
    """
    logger.error("Database operational error at %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database service is temporarily unavailable. Please try again later."},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler to ensure internal server errors are logged
    and masked from the client rather than leaking sensitive tracebacks.
    """
    logger.error("Unhandled server exception at %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact support."},
    )


app.add_middleware(SlowAPIMiddleware)

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://clinexa-pauo.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "Clinexa API"}


app.include_router(router.api_router)
