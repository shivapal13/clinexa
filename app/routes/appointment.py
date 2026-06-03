from fastapi import FastAPI,HTTPException,status,Depends,APIRouter,Response
from app.database import get_db
from app.models import appointment_model,patient_model,doctor_model
from app.schemas import appointment_schema,doctor_schema
from sqlalchemy.orm import Session
from app.core import security
from datetime import date

router=APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)

## Patient Side Logic ##

@router.post("/",status_code=status.HTTP_201_CREATED)
def CreateAppointments(appointment_data:appointment_schema.AppointmentCreate,db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!="patient"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Patient not found")


    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.doctor_id==appointment_data.doctor_id).first()

    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")
    
    existing_appointment=db.query(appointment_model.Appointment).filter(
               appointment_model.Appointment.doctor_id==appointment_data.doctor_id,
               appointment_model.Appointment.appointment_date==appointment_data.appointment_date,
               appointment_model.Appointment.appointment_time==appointment_data.appointment_time
    ).first()

    if existing_appointment is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="selected slot is  already filled")
 
    
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

@router.get("/patient",status_code=status.HTTP_200_OK)
def GetPatientAppointments(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Patient not found")
    
    patient_appointments=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.patient_id==patient_profile.patient_id).all()
    
    return  patient_appointments

    
@router.patch("/{appointment_id}/cancel")
def CancelAppointment(appointment_id:int,
                            db:Session=Depends(get_db),
                            current_user=Depends(security.get_current_user)):

    if(current_user.role!='patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Patient not found")
    
    appointment=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.appointment_id==appointment_id).first()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No appointments Found")
    
    if(appointment.patient_id!=patient_profile.patient_id):

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    if appointment.status=='COMPLETED':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Completed appointments cannot be cancelled")
    
    if appointment.status=="CANCELLED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Appointment Already cancelled ")
    
    appointment.status="CANCELLED" 

    db.commit()
    db.refresh(appointment)

    return {"message":"Status Cancelled Successfully"}

@router.patch("/{appointment_id}/status")
def UpdateDoctorAppointment(appointment_id:int,
                            update_appointment:appointment_schema.AppointmentsUpdate,
                            db:Session=Depends(get_db),
                            current_user=Depends(security.get_current_user)):

    if(current_user.role!='doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")
    
    appointment=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.appointment_id==appointment_id).first()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No appointments Found")
    
    if(appointment.doctor_id!=doctor_profile.doctor_id):

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")

    current_status=appointment.status
    new_status=update_appointment.status

######### status workflow ############

    if current_status=="PENDING":
        allowed=["CONFIRMED","REJECTED"]

    elif current_status=="CONFIRMED":
        allowed=["COMPLETED"]

    else:
        allowed=[]

    if new_status not in allowed:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"cannot change status from {current_status} to {new_status}")
    
    appointment.status=new_status

    db.commit()
    db.refresh(appointment)

    return {"message":f"Appointment marked to {new_status}"}

@router.patch("/{appointment_id}")
def UpdateAppointments(appointment_id:int,update_data:appointment_schema.UpdateAppointment,db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Patient not found")
    
    appointments=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.appointment_id==appointment_id).first()

    if appointments is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No appointments found")
    
    if appointments.patient_id!=patient_profile.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    if appointments.status!="PENDING":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You cannot update your appointment")
    conflict_appointments=db.query(appointment_model.Appointment).filter(
                                   appointment_model.Appointment.doctor_id==appointments.doctor_id,
                                   appointment_model.Appointment.appointment_date==update_data.appointment_date,
                                   appointment_model.Appointment.appointment_time==update_data.appointment_time,
                                   appointment_model.Appointment.appointment_id!=appointments.appointment_id
    ).first()

    if conflict_appointments is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Slot already Booked")
    
    appointments.appointment_date=update_data.appointment_date
    appointments.appointment_time=update_data.appointment_time
    appointments.reason=update_data.reason

    db.commit()
    db.refresh(appointments)

    return appointments


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

