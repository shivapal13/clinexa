from fastapi import FastAPI,HTTPException,status,Depends,APIRouter,Query
from app.core.database import get_db
from app.models import appointment_model,patient_model,doctor_model
from app.schemas import appointment_schema,doctor_schema
from sqlalchemy.orm import Session
from app.core import security
from datetime import date,datetime
import math
from app.services.availability_service import resolve_availability
from app.services.slot_generation import generate_slots,get_available_slots
router=APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)


@router.post("/",status_code=status.HTTP_201_CREATED)
def CreateAppointments(appointment_data:appointment_schema.AppointmentCreate,db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!="Patient"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Patient not found")


    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.doctor_id==appointment_data.doctor_id).first()

    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")
    
    availability=resolve_availability(
        doctor_id=appointment_data.doctor_id,
        target_date=appointment_data.appointment_date,
        db=db

    )

    if availability is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Doctor is not available on Date: {appointment_data.appointment_date}")
    
    slots=generate_slots(
        availability.start_time,
        availability.end_time,
        availability.slot_duration
    )
    
    if appointment_data.appointment_date<=date.today() and appointment_data.appointment_time<datetime.now().time():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot book appointment for past date")
    

    existing_appointment=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.doctor_id==appointment_data.doctor_id,
                                                                        appointment_model.Appointment.appointment_date==appointment_data.appointment_date,
                                                                        appointment_model.Appointment.appointment_time==appointment_data.appointment_time,
                                                                        appointment_model.Appointment.status
                                                                        !='CANCELLED').first()
    if existing_appointment:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Selected Slots is already booked plz select another slot")
    
    new_appointment=appointment_model.Appointment(
        patient_id=patient_profile.patient_id,
        doctor_id=appointment_data.doctor_id,
        medical_service=appointment_data.medical_service,
        reason=appointment_data.reason,
        appointment_date=appointment_data.appointment_date,
        appointment_time=appointment_data.appointment_time,
        status="PENDING"
    )

    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    return new_appointment

@router.get("/",status_code=status.HTTP_200_OK,response_model=appointment_schema.PatientAppointmentListResponse)
def GetPatientAppointments(db:Session=Depends(get_db),current_user=Depends(security.get_current_user),page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)):

    if(current_user.role!='Patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()
    
    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Patient not found")
    
    query=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.patient_id==patient_profile.patient_id)
    
    total=query.count()
    offset=(page-1)*page_size
    
    patient_appointments = (
     query
    .order_by(
        appointment_model.Appointment.appointment_date,
        appointment_model.Appointment.appointment_time
    )
    .offset(offset)
    .limit(page_size)
    .all()
)

    total_pages=math.ceil(total/page_size)

    return {
    "total": total,
    "page": page,
    "page_size": page_size,
    "total_pages": total_pages,
    "appointments": patient_appointments
    }

@router.get("/{appointment_id}",status_code=status.HTTP_200_OK,response_model=appointment_schema.PatietntAppointmentListResponse)
def GetPatientAppointmentById(appointment_id:int,db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='Patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()
    
    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Patient not found")
    
    patient_appointments=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.patient_id==patient_profile.patient_id,
                                                                        appointment_model.Appointment.appointment_id==appointment_id).first()
    
    if patient_appointments is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Appointment not found")
    
    return patient_appointments

    
