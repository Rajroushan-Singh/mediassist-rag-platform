from datetime import datetime
from typing import Literal
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# AUTHENTICATION

class RegisterRequest(BaseModel):

    full_name: str = Field(min_length=2, max_length=100)

    email: EmailStr

    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):

    email: EmailStr

    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):

    id: int
    full_name: str
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):

    access_token: str
    token_type: str = "bearer"


# CONSENT

class ConsentCreate(BaseModel):

    consent_type: str = Field(
        min_length=2,
        max_length=50
    )

    consent_version: str = Field(
        min_length=1,
        max_length=30
    )

    accepted: bool


class ConsentResponse(BaseModel):

    id: int
    consent_type: str
    consent_version: str
    accepted: bool
    accepted_at: datetime

    model_config = ConfigDict(from_attributes=True)


# CONVERSATIONS

class ConversationCreate(BaseModel):

    title: str = Field(
        default="New conversation",
        min_length=1,
        max_length=200
    )


class ConversationUpdate(BaseModel):

    title: str = Field(
        min_length=1,
        max_length=200
    )


class ConversationResponse(BaseModel):

    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# MESSAGES

class MessageCreate(BaseModel):

    content: str = Field(
        min_length=1,
        max_length=10000
    )
    attachment_text: str | None = Field(
        default=None,
        max_length=40000
    )


class MessageResponse(BaseModel):

    id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SourceResponse(BaseModel):
    title: str
    source: str
    page: int | None = None
    url: str | None = None
    kind: str = "knowledge_base"


class DocumentExtractResponse(BaseModel):
    filename: str
    content_type: str
    extracted_text: str
    warning: str | None = None


class ChatResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    sources: list[SourceResponse] = Field(default_factory=list)

class HealthProfileCreate(BaseModel):

    date_of_birth: date | None = None

    biological_sex: str | None = Field(
        default=None,
        max_length=30
    )

    health_notes: str | None = Field(
        default=None,
        max_length=5000
    )


class HealthProfileUpdate(HealthProfileCreate):
    pass


class HealthProfileResponse(HealthProfileCreate):

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MedicalConditionCreate(BaseModel):

    condition_name: str = Field(
        min_length=1,
        max_length=200
    )

    status: str = Field(
        default="active",
        max_length=30
    )

    diagnosed_date: date | None = None

    notes: str | None = Field(
        default=None,
        max_length=5000
    )


class MedicalConditionResponse(
    MedicalConditionCreate
):

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MedicationCreate(BaseModel):

    medication_name: str = Field(
        min_length=1,
        max_length=200
    )

    status: str = Field(
        default="active",
        max_length=30
    )

    start_date: date | None = None

    notes: str | None = Field(
        default=None,
        max_length=5000
    )


class MedicationResponse(MedicationCreate):

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TreatmentCreate(BaseModel):

    treatment_name: str = Field(
        min_length=1,
        max_length=200
    )

    treatment_type: str | None = Field(
        default=None,
        max_length=100
    )

    status: str = Field(
        default="active",
        max_length=30
    )

    start_date: date | None = None

    notes: str | None = Field(
        default=None,
        max_length=5000
    )


class TreatmentResponse(TreatmentCreate):

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MedicalConditionUpdate(BaseModel):

    condition_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200
    )

    status: str | None = Field(
        default=None,
        max_length=30
    )

    diagnosed_date: date | None = None

    notes: str | None = Field(
        default=None,
        max_length=5000
    )


class MedicationUpdate(BaseModel):

    medication_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200
    )

    status: str | None = Field(
        default=None,
        max_length=30
    )

    start_date: date | None = None

    notes: str | None = Field(
        default=None,
        max_length=5000
    )


class TreatmentUpdate(BaseModel):

    treatment_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200
    )

    treatment_type: str | None = Field(
        default=None,
        max_length=100
    )

    status: str | None = Field(
        default=None,
        max_length=30
    )

    start_date: date | None = None

    notes: str | None = Field(
        default=None,
        max_length=5000
    )
