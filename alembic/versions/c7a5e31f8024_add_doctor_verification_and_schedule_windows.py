"""add doctor verification and support multiple schedule windows

Revision ID: c7a5e31f8024
Revises: a1b2c3d4e5f6
Create Date: 2026-10-29 10:28:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7a5e31f8024"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'doctor_profiles' AND column_name = 'license_number'
            ) THEN
                ALTER TABLE doctor_profiles ADD COLUMN license_number VARCHAR(128);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'doctor_profiles' AND column_name = 'verification_status'
            ) THEN
                ALTER TABLE doctor_profiles ADD COLUMN verification_status VARCHAR(16) DEFAULT 'PENDING' NOT NULL;
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'ck_doctor_verification_status'
            ) THEN
                ALTER TABLE doctor_profiles ADD CONSTRAINT ck_doctor_verification_status
                CHECK (verification_status IN ('PENDING', 'VERIFIED', 'REJECTED'));
            END IF;
        END $$;
        """
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS index_doctor_verification_status ON doctor_profiles (verification_status)"
    )

    # Support separate non-overlapping windows on the same weekday by dropping uq_doctor_day
    op.execute(
        "ALTER TABLE recurringavailability DROP CONSTRAINT IF EXISTS uq_doctor_day"
    )


def downgrade() -> None:
    bind = op.get_bind()
    duplicate_window = bind.execute(
        sa.text(
            """
            SELECT doctor_id, day_of_week
            FROM recurringavailability
            GROUP BY doctor_id, day_of_week
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )
    ).first()
    if duplicate_window:
        raise RuntimeError(
            "Cannot restore uq_doctor_day while a doctor has multiple weekly "
            "availability windows; consolidate those windows before downgrading."
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
    op.execute("DROP INDEX IF EXISTS index_doctor_verification_status")
    op.execute("ALTER TABLE doctor_profiles DROP CONSTRAINT IF EXISTS ck_doctor_verification_status")
    op.execute("ALTER TABLE doctor_profiles DROP COLUMN IF EXISTS verification_status")
    op.execute("ALTER TABLE doctor_profiles DROP COLUMN IF EXISTS license_number")