@router.patch("/{appointment_id}")
def UpdateAppointment(appointment_id:int,
                      update_appointment:appointment_schema.AppointmentUpdate,
                            db:Session=Depends(get_db),
                            current_user=Depends(security.get_current_user)):

    if(current_user.role!='Patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Patient not found")
    
    appointment=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.appointment_id==appointment_id).first()

    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Appointment not found")
    
    if appointment.patient_id!=patient_profile.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not Allowed")

    if appointment.status in ["CANCELLED","COMPLETED"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot update this appointment")
    
    update_data=update_appointment.model_dump(exclude_unset=True)

    appointment_date=update_data.get(
        "appointment_date",
        appointment.appointment_date
    )

    appointment_time=update_data.get(
        "appointment_time",
        appointment.appointment_time
    )

    if appointment_date<date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot update past appointments")
    
    if appointment_date==date.today() and appointment_time<datetime.now().time():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot update past appointment")
    
    availability=resolve_availability(
        doctor_id=appointment.doctor_id,
        target_date=appointment_date,
        db=db
    )

    if availability is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Doctor is not available on Date: {appointment_date}")
    
    slots=generate_slots(
        availability.start_time,
        availability.end_time,
        availability.slot_duration
    )

    valid_slots=[
        slot["start_time"]
        for slot in slots
    ]

    requested_time=appointment_time.strftime("%H:%M")

    if requested_time not in valid_slots:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid time Slot")
    
    existing_appointment=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.doctor_id==appointment.doctor_id,
                                                                        appointment_model.Appointment.appointment_date==appointment_date,
                                                                        appointment_model.Appointment.appointment_time==appointment_time,
                                                                        appointment_model.Appointment.status!="CANCELLED",
                                                                        appointment_model.Appointment.appointment_id!=appointment_id).first()
    
    if existing_appointment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Selected Slot is already booked")
    
    for key,value in update_data.items():
        setattr(appointment,key,value)

    db.commit()
    db.refresh(appointment)

    return {"message":"Appointment Updated Successfully",
            "Appointment_details":appointment}

@router.get("/",status_code=status.HTTP_200_OK,response_model=appointment_schema.DoctorAppointmentListResponse)
def GetDoctorAppointments(appointment_date:date |None=None,status:str|None=None,db:Session=Depends(get_db),current_user=Depends(security.get_current_user),page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)):

    if(current_user.role!='Doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()
    
    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")
    
    query=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.doctor_id==doctor_profile.doctor_id)
    
    if appointment_date:
     query = query.filter(
        appointment_model.Appointment.appointment_date == appointment_date
    )
    if status:
     query = query.filter(
        appointment_model.Appointment.status == status
    )
    total=query.count()
    offset=(page-1)*page_size
    query = query.order_by(
    appointment_model.Appointment.appointment_date,
    appointment_model.Appointment.appointment_time
)
    doctor_appointments=query.offset(offset).limit(page_size).all()

    total_pages=math.ceil(total/page_size)
    
    return {
    "total": total,
    "page": page,
    "page_size": page_size,
    "total_pages": total_pages,
    "appointments": doctor_appointments
} 

@router.patch("/{appointment_id}/cancel")
def CancelDoctorAppointment(appointment_id:int,
                            db:Session=Depends(get_db),
                            current_user=Depends(security.get_current_user)):

    if(current_user.role!='Doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")
    
    appointment=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.appointment_id==appointment_id).first()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No appointments Found")
    
    if(appointment.doctor_id!=doctor_profile.doctor_id):

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")

    if appointment.status in ["CANCELLED","COMPLETED"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot cancel this appointment")
    
    if (
    appointment.appointment_date < date.today()
    or (
        appointment.appointment_date == date.today()
        and appointment.appointment_time <= datetime.now().time()
    )
):
     raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Cannot cancel a past appointment"
    )

    appointment.status = "CANCELLED"

    db.commit()
    db.refresh(appointment)

    return {
    "message": "Appointment cancelled successfully",
    "Cancelled_by":doctor_profile.doctor_id,
    "appointment": appointment
}


@router.get("/patient/upcoming")
def GetUpcomingAppointments(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Patient not found")

    today=date.today()

    upcomming_appointments=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.patient_id==patient_profile.patient_id,appointment_model.Appointment.appointment_date>=today).all()
    
    return upcomming_appointments

@router.get("/patient/history")
def GetPastAppointments(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Patient not found")

    today=date.today()

    Past_appointments=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.patient_id==patient_profile.patient_id,appointment_model.Appointment.appointment_date<today).all()

    
    return Past_appointments

