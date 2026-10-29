from fastapi import HTTPException, status, Depends, APIRouter, Query
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.models import appointment_model, patient_model, doctor_model, user
from app.schemas import appointment_schema
from sqlalchemy.orm import Session
from app.core import security
from datetime import date, datetime
from zoneinfo import ZoneInfo
import math
import logging
from app.core.enums import AppointmentStatus
from app.services.slot_generation import get_available_slots
from app.services import redis_service
from app.tasks.email_tasks import send_confirmation_email

router = APIRouter(prefix="/appointments", tags=["Appointments"])

IST = ZoneInfo("Asia/Kolkata")
logger = logging.getLogger(__name__)


def _now_ist():
    return datetime.now(IST)


def _today_ist():
    return _now_ist().date()


def _assert_future_slot(appt_date: date, appt_time):
    now = _now_ist()
    if appt_date < now.date():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book or reschedule an appointment for a past date",
        )
    if appt_date == now.date() and appt_time <= now.time():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book or reschedule an appointment for a past time slot",
        )


# ---------------------------------------------------------------------------
# POST /appointments/  — book an appointment
# ---------------------------------------------------------------------------
@router.post("/", status_code=status.HTTP_201_CREATED)
def CreateAppointments(
    appointment_data: appointment_schema.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    patient_profile = (
        db.query(patient_model.Patient)
        .filter(patient_model.Patient.user_id == current_user.id)
        .first()
    )
    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")

    doctor_profile = (
        db.query(doctor_model.Doctor)
        .filter(doctor_model.Doctor.doctor_id == appointment_data.doctor_id)
        .first()
    )
    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    if doctor_profile.verification_status != "VERIFIED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This doctor is not currently verified or accepting appointments",
        )

    doctor_user = (
        db.query(user.User).filter(user.User.id == doctor_profile.user_id).first()
    )

    _assert_future_slot(appointment_data.appointment_date, appointment_data.appointment_time)

    slots = get_available_slots(
        doctor_id=appointment_data.doctor_id,
        target_date=appointment_data.appointment_date,
        db=db,
    )
    if not slots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor is not available on {appointment_data.appointment_date}",
        )

    valid_slots = {slot["start_time"] for slot in slots}
    requested_time = appointment_data.appointment_time.strftime("%H:%M")
    if requested_time not in valid_slots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid time slot"
        )

    new_appointment = appointment_model.Appointment(
        patient_id=patient_profile.patient_id,
        doctor_id=appointment_data.doctor_id,
        medical_service=appointment_data.medical_service,
        reason=appointment_data.reason,
        appointment_date=appointment_data.appointment_date,
        appointment_time=appointment_data.appointment_time,
        status=AppointmentStatus.PENDING,
    )

    db.add(new_appointment)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This appointment slot was just booked by another user. Please choose another time.",
        ) from exc

    db.refresh(new_appointment)

    # Invalidate slot cache immediately
    redis_service.delete_key(
        f"availability:doctor:{appointment_data.doctor_id}:{appointment_data.appointment_date}"
    )

    try:
        send_confirmation_email.delay(
            email=current_user.email,
            patient_name=current_user.name,
            doctor_name=doctor_user.name if doctor_user else "Doctor",
            specialisation=doctor_profile.specialisation,
            medical_service=appointment_data.medical_service,
            appointment_date=str(appointment_data.appointment_date),
            appointment_time=str(appointment_data.appointment_time),
        )
    except Exception:
        logger.exception(
            "Could not queue confirmation email for appointment %s",
            new_appointment.appointment_id,
        )

    return new_appointment


# ---------------------------------------------------------------------------
# GET /appointments/patient  — paginated list for a patient
# ---------------------------------------------------------------------------
@router.get(
    "/patient",
    status_code=status.HTTP_200_OK,
    response_model=appointment_schema.PatientAppointmentListResponse,
)
def GetPatientAppointments(
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    view: str | None = None,
):
    if current_user.role != "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    patient_profile = (
        db.query(patient_model.Patient)
        .filter(patient_model.Patient.user_id == current_user.id)
        .first()
    )
    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")

    query = db.query(appointment_model.Appointment).filter(
        appointment_model.Appointment.patient_id == patient_profile.patient_id
    )
    today = _today_ist()

    if view:
        view = view.upper()
        if view not in ("UPCOMING", "HISTORY"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="view must be UPCOMING or HISTORY",
            )
        if view == "UPCOMING":
            query = query.filter(appointment_model.Appointment.appointment_date >= today)
        else:
            query = query.filter(appointment_model.Appointment.appointment_date < today)

    total = query.count()
    offset = (page - 1) * page_size
    appointments = (
        query.order_by(
            appointment_model.Appointment.appointment_date.desc(),
            appointment_model.Appointment.appointment_time.desc(),
        )
        .offset(offset)
        .limit(page_size)
        .all()
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "appointments": appointments,
    }


