
import re


EMERGENCY_PATTERNS = {
    "chest_pain": [
        r"\bsevere chest pain\b",
        r"\bi (?:am )?having chest pain\b",
        r"\bi (?:am )?experiencing chest pain\b",
        r"\bi feel (?:severe )?pain in my chest\b",
        r"\bmy chest (?:hurts|is hurting)\b",
        r"\bpressure in my chest\b",
        r"\btightness in my chest\b",
        r"\bchest pain and (?:sweating|breathlessness|nausea)\b",
    ],

    "breathing_difficulty": [
        r"\bdifficulty breathing\b",
        r"\btrouble breathing\b",
        r"\bshortness of breath\b",
        r"\bcan't breathe\b",
        r"\bcannot breathe\b",
        r"\bstruggling to breathe\b",
        r"\bnot able to breathe\b",
        r"\b(?:he|she|they|my father|my mother|my friend) "
        r"(?:is|are) struggling to breathe\b",
    ],

    "stroke_signs": [
        r"\bface drooping\b",
        r"\bone[- ]sided weakness\b",
        r"\bweakness on one side\b",
        r"\bslurred speech\b",
        r"\bsudden trouble speaking\b",
        r"\bsudden loss of vision\b",
    ],

    "unconsciousness": [
        r"\bunconscious\b",
        r"\bnot responding\b",
        r"\bunresponsive\b",
        r"\bpassed out and won't wake\b",
        r"\bnot waking up\b",
    ],

    "severe_bleeding": [
        r"\bsevere bleeding\b",
        r"\bheavy bleeding\b",
        r"\bbleeding won't stop\b",
        r"\bbleeding that won't stop\b",
        r"\buncontrolled bleeding\b",
    ],

    "seizure": [
        r"\bhaving a seizure\b",
        r"\bseizure lasting\b",
        r"\bcontinuous seizure\b",
        r"\bseizures one after another\b",
    ],
    "other_urgent_signs": [
        r"\bheart attack\b",
        r"\b(?:overdose|poisoning)\b",
        r"\bchoking and (?:can't|cannot) breathe\b",
        r"\b(?:anaphylaxis|severe allergic reaction)\b",
        r"\b(?:throat|tongue) (?:is )?swelling\b",
    ],
}


EMERGENCY_RESPONSE = """
⚠️ **This may be a medical emergency.**

Please seek emergency medical care immediately.

- Contact your local emergency services now.
- In India, call 112 for emergency assistance.
- Go to the nearest emergency department.
- Do not wait for an online response or try home remedies first.

If someone is unconscious or having difficulty breathing,
seek emergency help immediately.
Medical Disclaimer: MediAssist cannot diagnose or replace
professional medical care.

"""


class EmergencyDetectionService:

    def detect_emergency(self, message: str) -> bool:

        if not message or not message.strip():
            return False

        normalized_message = message.lower()

        for patterns in EMERGENCY_PATTERNS.values():

            for pattern in patterns:

                if re.search(pattern, normalized_message):
                    return True

        return False


emergency_detection_service = EmergencyDetectionService()
