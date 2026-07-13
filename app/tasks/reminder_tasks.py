from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from datetime import datetime ,timedelta
from app.models import appointment_model,patient_model,doctor_model,user
from app.tasks.email_tasks import send_reminder_email
from app.core.enums import AppointmentStatus



       

@celery_app.task
def check_upcoming_appointments():
    db=SessionLocal()
    
    try:
        now=datetime.now()
        reminder_time=now+timedelta(hours=1)
        window_end=reminder_time+timedelta(minutes=1)
        target_date=reminder_time.date()
        start_time=reminder_time.time()
        end_time=window_end.time()

        appointments=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.appointment_date==target_date,
                                                                    appointment_model.Appointment.appointment_time>=start_time,
                                                                    appointment_model.Appointment.appointment_time<=end_time,
                                                                    appointment_model.Appointment.status==AppointmentStatus.PENDING.value,
                                                                    appointment_model.Appointment.reminder_sent==False).all()

        print(f"found {len(appointments)} Upcoming Appointments")

        for appointment in appointments:
          patient=db.query(patient_model.Patient).filter(patient_model.Patient.patient_id==appointment.patient_id).first()
          patient_user=db.query(user.User).filter(user.User.id==patient.user_id).first()
          doctor=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.doctor_id==appointment.doctor_id).first()
          doctor_user=db.query(user.User).filter(user.User.id==doctor.user_id).first()

          send_reminder_email.delay(
            email=patient_user.email,
            patient_name=patient_user.name,
            doctor_name=doctor_user.name,
            specialisation=doctor.specialisation,
            medical_service=appointment.medical_service,
            appointment_date=appointment.appointment_date.strftime("%d %B %Y"),
            appointment_time=appointment.appointment_time.strftime("%I:%M %p"),
        )
            
          appointment.reminder_sent=True

        db.commit()

    except Exception as e:
       db.rollback()      
       print(f"Reminder task failed: {e}")
       raise

    finally:
       db.close()                                                  
