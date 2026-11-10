import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from types import SimpleNamespace

from app.database import Base, get_db
from app.dependencies import get_current_user
from app.main import app
from app.models import Conversation, ConsentRecord, User
from app.services.emergency_detection import emergency_detection_service
from app.services.gemini_service import gemini_service


@pytest.fixture
def api_environment(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    with TestingSession() as session:
        user = User(full_name="Test User", email="test@example.org", hashed_password="not-a-real-password-hash")
        session.add(user)
        session.commit()
        session.refresh(user)
        conversation = Conversation(user_id=user.id, title="Test conversation")
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        user_id = user.id
        conversation_id = conversation.id

    def override_db():
        with TestingSession() as session:
            yield session

    def override_user():
        return SimpleNamespace(id=user_id, is_active=True)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    monkeypatch.setattr(emergency_detection_service, "detect_emergency", lambda _: True)
    async def model_must_not_run(**kwargs):
        raise AssertionError("Emergency flow must not call the LLM")
    monkeypatch.setattr(gemini_service, "generate_response", model_must_not_run)
    with TestClient(app) as client:
        yield client, user_id, conversation_id, TestingSession
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_emergency_chat_bypasses_gemini(api_environment):
    client, _, conversation_id, _ = api_environment
    # Emergency handling still requires the authenticated, consented session.
    client.post(
        "/api/v1/consent",
        json={"consent_type": "health_information", "consent_version": "1.0", "accepted": True},
    )
    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "my father is struggling to breathe"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "medical emergency" in payload["assistant_message"]["content"].lower()


def test_health_endpoint_requires_latest_consent(api_environment):
    client, user_id, _, TestingSession = api_environment
    denied = client.get("/api/v1/health/profile")
    assert denied.status_code == 403

    with TestingSession() as session:
        session.add(
            ConsentRecord(
                user_id=user_id,
                consent_type="health_information",
                consent_version="1.0",
                accepted=True,
            )
        )
        session.commit()
    allowed = client.get("/api/v1/health/profile")
    assert allowed.status_code == 200
    assert allowed.json() is None

    with TestingSession() as session:
        session.add(
            ConsentRecord(
                user_id=user_id,
                consent_type="health_information",
                consent_version="1.0",
                accepted=False,
            )
        )
        session.commit()
    denied_after_withdrawal = client.get("/api/v1/health/profile")
    assert denied_after_withdrawal.status_code == 403
