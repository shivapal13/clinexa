from sqlalchemy.orm import session
from app.database import get_db
from app.schemas import userSchema
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime,timedelta,timezone
from jose import JWTError,jwt
from fastapi import Depends,HTTPException,status
from sqlalchemy.orm import Session
from app.models import user
from app.config import settings



SECRET_KEY=settings.SECRET_KEY
ALGORITHM=settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES=settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth_scheme=OAuth2PasswordBearer(tokenUrl='login')

def create_access_token(data:dict):
    to_encode=data.copy()
    expire=datetime.now(timezone.utc)+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp":expire})

    encode=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

    return encode
    

def verify_access_token(token:str,credentials_Exception):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])

        id:int=payload.get("user_id")

        if id is None:
            raise credentials_Exception
        
        token_data=userSchema.TokenData(id=id)
    except JWTError as e:
        raise credentials_Exception

    return token_data    

def get_current_user(token:str=Depends(oauth_scheme),db:Session=Depends(get_db)):

    credentials_Exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="could not validate credentials",
        headers={"WWW-Authenticate":"Bearer"}
    )

    token_data=verify_access_token(token,credentials_Exception)

    user_data=db.query(user.User).filter(user.User.id==token_data.id).first()

    if user_data is None:
        raise credentials_Exception

    return user_data

    