from app.core.celery_app import celery_app
from app.services.email_service import send_email
import asyncio


@celery_app.task
def send_confirmation_email(email: str,patient_name:str,doctor_name:str,specialisation:str,medical_service:str,appointment_date:str,appointment_time:str):

    try:
        asyncio.run(
            send_email(
                recipients=[email],
                subject="Appointment Confirmed",
               body = f"""
<h2>Appointment Confirmed</h2>

<p>Dear <strong>{patient_name}</strong>,</p>

<p>Your appointment has been successfully booked.</p>

<hr>

<h3>Appointment Details</h3>

<ul>
    <li><strong>Doctor:</strong> {doctor_name}</li>
    <li><strong>Specialisation:</strong> {specialisation}</li>
    <li><strong>Service:</strong> {medical_service}</li>
    <li><strong>Date:</strong> {appointment_date}</li>
    <li><strong>Time:</strong> {appointment_time}</li>
    <li><strong>Status:</strong> Confirmed</li>
</ul>

<hr>

<h3>Instructions</h3>

<ul>
    <li>Please arrive 10 minutes early.</li>
    <li>Carry a valid ID proof.</li>
    <li>Bring previous medical records if available.</li>
</ul>

<p>Thank you for choosing <strong>Clinexa</strong>.</p>
"""
            )
        )

    except Exception as e:
        print(f"Failed to send email: {e}")
        raise


from app.core.celery_app import celery_app
from app.services.email_service import send_email
import asyncio


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

    try:
        asyncio.run(
            send_email(
                recipients=[email],
                subject="⏰ Appointment Reminder | Clinexa",
                body=f"""
<h2>Appointment Reminder</h2>

<p>Dear <strong>{patient_name}</strong>,</p>

<p>
This is a friendly reminder that your appointment is scheduled in
<strong>1 hour</strong>.
</p>

<hr>

<h3>Appointment Details</h3>

<ul>
    <li><strong>Doctor:</strong> {doctor_name}</li>
    <li><strong>Specialisation:</strong> {specialisation}</li>
    <li><strong>Medical Service:</strong> {medical_service}</li>
    <li><strong>Date:</strong> {appointment_date}</li>
    <li><strong>Time:</strong> {appointment_time}</li>
</ul>

<hr>

<h3>Before Your Visit</h3>

<ul>
    <li>Please arrive 10 minutes early.</li>
    <li>Carry a valid ID proof.</li>
    <li>Bring previous prescriptions or reports if available.</li>
</ul>

<hr>

<p>
We look forward to serving you.
</p>

<p>
Thank you for choosing <strong>Clinexa</strong>.
</p>
"""
            )
        )

    except Exception as e:
        print(f"Failed to send reminder email: {e}")
        raise    