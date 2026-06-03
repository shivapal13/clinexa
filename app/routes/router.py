from fastapi import APIRouter
from app.auth import auth
from app.routes import patient_profile, doctor_profile, appointment,medicalrecord,prescription

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(patient_profile.router)
api_router.include_router(doctor_profile.router)
api_router.include_router(appointment.router)
api_router.include_router(medicalrecord.router)
api_router.include_router(prescription.router)