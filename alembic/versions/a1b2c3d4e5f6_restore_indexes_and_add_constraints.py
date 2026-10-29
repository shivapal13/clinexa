"""restore indexes, add unique constraints, add partial unique on appointments

Revision ID: a1b2c3d4e5f6
Revises: 49ebf955dc59
Create Date: 2026-10-29 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "49ebf955dc59"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Restore the performance indexes using IF NOT EXISTS for idempotency
    # ------------------------------------------------------------------
    indexes = [
        ("index_appointments_doctor_date_time", "appointments", "doctor_id, appointment_date, appointment_time"),
        ("index_appointments_doctor_status", "appointments", "doctor_id, status"),
        ("index_appointments_patient_date_time", "appointments", "patient_id, appointment_date, appointment_time"),
        ("index_appointments_patient_status", "appointments", "patient_id, status"),
        ("index_custom_doctor_date", "customavailability", "doctor_id, date"),
        ("index_doctor_specialisation", "doctor_profiles", "specialisation"),
        ("index_doctor_specialisation_city", "doctor_profiles", "specialisation, city"),
        ("index_medical_record_doctor_created", "medical_record", "doctor_id, created_at"),
        ("index_medical_record_patient_created", "medical_record", "patient_id, created_at"),
        ("index_prescription_doctor_created", "prescription", "doctor_id, created_at"),
        ("index_prescription_patient_created", "prescription", "patient_id, created_at"),
        ("index_recurring_day_of_week", "recurringavailability", "doctor_id, day_of_week"),
    ]
    for idx_name, table, cols in indexes:
        op.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({cols})")

    # ------------------------------------------------------------------
    # 2. Add unique constraints safely after cleaning any legacy duplicate entries
    # ------------------------------------------------------------------
    op.execute(
        """
        DELETE FROM recurringavailability
        WHERE id IN (
            SELECT id
            FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY doctor_id, day_of_week
                           ORDER BY id ASC
                       ) AS rnum
                FROM recurringavailability
            ) dupes
            WHERE rnum > 1
        )
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_doctor_day') THEN
                ALTER TABLE recurringavailability ADD CONSTRAINT uq_doctor_day UNIQUE (doctor_id, day_of_week);
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        DELETE FROM customavailability
        WHERE id IN (
            SELECT id
            FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY doctor_id, date
                           ORDER BY id ASC
                       ) AS rnum
                FROM customavailability
            ) dupes
            WHERE rnum > 1
        )
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_doctor_date') THEN
                ALTER TABLE customavailability ADD CONSTRAINT uq_doctor_date UNIQUE (doctor_id, date);
            END IF;
        END $$;
        """
    )

    # ------------------------------------------------------------------
    # 3. Clean up legacy double-bookings from prior runs before creating
    #    the partial unique index. For any slot with multiple active bookings,
    #    keep the earliest booked appointment (rnum = 1) and mark subsequent
    #    duplicate bookings as CANCELLED.
    # ------------------------------------------------------------------
    op.execute(
        """
        UPDATE appointments
        SET status = 'CANCELLED'
        WHERE appointment_id IN (
            SELECT appointment_id
            FROM (
                SELECT appointment_id,
                       ROW_NUMBER() OVER (
                           PARTITION BY doctor_id, appointment_date, appointment_time
                           ORDER BY appointment_id ASC
                       ) AS rnum
                FROM appointments
                WHERE status IN ('PENDING', 'CONFIRMED')
            ) duplicates
            WHERE rnum > 1
        )
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_appointment_slot_active
        ON appointments (doctor_id, appointment_date, appointment_time)
        WHERE status IN ('PENDING', 'CONFIRMED')
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_appointment_slot_active")
    op.execute("ALTER TABLE customavailability DROP CONSTRAINT IF EXISTS uq_doctor_date")
    op.execute("ALTER TABLE recurringavailability DROP CONSTRAINT IF EXISTS uq_doctor_day")

    indexes = [
        "index_recurring_day_of_week",
        "index_prescription_patient_created",
        "index_prescription_doctor_created",
        "index_medical_record_patient_created",
        "index_medical_record_doctor_created",
        "index_doctor_specialisation_city",
        "index_doctor_specialisation",
        "index_custom_doctor_date",
        "index_appointments_patient_status",
        "index_appointments_patient_date_time",
        "index_appointments_doctor_status",
        "index_appointments_doctor_date_time",
    ]
    for idx_name in indexes:
        op.execute(f"DROP INDEX IF EXISTS {idx_name}")
