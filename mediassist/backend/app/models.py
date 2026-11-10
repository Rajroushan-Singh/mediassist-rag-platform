from datetime import datetime, timezone, date
from sqlalchemy import (
    String,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Text,
    Integer,
    Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    consent_records: Mapped[list["ConsentRecord"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    health_profile: Mapped["UserHealthProfile | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False
    )

    medical_conditions: Mapped[list["UserMedicalCondition"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    medications: Mapped[list["UserMedication"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    treatments: Mapped[list["UserTreatment"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class ConsentRecord(Base):

    __tablename__ = "consent_records"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    consent_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    consent_version: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    accepted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )

    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="consent_records"
    )


class Conversation(Base):

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(200),
        default="New conversation",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="conversations"
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )


class Message(Base):

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages"
    )


Index(
    "ix_messages_conversation_created",
    Message.conversation_id,
    Message.created_at
)


class UserHealthProfile(Base):

    __tablename__ = "user_health_profiles"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    biological_sex: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )

    health_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="health_profile"
    )

class UserMedicalCondition(Base):

    __tablename__ = "user_medical_conditions"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    condition_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="active",
        nullable=False
    )

    diagnosed_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="medical_conditions"
    )

# class UserMedicalCondition(Base):

#     __tablename__ = "user_medical_conditions"

#     id: Mapped[int] = mapped_column(
#         primary_key=True
#     )

#     user_id: Mapped[int] = mapped_column(
#         ForeignKey("users.id", ondelete="CASCADE"),
#         nullable=False,
#         index=True
#     )

#     condition_name: Mapped[str] = mapped_column(
#         String(200),
#         nullable=False
#     )

#     status: Mapped[str] = mapped_column(
#         String(30),
#         default="active",
#         nullable=False
#     )

#     diagnosed_date: Mapped[date | None] = mapped_column(
#         Date,
#         nullable=True
#     )

#     notes: Mapped[str | None] = mapped_column(
#         Text,
#         nullable=True
#     )

#     created_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         default=utc_now,
#         nullable=False
#     )

#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         default=utc_now,
#         onupdate=utc_now,
#         nullable=False
#     )

#     user: Mapped["User"] = relationship(
#         back_populates="medical_conditions"
#     )

class UserMedication(Base):

    __tablename__ = "user_medications"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    medication_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="active",
        nullable=False
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="medications"
    )

class UserTreatment(Base):

    __tablename__ = "user_treatments"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    treatment_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    treatment_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="active",
        nullable=False
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="treatments"
    )