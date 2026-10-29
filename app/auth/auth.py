from fastapi import HTTPException, status, APIRouter, Depends, Request
from app.schemas import userSchema
from app.models import user
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.core.password_hashing import hash_password, verify_password
from fastapi.security import OAuth2PasswordRequestForm
from app.core import security
from app.core.limiter import limiter

router = APIRouter(tags=["UserRegistration"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=userSchema.UserResponse)
@limiter.limit("5/minute")
def CreateUser(
    request: Request,
    user_data: userSchema.UserRegister,
    db: Session = Depends(get_db),
):
    normalized_email = user_data.email.strip().lower()
    hashed_password = hash_password(user_data.password)

    new_user = user.User(
        name=user_data.name.strip(),
        email=normalized_email,
        password=hashed_password,
        role=user_data.role,  # Patient or Doctor
        is_admin=False,       # Admin accounts cannot self-register
        is_active=True,
    )

    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )

    db.refresh(new_user)
    return new_user


@router.post("/login", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
def LoginUser(
    request: Request,
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    normalized_email = user_credentials.username.strip().lower()
    user_data = (
        db.query(user.User).filter(user.User.email == normalized_email).first()
    )

    if not user_data or not verify_password(user_credentials.password, user_data.password):
        # Return 401 Unauthorized per HTTP standard
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    access_token = security.create_access_token(data={"user_id": user_data.id})
    return {"access_token": access_token, "token_type": "bearer"}
