from app.core.celery_app import celery_app
from app.services.email_service import send_email
import asyncio
import html
import logging

logger = logging.getLogger(__name__)


@celery_app.task
def send_confirmation_email(
    email: str,
    patient_name: str,
    doctor_name: str,
    specialisation: str,
    medical_service: str,
    appointment_date: str,
    appointment_time: str,
):
    # Escape user-controlled strings to prevent HTML injection
    safe_patient = html.escape(str(patient_name))
    safe_doctor = html.escape(str(doctor_name))
    safe_specialisation = html.escape(str(specialisation))
    safe_service = html.escape(str(medical_service))
    safe_date = html.escape(str(appointment_date))
    safe_time = html.escape(str(appointment_time))

    try:
        asyncio.run(
            send_email(
                recipients=[email],
                subject="Appointment Request Received | Clinexa",
                body=f"""
<h2>Appointment Request Received</h2>
<p>Dear <strong>{safe_patient}</strong>,</p>
<p>Your appointment request has been received and is awaiting confirmation from the doctor.</p>
<hr>
<h3>Appointment Details</h3>
<ul>
    <li><strong>Doctor:</strong> Dr. {safe_doctor}</li>
    <li><strong>Specialisation:</strong> {safe_specialisation}</li>
    <li><strong>Service:</strong> {safe_service}</li>
    <li><strong>Date:</strong> {safe_date}</li>
    <li><strong>Time:</strong> {safe_time}</li>
    <li><strong>Status:</strong> Pending confirmation</li>
</ul>
<hr>
<p>Thank you for choosing <strong>Clinexa</strong>.</p>
""",
            )
        )
    except Exception as e:
        logger.error("Failed to send booking confirmation email: %s", e)
        raise


@celery_app.task
def send_reminder_email(
    email: str,
    patient_name: str,
    doctor_name: str,
    specialisation: str,
    medical_service: str,
    appointment_date: str,
    appointment_time: str,
):
    safe_patient = html.escape(str(patient_name))
    safe_doctor = html.escape(str(doctor_name))
    safe_specialisation = html.escape(str(specialisation))
    safe_service = html.escape(str(medical_service))
    safe_date = html.escape(str(appointment_date))
    safe_time = html.escape(str(appointment_time))

    try:
        asyncio.run(
            send_email(
                recipients=[email],
                subject="⏰ Appointment Reminder | Clinexa",
                body=f"""
<h2>Appointment Reminder</h2>
<p>Dear <strong>{safe_patient}</strong>,</p>
<p>This is a friendly reminder that your appointment is scheduled in approximately <strong>1 hour</strong>.</p>
<hr>
<h3>Appointment Details</h3>
<ul>
    <li><strong>Doctor:</strong> Dr. {safe_doctor}</li>
    <li><strong>Specialisation:</strong> {safe_specialisation}</li>
    <li><strong>Medical Service:</strong> {safe_service}</li>
    <li><strong>Date:</strong> {safe_date}</li>
    <li><strong>Time:</strong> {safe_time}</li>
</ul>
<hr>
<h3>Before Your Visit</h3>
<ul>
    <li>Please arrive 10 minutes early.</li>
    <li>Carry a valid ID proof.</li>
    <li>Bring previous prescriptions or reports if available.</li>
</ul>
<hr>
<p>Thank you for choosing <strong>Clinexa</strong>.</p>
""",
            )
        )
    except Exception as e:
        logger.error("Failed to send reminder email: %s", e)
        raise


@celery_app.task
def send_status_update_email(
    email: str,
    patient_name: str,
    doctor_name: str,
    new_status: str,
    appointment_date: str,
    appointment_time: str,
):
    safe_patient = html.escape(str(patient_name))
    safe_doctor = html.escape(str(doctor_name))
    safe_status = html.escape(str(new_status))
    safe_date = html.escape(str(appointment_date))
    safe_time = html.escape(str(appointment_time))

    try:
        asyncio.run(
            send_email(
                recipients=[email],
                subject=f"Appointment Status Update: {safe_status} | Clinexa",
                body=f"""
<h2>Appointment Status Update</h2>
<p>Dear <strong>{safe_patient}</strong>,</p>
<p>Your appointment on <strong>{safe_date}</strong> at <strong>{safe_time}</strong> with <strong>Dr. {safe_doctor}</strong> has been updated to: <strong>{safe_status}</strong>.</p>
<hr>
<p>If you have questions, please log in to your Clinexa dashboard.</p>
""",
            )
        )
    except Exception as e:
        logger.error("Failed to send status update email: %s", e)
        raise
