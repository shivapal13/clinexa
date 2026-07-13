from fastapi import HTTPException,status,Depends,APIRouter,Response
from sqlalchemy.orm import Session
from app.schemas import doctor_schema
from app.core.database import get_db
from app.core import security
from app.models import doctor_model,user
from app.services import redis_service
router=APIRouter(
    prefix="/doctor/profile",
    tags=["DoctorProfile"]
)

@router.post("/",status_code=status.HTTP_201_CREATED)
def CreateDoctorProfile(doctor_data:doctor_schema.DoctorProfileCreate,
                        db:Session=Depends(get_db),
                        current_user=Depends(security.get_current_user)):
    
    if(current_user.role!="Doctor"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not allowed"
                            )
    
    existing_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if existing_profile is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Profile already exist")
    
    doctor=doctor_model.Doctor(
        user_id=current_user.id,
        specialisation=doctor_data.specialisation,
        experience=doctor_data.experience,
        fees=doctor_data.fees,
        city=doctor_data.city,
        bio=doctor_data.bio,
        hospital_name=doctor_data.hospital_name
    )

    db.add(doctor)
    db.commit()
    redis_service.delete_key(
        f"doctor:{current_user.id}"
    )
    db.refresh(doctor)

    return doctor

@router.get("/",status_code=status.HTTP_200_OK,response_model=doctor_schema.DoctorSearchResponse)
def GetDoctorProfile(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!="Doctor"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    cache_key=f"doctor:{current_user.id}"
    cache_doctor=redis_service.get_json(cache_key)

    if cache_doctor:
        return cache_doctor

    doctor_data=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor profile not found")
    
    doctor_response=doctor_schema.DoctorSearchResponse.model_validate(doctor_data).model_dump()

    redis_service.set_json(
        cache_key,
        doctor_response,
        ttl=300
    )
    
    return doctor_response


@router.patch("/",status_code=status.HTTP_200_OK)
def UpdateDoctorProfile(Update_data:doctor_schema.DoctorProfileUpdate,db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='Doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    doctor=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id)
    doctor_data=doctor.first()

    if doctor_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="profile not found")
    
    update_data=Update_data.model_dump(exclude_unset=True)
    
    for key,Value in update_data.items():
        setattr(doctor_data,key,Value)
    
    db.commit()
    redis_service.delete_key(
        f"doctor:{current_user.id}"
    )
    db.refresh(doctor_data)


    return doctor_data

@router.delete("/")
def DeleteDoctorProfile(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!="Doctor"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")

    doctor=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor is None:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,detail="Profile not found")
    
    db.delete(doctor)

    db.commit()
    redis_service.delete_key(
        f"doctor:{current_user.id}"
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
    
@router.get("/{id}",response_model=doctor_schema.DoctorSearchResponse)
def GetDoctorById(id:int,db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):
    
    if(current_user.role!='Patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    cache_key=f"doctor:{id}"
    cache_doctor=redis_service.get_json(cache_key)
    
    if cache_doctor:
        return cache_doctor
    
    doctor_data=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.doctor_id==id).first()

    if doctor_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")
    
    doctor_response=doctor_schema.DoctorSearchResponse.model_validate(doctor_data).model_dump()

    redis_service.set_json(
        cache_key,
        doctor_response,
        ttl=300
    )
    
    return doctor_response

@router.get("/search/specialisation/{specialisation}",response_model=list[doctor_schema.DoctorSearchResponse])
def SearchDoctorByName(specialisation:str,
                       db:Session=Depends(get_db),
                       current_user=Depends(security.get_current_user)):

    if(current_user.role!='Patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    doctor=db.query(doctor_model.Doctor).join(
        user.User,doctor_model.Doctor.user_id==user.User.id).filter(
        doctor_model.Doctor.specialisation.ilike(f"%{specialisation}%")
        ).all()

    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Not found")

    return doctor

@router.get("/search/name/{name}",response_model=list[doctor_schema.DoctorSearchResponse])
def SearchDoctorByName(name:str,
                       db:Session=Depends(get_db),
                       current_user=Depends(security.get_current_user)):

    if(current_user.role!='Patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    doctor=db.query(doctor_model.Doctor).join(
        user.User,doctor_model.Doctor.user_id==user.User.id).filter(
        user.User.name.ilike(f"%{name}%")
        ).all()

    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Not found")
    

    return doctor




    
