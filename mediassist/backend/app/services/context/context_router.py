from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ContextDecision:
    use_medical_rag: bool = False
    use_personal_health: bool = False


class ContextRouter:
    MEDICAL_TERMS = (
        "health", "medical", "symptom", "headache", "migraine", "pain",
        "fever", "cough", "breathing", "rash", "disease", "condition",
        "medicine", "medication", "drug", "dose", "treatment", "diagnosis",
        "diabetes", "blood pressure", "infection", "therapy", "allergy",
        "pregnan", "injury", "wound", "bleed", "stroke", "chest",
        "doctor", "hospital", "lab result", "test result", "prescription",
    )
    PERSONAL_TERMS = (
        "my", "i am", "i have", "i feel", "i take", "i use", "for me",
        "based on me", "my family", "my child", "my doctor", "my result",
    )

    def route(self, message: str) -> ContextDecision:
        normalized = re.sub(r"\s+", " ", (message or "").lower()).strip()
        use_medical_rag = any(
            re.search(rf"\b{re.escape(term)}\w*\b", normalized)
            for term in self.MEDICAL_TERMS
        )
        use_personal_health = use_medical_rag and any(
            re.search(rf"\b{re.escape(term)}\b", normalized)
            for term in self.PERSONAL_TERMS
        )
        return ContextDecision(
            use_medical_rag=use_medical_rag,
            use_personal_health=use_personal_health,
        )


context_router = ContextRouter()
