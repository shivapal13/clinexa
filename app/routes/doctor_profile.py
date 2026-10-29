from fastapi import HTTPException, status, Depends, APIRouter, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.schemas import doctor_schema
from app.core.database import get_db
from app.core import security
from app.models import doctor_model, user, appointment_model
from app.services import redis_service

router = APIRouter(prefix="/doctor/profile", tags=["DoctorProfile"])


@router.get("/admin/access", tags=["DoctorVerification"])
def GetDoctorAdminAccess(
    current_user=Depends(security.get_current_user),
):
    return {"is_admin": security.is_admin_user(current_user)}


@router.get(
    "/admin/accounts",
    response_model=list[doctor_schema.DoctorAccountForProfile],
    tags=["DoctorVerification"],
    dependencies=[Depends(security.get_admin_user)],
)
def GetDoctorsWithoutProfiles(
    db: Session = Depends(get_db),
):
    return (
        db.query(user.User)
        .outerjoin(
            doctor_model.Doctor,
            doctor_model.Doctor.user_id == user.User.id,
        )
        .filter(
            user.User.role == "Doctor",
            user.User.is_active.is_(True),
            doctor_model.Doctor.doctor_id.is_(None),
        )
        .order_by(user.User.name, user.User.id)
        .all()
    )


@router.post(
    "/admin/accounts/{user_id}/profile",
    status_code=status.HTTP_201_CREATED,
    response_model=doctor_schema.DoctorProfileResponse,
    tags=["DoctorVerification"],
    dependencies=[Depends(security.get_admin_user)],
)
def CreateDoctorProfileForAccount(
    user_id: int,
    doctor_data: doctor_schema.DoctorProfileCreate,
    db: Session = Depends(get_db),
):
    doctor_account = (
        db.query(user.User)
        .filter(
            user.User.id == user_id,
            user.User.role == "Doctor",
            user.User.is_active.is_(True),
        )
        .first()
    )
    if doctor_account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active doctor account not found",
        )

    existing_profile = (
        db.query(doctor_model.Doctor)
        .filter(doctor_model.Doctor.user_id == user_id)
        .first()
    )
    if existing_profile is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Doctor account already has a profile",
        )

    doctor = doctor_model.Doctor(
        user_id=user_id,
        specialisation=doctor_data.specialisation,
        experience=doctor_data.experience,
        fees=doctor_data.fees,
        city=doctor_data.city,
        bio=doctor_data.bio,
        hospital_name=doctor_data.hospital_name,
        license_number=doctor_data.license_number,
        verification_status="PENDING",
    )
    db.add(doctor)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Doctor account already has a profile",
        ) from exc

    db.refresh(doctor)
    return doctor


@router.get(
    "/admin/pending",
    response_model=list[doctor_schema.DoctorVerificationReview],
    tags=["DoctorVerification"],
    dependencies=[Depends(security.get_admin_user)],
)
def GetPendingDoctorReviews(
    db: Session = Depends(get_db),
):
    reviews = (
        db.query(doctor_model.Doctor, user.User)
        .join(user.User, doctor_model.Doctor.user_id == user.User.id)
        .filter(doctor_model.Doctor.verification_status == "PENDING")
        .order_by(doctor_model.Doctor.doctor_id)
        .all()
    )
    return [
        {
            "doctor_id": doctor.doctor_id,
            "doctor_name": account.name,
            "doctor_email": account.email,
            "specialisation": doctor.specialisation,
            "hospital_name": doctor.hospital_name,
            "city": doctor.city,
            "license_number": doctor.license_number,
            "verification_status": doctor.verification_status,
        }
        for doctor, account in reviews
    ]


@router.patch(
    "/admin/{doctor_id}/verification",
    response_model=doctor_schema.DoctorVerificationReview,
    tags=["DoctorVerification"],
    dependencies=[Depends(security.get_admin_user)],
)
def ReviewDoctorProfile(
    doctor_id: int,
    decision: doctor_schema.DoctorVerificationUpdate,
    db: Session = Depends(get_db),
):
    review = (
        db.query(doctor_model.Doctor, user.User)
        .join(user.User, doctor_model.Doctor.user_id == user.User.id)
        .filter(doctor_model.Doctor.doctor_id == doctor_id)
        .first()
    )
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found",
        )

    doctor, account = review
    if decision.verification_status == "VERIFIED" and not doctor.license_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A professional license number is required before approval",
        )

    doctor.verification_status = decision.verification_status
    db.commit()
    redis_service.delete_key(f"doctor:profile:{doctor.doctor_id}")
    redis_service.delete_pattern(f"availability:doctor:{doctor.doctor_id}:*")
    db.refresh(doctor)

    return {
        "doctor_id": doctor.doctor_id,
        "doctor_name": account.name,
        "doctor_email": account.email,
        "specialisation": doctor.specialisation,
        "hospital_name": doctor.hospital_name,
        "city": doctor.city,
        "license_number": doctor.license_number,
        "verification_status": doctor.verification_status,
    }


