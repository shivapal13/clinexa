from datetime import date, time, timedelta, datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from app.services.availability_service import resolve_availability
from app.models import appointment_model
from app.core.enums import AppointmentStatus

IST = ZoneInfo("Asia/Kolkata")


def generate_slots(start_time: time, end_time: time, slot_duration: int):
    slots = []
    base = datetime(2000, 1, 1)
    current = base.replace(
        hour=start_time.hour,
        minute=start_time.minute,
        second=0,
        microsecond=0,
    )
    end = base.replace(
        hour=end_time.hour,
        minute=end_time.minute,
        second=0,
        microsecond=0,
    )

    while current + timedelta(minutes=slot_duration) <= end:
        slot_end = current + timedelta(minutes=slot_duration)
        slots.append(
            {
                "start_time": current.time().strftime("%H:%M"),
                "end_time": slot_end.time().strftime("%H:%M"),
            }
        )
        current = slot_end

    return slots


def get_available_slots(
    doctor_id: int,
    target_date: date,
    db: Session,
    exclude_appointment_id: int | None = None,
):
    now_ist = datetime.now(IST)
    today_ist = now_ist.date()

    # Past dates have no available slots
    if target_date < today_ist:
        return []

    availability = resolve_availability(
        doctor_id=doctor_id,
        target_date=target_date,
        db=db,
    )

    if not availability:
        return []

    slots = [
        slot
        for window in availability
        for slot in generate_slots(
            window.start_time,
            window.end_time,
            window.slot_duration,
        )
    ]

    query = db.query(appointment_model.Appointment).filter(
        appointment_model.Appointment.doctor_id == doctor_id,
        appointment_model.Appointment.appointment_date == target_date,
        appointment_model.Appointment.status.in_(
            [AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]
        ),
    )

    if exclude_appointment_id is not None:
        query = query.filter(
            appointment_model.Appointment.appointment_id != exclude_appointment_id
        )

    booked_appointments = query.all()
    booked_times = {
        appointment.appointment_time.strftime("%H:%M")
        for appointment in booked_appointments
    }

    current_time_str = now_ist.strftime("%H:%M")

    available_slots = []
    for slot in slots:
        start_time_str = slot["start_time"]
        # Skip booked slots
        if start_time_str in booked_times:
            continue
        # Filter out past slots for today
        if target_date == today_ist and start_time_str <= current_time_str:
            continue
        available_slots.append(slot)

    return available_slots
