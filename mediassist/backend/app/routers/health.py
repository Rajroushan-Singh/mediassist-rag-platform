from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_health_information_consent
from app.models import (
    User,
    UserHealthProfile,
    UserMedicalCondition,
    UserMedication,
    UserTreatment
)
from app.schemas import (
    HealthProfileCreate,
    HealthProfileResponse,
    HealthProfileUpdate,
    MedicalConditionCreate,
    MedicalConditionUpdate,
    MedicalConditionResponse,
    MedicationCreate,
    MedicationUpdate,
    MedicationResponse,
    TreatmentCreate,
    TreatmentUpdate,
    TreatmentResponse
)


router = APIRouter(
    prefix="/health",
    tags=["Health Data"],
    dependencies=[Depends(require_health_information_consent)],
)


# ============================================================
# HEALTH PROFILE
# ============================================================

@router.get(
    "/profile",
    response_model=HealthProfileResponse | None
)
def get_health_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    profile = (
        db.query(UserHealthProfile)
        .filter(
            UserHealthProfile.user_id == current_user.id
        )
        .first()
    )

    return profile


@router.put(
    "/profile",
    response_model=HealthProfileResponse
)
def create_or_update_health_profile(
    data: HealthProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    profile = (
        db.query(UserHealthProfile)
        .filter(
            UserHealthProfile.user_id == current_user.id
        )
        .first()
    )

    if profile is None:

        profile = UserHealthProfile(
            user_id=current_user.id,
            **data.model_dump(exclude_unset=True)
        )

        db.add(profile)

    else:

        update_data = data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return profile


# ============================================================
# MEDICAL CONDITIONS
# ============================================================

@router.get(
    "/conditions",
    response_model=list[MedicalConditionResponse]
)
def get_medical_conditions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    return (
        db.query(UserMedicalCondition)
        .filter(
            UserMedicalCondition.user_id == current_user.id
        )
        .order_by(
            UserMedicalCondition.created_at.desc()
        )
        .all()
    )


@router.post(
    "/conditions",
    response_model=MedicalConditionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_medical_condition(
    data: MedicalConditionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    condition = UserMedicalCondition(
        user_id=current_user.id,
        **data.model_dump()
    )

    db.add(condition)
    db.commit()
    db.refresh(condition)

    return condition


@router.patch(
    "/conditions/{condition_id}",
    response_model=MedicalConditionResponse
)
def update_medical_condition(
    condition_id: int,
    data: MedicalConditionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    condition = (
        db.query(UserMedicalCondition)
        .filter(
            UserMedicalCondition.id == condition_id,
            UserMedicalCondition.user_id == current_user.id
        )
        .first()
    )

    if condition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical condition not found"
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(condition, field, value)

    db.commit()
    db.refresh(condition)

    return condition


@router.delete(
    "/conditions/{condition_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_medical_condition(
    condition_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    condition = (
        db.query(UserMedicalCondition)
        .filter(
            UserMedicalCondition.id == condition_id,
            UserMedicalCondition.user_id == current_user.id
        )
        .first()
    )

    if condition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical condition not found"
        )

    db.delete(condition)
    db.commit()


# ============================================================
# MEDICATIONS
# ============================================================

@router.get(
    "/medications",
    response_model=list[MedicationResponse]
)
def get_medications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    return (
        db.query(UserMedication)
        .filter(
            UserMedication.user_id == current_user.id
        )
        .order_by(
            UserMedication.created_at.desc()
        )
        .all()
    )


@router.post(
    "/medications",
    response_model=MedicationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_medication(
    data: MedicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    medication = UserMedication(
        user_id=current_user.id,
        **data.model_dump()
    )

    db.add(medication)
    db.commit()
    db.refresh(medication)

    return medication


@router.patch(
    "/medications/{medication_id}",
    response_model=MedicationResponse
)
def update_medication(
    medication_id: int,
    data: MedicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    medication = (
        db.query(UserMedication)
        .filter(
            UserMedication.id == medication_id,
            UserMedication.user_id == current_user.id
        )
        .first()
    )

    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found"
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(medication, field, value)

    db.commit()
    db.refresh(medication)

    return medication


@router.delete(
    "/medications/{medication_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_medication(
    medication_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    medication = (
        db.query(UserMedication)
        .filter(
            UserMedication.id == medication_id,
            UserMedication.user_id == current_user.id
        )
        .first()
    )

    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found"
        )

    db.delete(medication)
    db.commit()


# ============================================================
# TREATMENTS
# ============================================================

@router.get(
    "/treatments",
    response_model=list[TreatmentResponse]
)
def get_treatments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    return (
        db.query(UserTreatment)
        .filter(
            UserTreatment.user_id == current_user.id
        )
        .order_by(
            UserTreatment.created_at.desc()
        )
        .all()
    )


@router.post(
    "/treatments",
    response_model=TreatmentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_treatment(
    data: TreatmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    treatment = UserTreatment(
        user_id=current_user.id,
        **data.model_dump()
    )

    db.add(treatment)
    db.commit()
    db.refresh(treatment)

    return treatment


@router.patch(
    "/treatments/{treatment_id}",
    response_model=TreatmentResponse
)
def update_treatment(
    treatment_id: int,
    data: TreatmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    treatment = (
        db.query(UserTreatment)
        .filter(
            UserTreatment.id == treatment_id,
            UserTreatment.user_id == current_user.id
        )
        .first()
    )

    if treatment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment not found"
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(treatment, field, value)

    db.commit()
    db.refresh(treatment)

    return treatment


@router.delete(
    "/treatments/{treatment_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_treatment(
    treatment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    treatment = (
        db.query(UserTreatment)
        .filter(
            UserTreatment.id == treatment_id,
            UserTreatment.user_id == current_user.id
        )
        .first()
    )

    if treatment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment not found"
        )

    db.delete(treatment)
    db.commit()
