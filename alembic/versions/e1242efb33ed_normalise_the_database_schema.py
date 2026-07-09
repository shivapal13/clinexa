"""normalise the database schema

Revision ID: e1242efb33ed
Revises: d48150da1343
Create Date: 2026-07-09 18:32:33.552111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1242efb33ed'
down_revision: Union[str, Sequence[str], None] = 'd48150da1343'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op
import sqlalchemy as sa


def upgrade():

    appointment_status = sa.Enum(
        "PENDING",
        "CONFIRMED",
        "COMPLETED",
        "CANCELLED",
        "REJECTED",
        name="appointmentstatus",
    )

    # Create PostgreSQL enum type
    appointment_status.create(op.get_bind(), checkfirst=True)

    op.create_unique_constraint(
        "uq_patient_phone",
        "Patient_Profiles",
        ["phone_number"],
    )

    op.alter_column(
        "appointments",
        "status",
        existing_type=sa.String(),
        type_=appointment_status,
        existing_nullable=False,
        postgresql_using="status::appointmentstatus",
    )

    op.create_unique_constraint(
        "uq_medicalrecord_appointment",
        "medicalrecord",
        ["appointment_id"],
    )

    op.create_unique_constraint(
        "uq_prescription_record",
        "prescription",
        ["medical_record_id"],
    )

def downgrade():

    appointment_status = sa.Enum(
        "PENDING",
        "CONFIRMED",
        "COMPLETED",
        "CANCELLED",
        "REJECTED",
        name="appointmentstatus",
    )

    op.drop_constraint(
        "uq_prescription_record",
        "prescription",
        type_="unique",
    )

    op.drop_constraint(
        "uq_medicalrecord_appointment",
        "medicalrecord",
        type_="unique",
    )

    op.alter_column(
        "appointments",
        "status",
        existing_type=appointment_status,
        type_=sa.String(),
        existing_nullable=False,
        postgresql_using="status::text",
    )

    appointment_status.drop(op.get_bind(), checkfirst=True)

    op.drop_constraint(
        "uq_patient_phone",
        "Patient_Profiles",
        type_="unique",
    )
