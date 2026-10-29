from app.core.database import get_db
from app.schemas import userSchema
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models import user
from app.core.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        return userSchema.TokenData(id=int(user_id))
    except (JWTError, ValueError, Exception):
        raise credentials_exception


def get_current_user(token: str = Depends(oauth_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_access_token(token, credentials_exception)
    user_data = db.query(user.User).filter(user.User.id == token_data.id).first()

    if user_data is None:
        raise credentials_exception

    if not user_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    return user_data


def is_admin_user(current_user: user.User) -> bool:
    """
    Check if a user has admin privileges.
    Requires is_admin=True in the database, OR explicitly matching configured ADMIN_EMAIL(S)
    along with an Admin or verified role.
    """
    if getattr(current_user, "is_admin", False):
        return True

    admin_emails = {
        e.strip().lower()
        for cfg in (settings.ADMIN_EMAILS, settings.ADMIN_EMAIL)
        for e in cfg.split(",")
        if e.strip()
    }
    
    if current_user.email.lower() in admin_emails and current_user.role == "Admin":
        return True

    return False


def get_admin_user(current_user: user.User = Depends(get_current_user)):
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return current_user