## Doctor side Logic ##

@router.get("/doctor",status_code=status.HTTP_200_OK)
def GetDoctorAppointments(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")
    
    doctor_appointments=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.doctor_id==doctor_profile.doctor_id).all()    

    return doctor_appointments

# doctor dashboard infomation about upcoming,pending,completed,cancelled appointments

@router.get("/doctor/dashboard",response_model=doctor_schema.DoctorDashboardResponse)
def GetDoctorDashboard(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")

    today=date.today()

    upcomming_appointments=db.query(appointment_model.Appointment).filter(
                                    appointment_model.Appointment.doctor_id==doctor_profile.doctor_id,
                                    appointment_model.Appointment.appointment_date>=today,
                                    appointment_model.Appointment.status=="CONFIRMED").count()
    
    pending_appointments=db.query(appointment_model.Appointment).filter(
                                    appointment_model.Appointment.doctor_id==doctor_profile.doctor_id,
                                    appointment_model.Appointment.status=="PENDING").count()
    
    completed_appointments=db.query(appointment_model.Appointment).filter(
                                    appointment_model.Appointment.doctor_id==doctor_profile.doctor_id,
                                    appointment_model.Appointment.status=="COMPLETED").count()
    
    cancelled_appointments=db.query(appointment_model.Appointment).filter(
                                    appointment_model.Appointment.doctor_id==doctor_profile.doctor_id,
                                    appointment_model.Appointment.status=="CANCELLED").count()
    
    rejected_appointments=db.query(appointment_model.Appointment).filter(
                                    appointment_model.Appointment.doctor_id==doctor_profile.doctor_id,
                                    appointment_model.Appointment.status=="REJECTED").count()
    
    
    return {
        "upcoming":upcomming_appointments,
        "pending":pending_appointments,
        "completed":completed_appointments,
        "cancelled":cancelled_appointments,
        "rejected":rejected_appointments
    } 

@router.get("/doctor/upcomming")
def GetDoctorUpcomingAppointments(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")
    today=date.today()

    upcomming_appointments=db.query(appointment_model.Appointment).filter(
                                    appointment_model.Appointment.doctor_id==doctor_profile.doctor_id,
                                    appointment_model.Appointment.appointment_date>=today,
                                    appointment_model.Appointment.status=="CONFIRMED").all()
    
    
    
    return upcomming_appointments

@router.get("/doctor/pending")
def GetDoctorPendingAppointments(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")


    pending_appointments=db.query(appointment_model.Appointment).filter(
                                    appointment_model.Appointment.doctor_id==doctor_profile.doctor_id,
                                    appointment_model.Appointment.status=="PENDING").all()
    
    return pending_appointments

@router.get("/doctor/completed")
def GetDoctorCompletedAppointments(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")


    completed_appointments=db.query(appointment_model.Appointment).filter(
                                    appointment_model.Appointment.doctor_id==doctor_profile.doctor_id,
                                    appointment_model.Appointment.status=="COMPLETED").all()
    
    return completed_appointments

@router.get("/doctor/cancelled")
def GetDoctorCancelledAppointments(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")


    cancelled_appointments=db.query(appointment_model.Appointment).filter(
                                    appointment_model.Appointment.doctor_id==doctor_profile.doctor_id,
                                   appointment_model.Appointment.status=="CANCELLED").all()
    
    return cancelled_appointments

@router.get("/doctor/rejected")
def GetDoctorRejectedAppointments(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")


    rejected_appointments=db.query(appointment_model.Appointment).filter(
                                    appointment_model.Appointment.doctor_id==doctor_profile.doctor_id,
                                    appointment_model.Appointment.status=="REJECTED").all()
    
    return rejected_appointments

@router.get("/doctor/history")
def GetPastAppointments(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")

    today=date.today()

    Past_appointments=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.doctor_id==doctor_profile.doctor_id,appointment_model.Appointment.appointment_date<today).all()
    

    return Past_appointments

