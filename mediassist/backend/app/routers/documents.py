import base64
from io import BytesIO
import logging
from pathlib import Path
from time import perf_counter
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pdf2image import convert_from_bytes
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader
import pytesseract
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from groq import AsyncGroq

from app.config import settings
from app.dependencies import require_health_information_consent
from app.models import User
from app.schemas import DocumentExtractResponse
from app.services.metrics import OCR_REQUESTS_TOTAL, OCR_DURATION_SECONDS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}

CLINICAL_VISION_PROMPT = (
    "You are MediAssist's clinical image and document extraction specialist. "
    "Analyze this medical image or document thoroughly and extract structured, reliable information:\n"
    "1. TRANSCRIPTION: Transcribe all visible clinical text, lab names, values, units, physician notes, and dates accurately.\n"
    "2. LAB PANELS / TEST RESULTS: Clearly present test parameters, measured values, normal reference intervals, and clearly highlight abnormal/high/low markers.\n"
    "3. PRESCRIPTIONS & DRUGS: Extract drug names, strengths, dosages, route, frequency, duration, and safety warnings.\n"
    "4. CLINICAL / SYMPTOM PHOTOS: If this shows symptoms (e.g. skin rash, lesion, wound, swelling, eye), objectively describe the anatomical region and visual presentation (color, border, texture, size), outline key caution signs, and list questions to discuss with a physician.\n"
    "5. SAFETY & UNCERTAINTY: If any part is blurry or uncertain, indicate with [uncertain]. Always maintain a calm, objective clinical tone.\n"
    "Format cleanly in Markdown with bold headers and bullet points. Never fabricate data."
)


def detect_content_type(data: bytes) -> str | None:
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _format_llm_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
            elif isinstance(block, str):
                parts.append(block)
            elif hasattr(block, "text"):
                parts.append(str(getattr(block, "text")))
        return "\n".join(parts)
    return str(content)


async def _extract_with_groq_vision(data: bytes, content_type: str) -> str:
    """Analyze medical document or clinical image using Groq Llama 3.2 Vision."""
    if not settings.GROQ_API_KEY or not settings.GROQ_API_KEY.strip():
        raise ValueError("GROQ_API_KEY is not configured")

    b64_data = base64.b64encode(data).decode("utf-8")
    data_url = f"data:{content_type};base64,{b64_data}"

    client = AsyncGroq(api_key=settings.GROQ_API_KEY.strip())
    response = await client.chat.completions.create(
        model=settings.GROQ_VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": CLINICAL_VISION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_url,
                        },
                    },
                ],
            }
        ],
        temperature=0.1,
        max_tokens=2048,
    )
    if response.choices and response.choices[0].message and response.choices[0].message.content:
        return response.choices[0].message.content.strip()
    return ""


async def _extract_with_gemini_vision(data: bytes, content_type: str) -> str:
    """Analyze medical document or clinical image using Gemini Multimodal Vision."""
    if not settings.GEMINI_API_KEY or not settings.GEMINI_API_KEY.strip():
        raise ValueError("GEMINI_API_KEY is not configured")

    b64_data = base64.b64encode(data).decode("utf-8")
    data_url = f"data:{content_type};base64,{b64_data}"

    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY.strip(),
        temperature=0.1,
        max_output_tokens=2048,
    )
    msg = HumanMessage(
        content=[
            {"type": "text", "text": CLINICAL_VISION_PROMPT},
            {"type": "image_url", "image_url": data_url},
        ]
    )
    result = await llm.ainvoke([msg])
    return _format_llm_content(result.content).strip()


async def _extract_with_ai_vision(data: bytes, content_type: str) -> str:
    """Analyze medical image using Groq Vision (primary) or Gemini Vision (fallback)."""
    if settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip():
        try:
            return await _extract_with_groq_vision(data, content_type)
        except Exception as exc:
            logger.warning("Groq Vision extraction failed: %s", exc)
            if not (settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip()):
                raise

    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
        return await _extract_with_gemini_vision(data, content_type)

    raise ValueError("Neither GROQ_API_KEY nor GEMINI_API_KEY is configured.")


async def _extract_pdf(data: bytes) -> tuple[str, str | None]:
    try:
        reader = PdfReader(BytesIO(data), strict=False)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The PDF could not be read.") from exc
    if len(reader.pages) > settings.MAX_PDF_PAGES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF exceeds the {settings.MAX_PDF_PAGES}-page processing limit.",
        )

    # 1. Try digital text extraction first
    text_parts = [(page.extract_text() or "").strip() for page in reader.pages]
    text = "\n\n".join(part for part in text_parts if part)
    if text.strip():
        return text, None

    # 2. Scanned PDF: try extracting embedded page images with AI Vision
    pages_text: list[str] = []
    has_vision = bool((settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip()) or (settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip()))
    if has_vision:
        try:
            for page_idx, page in enumerate(reader.pages[:settings.MAX_PDF_PAGES], start=1):
                for img_obj in page.images:
                    try:
                        mime = "image/png" if img_obj.name.lower().endswith(".png") else "image/jpeg"
                        vision_text = await _extract_with_ai_vision(img_obj.data, mime)
                        if vision_text.strip():
                            pages_text.append(f"### Page {page_idx}\n{vision_text}")
                            break
                    except Exception as err:
                        logger.warning("Failed extracting page %s image with vision: %s", page_idx, err)
        except Exception as exc:
            logger.warning("Scanned PDF embedded image extraction error: %s", exc)

    if pages_text:
        provider = "Groq" if settings.GROQ_API_KEY else "Gemini"
        return "\n\n".join(pages_text), f"Extracted using MediAssist AI Vision ({provider}). Review before sending."

    # 3. Fallback: pdf2image + pytesseract if installed
    try:
        images = convert_from_bytes(
            data,
            first_page=1,
            last_page=min(len(reader.pages), settings.MAX_PDF_PAGES),
            dpi=150,
            fmt="png",
            thread_count=1,
        )
        # Try vision on rendered pages first
        if has_vision and images:
            for page_idx, img in enumerate(images, start=1):
                buf = BytesIO()
                img.save(buf, format="PNG")
                try:
                    p_text = await _extract_with_ai_vision(buf.getvalue(), "image/png")
                    if p_text.strip():
                        pages_text.append(f"### Page {page_idx}\n{p_text}")
                except Exception:
                    pass
            if pages_text:
                provider = "Groq" if settings.GROQ_API_KEY else "Gemini"
                return "\n\n".join(pages_text), f"Extracted using MediAssist AI Vision ({provider}). Review before sending."

        ocr_text = "\n\n".join(pytesseract.image_to_string(image) for image in images)
        if ocr_text.strip():
            return ocr_text, "Text was extracted with OCR and may contain recognition errors; review it before use."
    except Exception as exc:
        logger.warning("Scanned PDF convert/OCR fallback unavailable: %s", exc)

    return "", "No readable text or images found in this PDF. Check the document quality or enter your questions manually."