# ---------------------------------------------------------------------------
# GET /appointments/patient/{appointment_id}  — single appointment for patient
# ---------------------------------------------------------------------------
@router.get(
    "/patient/{appointment_id}",
    status_code=status.HTTP_200_OK,
    response_model=appointment_schema.PatientAppointmentsResponse,
)
def GetPatientAppointmentById(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    patient_profile = (
        db.query(patient_model.Patient)
        .filter(patient_model.Patient.user_id == current_user.id)
        .first()
    )
    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")

    appointment = (
        db.query(appointment_model.Appointment)
        .filter(
            appointment_model.Appointment.patient_id == patient_profile.patient_id,
            appointment_model.Appointment.appointment_id == appointment_id,
        )
        .first()
    )
    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
        )

    return appointment


# ---------------------------------------------------------------------------
# PATCH /appointments/{appointment_id}  — patient reschedules
# ---------------------------------------------------------------------------
@router.patch("/{appointment_id}")
def UpdateAppointment(
    appointment_id: int,
    update_appointment: appointment_schema.AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    patient_profile = (
        db.query(patient_model.Patient)
        .filter(patient_model.Patient.user_id == current_user.id)
        .first()
    )
    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")

    appointment = (
        db.query(appointment_model.Appointment)
        .filter(appointment_model.Appointment.appointment_id == appointment_id)
        .first()
    )
    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
        )

    if appointment.patient_id != patient_profile.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    # Terminal states cannot be rescheduled
    if appointment.status in (AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED, AppointmentStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reschedule an appointment with status {appointment.status}",
        )

    update_data = update_appointment.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")

    old_date = appointment.appointment_date
    new_date = update_data.get("appointment_date", appointment.appointment_date)
    new_time = update_data.get("appointment_time", appointment.appointment_time)

    _assert_future_slot(new_date, new_time)

    # Check slot availability
    slots = get_available_slots(
        doctor_id=appointment.doctor_id,
        target_date=new_date,
        db=db,
        exclude_appointment_id=appointment_id,
    )
    if not slots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No slots available for {new_date}",
        )

    valid_slots = {slot["start_time"] for slot in slots}
    if new_time.strftime("%H:%M") not in valid_slots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid time slot"
        )

    for key, value in update_data.items():
        setattr(appointment, key, value)

    # If the appointment was CONFIRMED, resetting date/time returns it to PENDING for doctor re-approval
    if appointment.status == AppointmentStatus.CONFIRMED and ("appointment_date" in update_data or "appointment_time" in update_data):
        appointment.status = AppointmentStatus.PENDING

    # Reset reminder for the new time
    appointment.reminder_sent = False

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This slot was just taken by another appointment. Please choose another time.",
        ) from exc

    db.refresh(appointment)

    # Invalidate slot caches
    redis_service.delete_key(f"availability:doctor:{appointment.doctor_id}:{old_date}")
    redis_service.delete_key(f"availability:doctor:{appointment.doctor_id}:{new_date}")

    return {"message": "Appointment updated successfully", "appointment": appointment}


# ---------------------------------------------------------------------------
# PATCH /appointments/{appointment_id}/cancel  — patient cancels their appointment
# ---------------------------------------------------------------------------
@router.patch("/{appointment_id}/cancel")
def CancelPatientAppointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    patient_profile = (
        db.query(patient_model.Patient)
        .filter(patient_model.Patient.user_id == current_user.id)
        .first()
    )
    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")

    appointment = (
        db.query(appointment_model.Appointment)
        .filter(appointment_model.Appointment.appointment_id == appointment_id)
        .first()
    )
    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
        )

    if appointment.patient_id != patient_profile.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    # Patient can only cancel active appointments (PENDING or CONFIRMED)
    if appointment.status in (AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED, AppointmentStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel an appointment that is already {appointment.status}",
        )

    appointment.status = AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appointment)

    redis_service.delete_key(
        f"availability:doctor:{appointment.doctor_id}:{appointment.appointment_date}"
    )

    return {"message": "Appointment cancelled successfully", "appointment": appointment}


