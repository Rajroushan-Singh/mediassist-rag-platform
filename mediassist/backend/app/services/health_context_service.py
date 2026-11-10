from sqlalchemy.orm import Session

from app.models import (
    UserHealthProfile,
    UserMedicalCondition,
    UserMedication,
    UserTreatment
)


class HealthContextService:

    def get_user_health_context(
        self,
        db: Session,
        user_id: int
    ) -> str:

        context_parts = []

        profile = (
            db.query(UserHealthProfile)
            .filter(
                UserHealthProfile.user_id == user_id
            )
            .first()
        )

        if profile:

            profile_parts = []

            if profile.biological_sex:
                profile_parts.append(
                    f"Biological sex: {profile.biological_sex}"
                )

            if profile.health_notes:
                profile_parts.append(
                    f"General health notes: "
                    f"{profile.health_notes}"
                )

            if profile_parts:

                context_parts.append(
                    "USER HEALTH PROFILE:\n"
                    + "\n".join(profile_parts)
                )

        conditions = (
            db.query(UserMedicalCondition)
            .filter(
                UserMedicalCondition.user_id == user_id
            )
            .all()
        )

        if conditions:

            condition_lines = []

            for condition in conditions:

                line = (
                    f"- {condition.condition_name} "
                    f"(status: {condition.status})"
                )

                if condition.notes:
                    line += f". Notes: {condition.notes}"

                condition_lines.append(line)

            context_parts.append(
                "MEDICAL CONDITIONS:\n"
                + "\n".join(condition_lines)
            )

        medications = (
            db.query(UserMedication)
            .filter(
                UserMedication.user_id == user_id
            )
            .all()
        )

        if medications:

            medication_lines = []

            for medication in medications:

                line = (
                    f"- {medication.medication_name} "
                    f"(status: {medication.status})"
                )

                if medication.notes:
                    line += f". Notes: {medication.notes}"

                medication_lines.append(line)

            context_parts.append(
                "MEDICATIONS:\n"
                + "\n".join(medication_lines)
            )

        treatments = (
            db.query(UserTreatment)
            .filter(
                UserTreatment.user_id == user_id
            )
            .all()
        )

        if treatments:

            treatment_lines = []

            for treatment in treatments:

                line = (
                    f"- {treatment.treatment_name} "
                    f"(status: {treatment.status})"
                )

                if treatment.treatment_type:
                    line += (
                        f", type: "
                        f"{treatment.treatment_type}"
                    )

                if treatment.notes:
                    line += f". Notes: {treatment.notes}"

                treatment_lines.append(line)

            context_parts.append(
                "CURRENT OR PAST TREATMENTS:\n"
                + "\n".join(treatment_lines)
            )

        if not context_parts:
            return ""

        return "\n\n".join(context_parts)


health_context_service = HealthContextService()