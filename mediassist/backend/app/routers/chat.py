import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import require_health_information_consent
from app.models import Conversation, Message, User
from app.schemas import (
    ChatResponse,
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
    SourceResponse,
)
from app.services.context.context_router import context_router
from app.services.emergency_detection import EMERGENCY_RESPONSE, emergency_detection_service
from app.services.gemini_service import gemini_service
from app.services.health_context_service import health_context_service
from app.services.rag.retrieval_service import retrieval_service
from app.services.web_search_service import web_search_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversations", tags=["Chat"])


def _conversation_for_user(db: Session, conversation_id: int, user_id: int) -> Conversation:
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def _knowledge_source(chunk: dict) -> SourceResponse:
    metadata = chunk.get("metadata") or {}
    return SourceResponse(
        title=str(metadata.get("title") or "Medical knowledge source"),
        source=str(metadata.get("source") or metadata.get("filename") or "Curated knowledge base"),
        page=metadata.get("page"),
        url=metadata.get("url") or metadata.get("source_url"),
        kind="knowledge_base",
    )


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(require_health_information_consent),
    db: Session = Depends(get_db),
):
    conversation = Conversation(user_id=current_user.id, title=conversation_data.title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("", response_model=list[ConversationResponse])
def get_conversations(
    current_user: User = Depends(require_health_information_consent),
    db: Session = Depends(get_db),
):
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: int,
    conversation_data: ConversationUpdate,
    current_user: User = Depends(require_health_information_consent),
    db: Session = Depends(get_db),
):
    conversation = _conversation_for_user(db, conversation_id, current_user.id)
    conversation.title = conversation_data.title
    db.commit()
    db.refresh(conversation)
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(require_health_information_consent),
    db: Session = Depends(get_db),
):
    conversation = _conversation_for_user(db, conversation_id, current_user.id)
    db.delete(conversation)
    db.commit()
    return None


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
def get_conversation_messages(
    conversation_id: int,
    current_user: User = Depends(require_health_information_consent),
    db: Session = Depends(get_db),
):
    conversation = _conversation_for_user(db, conversation_id, current_user.id)
    return conversation.messages


@router.post("/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(
    conversation_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(require_health_information_consent),
    db: Session = Depends(get_db),
):
    conversation = _conversation_for_user(db, conversation_id, current_user.id)
    content = message_data.content.strip()
    attachment_context = (message_data.attachment_text or "").strip()
    if not content:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")
    if len(attachment_context) > settings.MAX_ATTACHMENT_CHARS:
        raise HTTPException(status_code=413, detail="Attached text exceeds the processing limit.")

    user_message = Message(conversation_id=conversation.id, role="user", content=content)
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    previous_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id, Message.id != user_message.id)
        .order_by(Message.created_at.desc())
        .limit(10)
        .all()
    )
    previous_messages.reverse()
    history = [{"role": item.role, "content": item.content} for item in previous_messages]

    sources: list[SourceResponse] = []
    reference_context: list[dict] = []
    personal_context = ""
    web_context = ""

    try:
        # The deterministic emergency route runs before retrieval or any model call.
        if emergency_detection_service.detect_emergency(content):
            answer = EMERGENCY_RESPONSE.strip()
        else:
            decision = context_router.route(content)
            logger.info(
                "Chat context selected (user_id=%s, rag=%s, personal=%s, attachment=%s)",
                current_user.id,
                decision.use_medical_rag,
                decision.use_personal_health,
                bool(attachment_context),
            )

            if decision.use_personal_health:
                personal_context = health_context_service.get_user_health_context(
                    db=db,
                    user_id=current_user.id,
                )

            if decision.use_medical_rag or attachment_context:
                reference_context = retrieval_service.search(
                    content,
                    limit=4,
                    candidate_k=settings.RERANKER_CANDIDATE_K,
                    use_reranker=settings.RERANKER_ENABLED,
                    )

                sources.extend(_knowledge_source(item) for item in reference_context)

            # Web search is off by default and only receives generic-looking
            # non-personal queries; the adapter applies additional redaction filters.
            if (
                settings.ENABLE_WEB_SEARCH
                and decision.use_medical_rag
                and not decision.use_personal_health
                and not attachment_context
            ):
                web_results = await web_search_service.search_generic_health(content)
                for item in web_results:
                    web_context += f"\n\n[{item['title']} — {item['url']}]\n{item['content']}"
                    sources.append(
                        SourceResponse(
                            title=item["title"],
                            source=item["source"],
                            url=item["url"],
                            kind="web_search",
                        )
                    )

            answer = await gemini_service.generate_response(
                user_message=content,
                conversation_history=history,
                retrieved_context=reference_context,
                personal_health_context=personal_context,
                attachment_context=attachment_context,
                web_context=web_context,
            )

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
        )
        db.add(assistant_message)
        db.add(conversation)
        db.commit()
        db.refresh(assistant_message)
        return ChatResponse(
            user_message=user_message,
            assistant_message=assistant_message,
            sources=sources,
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        logger.exception("Chat response generation failed (user_id=%s)", current_user.id)
        db.rollback()
        err_str = str(exc).lower()
        provider_name = "Groq" if settings.LLM_PROVIDER.strip().lower() == "groq" else "Gemini"
        if "configured groq model" in err_str or "configured gemini model" in err_str:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        if "quota" in err_str or "resourceexhausted" in err_str or "429" in err_str or "rate_limit" in err_str:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"{provider_name} AI API quota or rate limit reached. Please check your {provider_name} dashboard or try again shortly.",
            ) from exc
        if "invalid_api_key" in err_str or "authentication" in err_str or "401" in err_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid {provider_name} API key. Please verify your {provider_name} API key in backend/.env.",
            ) from exc
        if "no llm api key configured" in err_str:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No AI API key is configured. Please add your GROQ_API_KEY in backend/.env.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"MediAssist is temporarily unable to generate a response via {provider_name}. Please try again.",
        ) from exc
