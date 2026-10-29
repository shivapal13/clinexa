from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.models import appointment_model, patient_model, doctor_model, user
from app.tasks.email_tasks import send_reminder_email
from app.core.enums import AppointmentStatus
import logging

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")


@celery_app.task
def check_upcoming_appointments():
    db = SessionLocal()
    try:
        now = datetime.now(IST)
        # Look at appointments scheduled for today or tomorrow (handles midnight transitions cleanly)
        candidate_dates = [now.date(), (now + timedelta(days=1)).date()]

        candidates = (
            db.query(appointment_model.Appointment)
            .filter(
                appointment_model.Appointment.appointment_date.in_(candidate_dates),
                appointment_model.Appointment.status.in_(
                    [AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]
                ),
                appointment_model.Appointment.reminder_sent == False,
            )
            .all()
        )

        due_appointments = []
        for appt in candidates:
            appt_dt = datetime.combine(
                appt.appointment_date, appt.appointment_time, tzinfo=IST
            )
            diff_seconds = (appt_dt - now).total_seconds()
            # Send reminder if appointment is upcoming within the next 65 minutes
            if 0 <= diff_seconds <= 3900:
                due_appointments.append(appt)

        logger.info("Found %d upcoming appointments due for reminder", len(due_appointments))

        for appointment in due_appointments:
            patient = (
                db.query(patient_model.Patient)
                .filter(patient_model.Patient.patient_id == appointment.patient_id)
                .first()
            )
            if not patient:
                continue
            patient_user = db.query(user.User).filter(user.User.id == patient.user_id).first()
            doctor = (
                db.query(doctor_model.Doctor)
                .filter(doctor_model.Doctor.doctor_id == appointment.doctor_id)
                .first()
            )
            doctor_user = (
                db.query(user.User).filter(user.User.id == doctor.user_id).first() if doctor else None
            )

            if not patient_user or not doctor_user:
                continue

            try:
                send_reminder_email.delay(
                    email=patient_user.email,
                    patient_name=patient_user.name,
                    doctor_name=doctor_user.name,
                    specialisation=doctor.specialisation if doctor else "General",
                    medical_service=appointment.medical_service,
                    appointment_date=appointment.appointment_date.strftime("%d %B %Y"),
                    appointment_time=appointment.appointment_time.strftime("%I:%M %p"),
                )
                appointment.reminder_sent = True
            except Exception as exc:
                logger.error(
                    "Failed to queue reminder for appointment %s: %s",
                    appointment.appointment_id,
                    exc,
                )

        db.commit()

    except Exception as e:
        db.rollback()
        logger.error("Reminder task failed: %s", e)
        raise

    finally:
        db.close()
