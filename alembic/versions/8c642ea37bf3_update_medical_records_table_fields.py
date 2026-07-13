"""update medical_records table fields

Revision ID: 8c642ea37bf3
Revises: e1242efb33ed
Create Date: 2026-07-09

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "8c642ea37bf3"
down_revision: Union[str, Sequence[str], None] = "e1242efb33ed"
branch_labels = None
depends_on = None


def upgrade() -> None:

    # -----------------------------
    # Rename tables
    # -----------------------------
    op.rename_table("Patient_Profiles", "patient_profiles")
    op.rename_table("medicalrecord", "medical_record")

    # -----------------------------
    # Rename columns
    # -----------------------------
    op.alter_column(
        "medical_record",
        "record_id",
        new_column_name="medical_record_id"
    )

    op.alter_column(
        "medical_record",
        "doctor_notes",
        new_column_name="clinical_notes"
    )

    op.alter_column(
        "medical_record",
        "follow_up_dates",
        new_column_name="follow_up_date"
    )

    # -----------------------------
    # Drop old foreign keys
    # -----------------------------
    op.drop_constraint(
        "appointments_patient_id_fkey",
        "appointments",
        type_="foreignkey"
    )

    op.drop_constraint(
        "medicalrecord_patient_id_fkey",
        "medical_record",
        type_="foreignkey"
    )

    op.drop_constraint(
        "prescription_patient_id_fkey",
        "prescription",
        type_="foreignkey"
    )

    op.drop_constraint(
        "prescription_medical_record_id_fkey",
        "prescription",
        type_="foreignkey"
    )

    # -----------------------------
    # Recreate foreign keys
    # -----------------------------
    op.create_foreign_key(
        "appointments_patient_id_fkey",
        "appointments",
        "patient_profiles",
        ["patient_id"],
        ["patient_id"]
    )

    op.create_foreign_key(
        "medical_record_patient_id_fkey",
        "medical_record",
        "patient_profiles",
        ["patient_id"],
        ["patient_id"]
    )

    op.create_foreign_key(
        "prescription_patient_id_fkey",
        "prescription",
        "patient_profiles",
        ["patient_id"],
        ["patient_id"]
    )

    op.create_foreign_key(
        "prescription_medical_record_id_fkey",
        "prescription",
        "medical_record",
        ["medical_record_id"],
        ["medical_record_id"]
    )


def downgrade() -> None:

    op.drop_constraint(
        "prescription_medical_record_id_fkey",
        "prescription",
        type_="foreignkey"
    )

    op.drop_constraint(
        "prescription_patient_id_fkey",
        "prescription",
        type_="foreignkey"
    )

    op.drop_constraint(
        "medical_record_patient_id_fkey",
        "medical_record",
        type_="foreignkey"
    )

    op.drop_constraint(
        "appointments_patient_id_fkey",
        "appointments",
        type_="foreignkey"
    )

    op.alter_column(
        "medical_record",
        "medical_record_id",
        new_column_name="record_id"
    )

    op.alter_column(
        "medical_record",
        "clinical_notes",
        new_column_name="doctor_notes"
    )

    op.alter_column(
        "medical_record",
        "follow_up_date",
        new_column_name="follow_up_dates"
    )

    op.rename_table("medical_record", "medicalrecord")
    op.rename_table("patient_profiles", "Patient_Profiles")

    op.create_foreign_key(
        "appointments_patient_id_fkey",
        "appointments",
        "Patient_Profiles",
        ["patient_id"],
        ["patient_id"]
    )

    op.create_foreign_key(
        "medicalrecord_patient_id_fkey",
        "medicalrecord",
        "Patient_Profiles",
        ["patient_id"],
        ["patient_id"]
    )

    op.create_foreign_key(
        "prescription_patient_id_fkey",
        "prescription",
        "Patient_Profiles",
        ["patient_id"],
        ["patient_id"]
    )

    op.create_foreign_key(
        "prescription_medical_record_id_fkey",
        "prescription",
        "medicalrecord",
        ["medical_record_id"],
        ["record_id"]
    )