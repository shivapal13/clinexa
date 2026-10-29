from app.models import recurring_availability_model, custom_availability_model
from sqlalchemy.orm import Session
from datetime import date


def resolve_availability(doctor_id: int, target_date: date, db: Session):
    # FIX: was `custom_availability.CustomAvailability.is_available` —
    # that's accessing the *class* attribute, not the row instance, raising AttributeError.
    # Correct: use the instance directly.
    custom_availability = (
        db.query(custom_availability_model.CustomAvailability)
        .filter(
            custom_availability_model.CustomAvailability.doctor_id == doctor_id,
            custom_availability_model.CustomAvailability.date == target_date,
        )
        .first()
    )

    if custom_availability is not None:
        if not custom_availability.is_available:
            return []
        return [custom_availability]

    weekday = target_date.strftime("%A").upper()

    recurring_availabilities = (
        db.query(recurring_availability_model.RecurringAvailability)
        .filter(
            recurring_availability_model.RecurringAvailability.doctor_id == doctor_id,
            recurring_availability_model.RecurringAvailability.day_of_week == weekday,
        )
        .order_by(recurring_availability_model.RecurringAvailability.start_time)
        .all()
    )

    return recurring_availabilities