async def _extract_image(data: bytes, content_type: str = "image/jpeg") -> tuple[str, str | None]:
    try:
        image = Image.open(BytesIO(data))
        width, height = image.size
        if width <= 0 or height <= 0 or width * height > settings.MAX_IMAGE_PIXELS:
            raise HTTPException(status_code=413, detail="Image dimensions exceed the processing limit.")
        image.load()
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=400, detail="The image could not be decoded.") from exc

    # 1. Primary engine: AI Multimodal Vision (Groq Llama 3.2 Vision / Gemini Vision)
    has_vision = bool((settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip()) or (settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip()))
    if has_vision:
        try:
            extracted_text = await _extract_with_ai_vision(data, content_type)
            if extracted_text.strip():
                provider = "Groq" if (settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip()) else "Gemini"
                return extracted_text, f"Analyzed using MediAssist AI Vision ({provider}). Review details before sending."
        except Exception as exc:
            err_str = str(exc).lower()
            provider = "Groq" if (settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip()) else "Gemini"
            if "quota" in err_str or "resourceexhausted" in err_str or "429" in err_str or "rate_limit" in err_str:
                return "", f"{provider} AI Vision rate limit or quota reached. Check your API plan or enter questions manually."
            if "invalid_api_key" in err_str or "authentication" in err_str or "401" in err_str:
                return "", f"Invalid {provider} API key. Please check your API key in backend/.env."
            logger.warning("AI Vision extraction failed (%s): %s", type(exc).__name__, exc)

    # 2. Secondary fallback: local pytesseract OCR if available
    try:
        ocr_text = pytesseract.image_to_string(image.convert("RGB")).strip()
        if ocr_text:
            return ocr_text, "OCR may contain recognition errors; review the extracted text before use."
    except Exception as exc:
        logger.warning("Local OCR fallback unavailable (%s)", type(exc).__name__)

    hint = "Set GROQ_API_KEY in backend/.env for AI image analysis." if not has_vision else "You can describe your image or symptoms directly in the message."
    return "", f"No readable text or clinical details could be identified. {hint}"


@router.post("/extract", response_model=DocumentExtractResponse)
async def extract_document_text(
    file: UploadFile = File(...),
    current_user: User = Depends(require_health_information_consent),
):
    # The file is processed in memory and is never persisted.
    del current_user
    started = perf_counter()
    content_type = "unknown"
    outcome = "error"
    try:
        payload = await file.read(settings.MAX_UPLOAD_BYTES + 1)
        await file.close()
        if not payload:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")
        if len(payload) > settings.MAX_UPLOAD_BYTES:
            limit_mb = max(1, settings.MAX_UPLOAD_BYTES // (1024 * 1024))
            raise HTTPException(status_code=413, detail=f"File exceeds the {limit_mb} MB processing limit.")

        detected_type = detect_content_type(payload)
        content_type = detected_type or "unknown"
        if detected_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=415, detail="Upload a PDF, JPG, PNG, or WebP file.")

        if detected_type == "application/pdf":
            extracted_text, warning = await _extract_pdf(payload)
        else:
            extracted_text, warning = await _extract_image(payload, detected_type)

        truncated = len(extracted_text) > settings.MAX_ATTACHMENT_CHARS
        extracted_text = extracted_text[: settings.MAX_ATTACHMENT_CHARS]
        if truncated:
            warning = "Extracted text was truncated to the safe processing limit. " + (warning or "Review the available text before use.")

        outcome = "success" if extracted_text.strip() else "empty"
        # Do not log filename, extracted text, file content, or health information.
        logger.info("Transient document extraction completed (type=%s, bytes=%s)", detected_type, len(payload))
        return DocumentExtractResponse(
            filename=Path((file.filename or "uploaded-document").replace("\\", "/")).name[:200],
            content_type=detected_type,
            extracted_text=extracted_text,
            warning=warning,
        )
    except HTTPException as exc:
        outcome = "client_error" if exc.status_code < 500 else "error"
        raise
    except Exception:
        outcome = "error"
        raise
    finally:
        OCR_REQUESTS_TOTAL.labels(content_type=content_type, outcome=outcome).inc()
        OCR_DURATION_SECONDS.labels(content_type=content_type).observe(perf_counter() - started)