# ---------------------------------------------------------------------------
# GET /appointments/doctor  — paginated list for a doctor
# ---------------------------------------------------------------------------
@router.get(
    "/doctor",
    status_code=status.HTTP_200_OK,
    response_model=appointment_schema.DoctorAppointmentListResponse,
)
def GetDoctorAppointments(
    appt_status: AppointmentStatus | None = Query(None, alias="status"),
    appointment_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    doctor_profile = (
        db.query(doctor_model.Doctor)
        .filter(doctor_model.Doctor.user_id == current_user.id)
        .first()
    )
    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")

    query = db.query(appointment_model.Appointment).filter(
        appointment_model.Appointment.doctor_id == doctor_profile.doctor_id
    )

    if appt_status:
        query = query.filter(appointment_model.Appointment.status == appt_status)

    if appointment_date:
        query = query.filter(
            appointment_model.Appointment.appointment_date == appointment_date
        )

    total = query.count()
    offset = (page - 1) * page_size
    appointments = (
        query.order_by(
            appointment_model.Appointment.appointment_date.desc(),
            appointment_model.Appointment.appointment_time.desc(),
        )
        .offset(offset)
        .limit(page_size)
        .all()
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "appointments": appointments,
    }


# ---------------------------------------------------------------------------
# PATCH /appointments/{appointment_id}/status  — doctor transitions status
# ---------------------------------------------------------------------------
@router.patch("/{appointment_id}/status")
def UpdateAppointmentStatus(
    appointment_id: int,
    status_update: appointment_schema.AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    """
    Doctor-only endpoint to drive the status machine:
      PENDING   → CONFIRMED | REJECTED
      CONFIRMED → COMPLETED | CANCELLED
    """
    if current_user.role != "Doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    doctor_profile = (
        db.query(doctor_model.Doctor)
        .filter(doctor_model.Doctor.user_id == current_user.id)
        .first()
    )
    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")

    appointment = (
        db.query(appointment_model.Appointment)
        .filter(appointment_model.Appointment.appointment_id == appointment_id)
        .first()
    )
    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
        )

    if appointment.doctor_id != doctor_profile.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    allowed_transitions: dict[AppointmentStatus, set[AppointmentStatus]] = {
        AppointmentStatus.PENDING: {
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.REJECTED,
        },
        AppointmentStatus.CONFIRMED: {
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
        },
    }

    current_status = appointment.status
    new_status = status_update.status

    if current_status not in allowed_transitions or new_status not in allowed_transitions[current_status]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition appointment from {current_status} to {new_status}",
        )

    # Prevent marking future appointments as COMPLETED
    if new_status == AppointmentStatus.COMPLETED:
        now = _now_ist()
        if appointment.appointment_date > now.date() or (
            appointment.appointment_date == now.date() and appointment.appointment_time > now.time()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot mark a future appointment as completed before its scheduled time",
            )

    appointment.status = new_status
    db.commit()
    db.refresh(appointment)

    # Invalidate cache if slot freed
    if new_status in (AppointmentStatus.REJECTED, AppointmentStatus.CANCELLED):
        redis_service.delete_key(
            f"availability:doctor:{appointment.doctor_id}:{appointment.appointment_date}"
        )

    return {
        "message": f"Appointment status updated to {new_status}",
        "appointment": appointment,
    }


# ---------------------------------------------------------------------------
# PATCH /appointments/{appointment_id}/doctor-cancel  — doctor cancels appointment
# ---------------------------------------------------------------------------
@router.patch("/{appointment_id}/doctor-cancel")
def CancelDoctorAppointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    doctor_profile = (
        db.query(doctor_model.Doctor)
        .filter(doctor_model.Doctor.user_id == current_user.id)
        .first()
    )
    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")

    appointment = (
        db.query(appointment_model.Appointment)
        .filter(appointment_model.Appointment.appointment_id == appointment_id)
        .first()
    )
    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
        )

    if appointment.doctor_id != doctor_profile.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    # Doctor can only cancel CONFIRMED appointments. If PENDING, doctor must REJECT via /status.
    if appointment.status == AppointmentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a pending appointment; please reject it instead via status update",
        )

    if appointment.status in (AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED, AppointmentStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel an appointment that is already {appointment.status}",
        )

    appointment.status = AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appointment)

    redis_service.delete_key(
        f"availability:doctor:{appointment.doctor_id}:{appointment.appointment_date}"
    )

    return {
        "message": "Appointment cancelled successfully",
        "cancelled_by_doctor": doctor_profile.doctor_id,
        "appointment": appointment,
    }
