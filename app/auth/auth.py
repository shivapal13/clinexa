from fastapi import FastAPI,HTTPException,status,APIRouter,Depends,Response
from app.schemas import userSchema
from app.models import user
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.password_hashing import hash_password
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from app.core import password_hashing,security


router=APIRouter(
    tags=["UserRegistration"]
)



@router.post("/register",status_code=status.HTTP_201_CREATED,response_model=userSchema.UserResponse)
def CreateUser(user_data:userSchema.UserRegister,db:Session=Depends(get_db)):

    hashed_password=hash_password(user_data.password)
    
    new_user=user.User(

        name=user_data.name,
        email=user_data.email,
        password=hashed_password,
        role=user_data.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/login",status_code=status.HTTP_200_OK)
def LoginUser(user_credentials:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
   user_data=db.query(user.User).filter(user.User.email==user_credentials.username).first()

   if not user_data:
       raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Invalid credentials")
   
   if not password_hashing.verify_password(user_credentials.password,user_data.password):
       raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="invalid credentials")
   
   access_token=security.create_access_token(data={"user_id":user_data.id})
   return {"access_token":access_token,"token_type":"bearer"}

       