# ---------------------------------------------------------------------------
# POST /doctor/profile/  — create profile for the authenticated doctor
# ---------------------------------------------------------------------------
@router.post("/", status_code=status.HTTP_201_CREATED)
def CreateDoctorProfile(
    doctor_data: doctor_schema.DoctorProfileCreate,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    existing_profile = (
        db.query(doctor_model.Doctor)
        .filter(doctor_model.Doctor.user_id == current_user.id)
        .first()
    )
    if existing_profile is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Profile already exists"
        )

    doctor = doctor_model.Doctor(
        user_id=current_user.id,
        specialisation=doctor_data.specialisation,
        experience=doctor_data.experience,
        fees=doctor_data.fees,
        city=doctor_data.city,
        bio=doctor_data.bio,
        hospital_name=doctor_data.hospital_name,
        license_number=doctor_data.license_number.strip(),
        verification_status="PENDING",
    )

    db.add(doctor)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Doctor profile already exists for this account",
        ) from exc
    db.refresh(doctor)

    # FIX: use doctor_id (the PK) — not user_id — as the cache key so
    # GetDoctorById (which looks up by doctor_id) uses the same key namespace.
    redis_service.delete_key(f"doctor:profile:{doctor.doctor_id}")

    return doctor


# ---------------------------------------------------------------------------
# GET /doctor/profile/  — get own profile (doctor-facing)
# ---------------------------------------------------------------------------
@router.get("/", status_code=status.HTTP_200_OK, response_model=doctor_schema.DoctorProfileResponse)
def GetDoctorProfile(
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    doctor_data = (
        db.query(doctor_model.Doctor)
        .filter(doctor_model.Doctor.user_id == current_user.id)
        .first()
    )
    if doctor_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found"
        )

    return doctor_data


# ---------------------------------------------------------------------------
# PATCH /doctor/profile/  — update own profile
# ---------------------------------------------------------------------------
@router.patch("/", status_code=status.HTTP_200_OK)
def UpdateDoctorProfile(
    update_data: doctor_schema.DoctorProfileUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    doctor_data = (
        db.query(doctor_model.Doctor)
        .filter(doctor_model.Doctor.user_id == current_user.id)
        .first()
    )
    if doctor_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    changes = update_data.model_dump(exclude_unset=True)
    license_changed = False
    if "license_number" in changes:
        if changes["license_number"] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Professional license number cannot be removed",
            )
        license_changed = changes["license_number"] != doctor_data.license_number
        if license_changed:
            doctor_data.verification_status = "PENDING"

    for key, value in changes.items():
        setattr(doctor_data, key, value)

    db.commit()
    redis_service.delete_key(f"doctor:profile:{doctor_data.doctor_id}")
    if license_changed:
        redis_service.delete_pattern(
            f"availability:doctor:{doctor_data.doctor_id}:*"
        )
    db.refresh(doctor_data)

    return doctor_data


# ---------------------------------------------------------------------------
# DELETE /doctor/profile/  — delete own profile
# ---------------------------------------------------------------------------
@router.delete("/")
def DeleteDoctorProfile(
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    doctor = (
        db.query(doctor_model.Doctor)
        .filter(doctor_model.Doctor.user_id == current_user.id)
        .first()
    )
    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    has_appointments = (
        db.query(appointment_model.Appointment)
        .filter(appointment_model.Appointment.doctor_id == doctor.doctor_id)
        .first()
    )
    if has_appointments is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete doctor profile because active or historical appointments exist",
        )

    try:
        db.delete(doctor)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete doctor profile due to existing dependent records",
        )

    redis_service.delete_key(f"doctor:profile:{doctor.doctor_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# GET /doctor/profile/{id}  — patient looks up a doctor by doctor_id
# ---------------------------------------------------------------------------
@router.get("/{id}", response_model=doctor_schema.DoctorSearchResponse)
def GetDoctorById(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    # Check cache FIRST before querying database
    cache_key = f"doctor:profile:{id}"
    cached = redis_service.get_json(cache_key)
    if cached:
        return cached

    doctor_data = (
        db.query(doctor_model.Doctor)
        .filter(
            doctor_model.Doctor.doctor_id == id,
            doctor_model.Doctor.verification_status == "VERIFIED",
        )
        .first()
    )
    if doctor_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found"
        )

    response = doctor_schema.DoctorSearchResponse.model_validate(doctor_data).model_dump()
    redis_service.set_json(cache_key, response, ttl=300)

    return response


# ---------------------------------------------------------------------------
# GET /doctor/profile/search/specialisation/{specialisation}
# ---------------------------------------------------------------------------
@router.get(
    "/search/specialisation/{specialisation}",
    response_model=list[doctor_schema.DoctorSearchResponse],
)
def SearchDoctorBySpecialisation(
    specialisation: str,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    doctors = (
        db.query(doctor_model.Doctor)
        .join(user.User, doctor_model.Doctor.user_id == user.User.id)
        .filter(
            doctor_model.Doctor.specialisation.ilike(f"%{specialisation}%"),
            doctor_model.Doctor.verification_status == "VERIFIED",
        )
        .all()
    )
    if not doctors:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    return doctors


# ---------------------------------------------------------------------------
# GET /doctor/profile/search/name/{name}
# ---------------------------------------------------------------------------
@router.get(
    "/search/name/{name}",
    response_model=list[doctor_schema.DoctorSearchResponse],
)
def SearchDoctorByName(
    name: str,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    doctors = (
        db.query(doctor_model.Doctor)
        .join(user.User, doctor_model.Doctor.user_id == user.User.id)
        .filter(
            user.User.name.ilike(f"%{name}%"),
            doctor_model.Doctor.verification_status == "VERIFIED",
        )
        .all()
    )
    if not doctors:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    return doctors
