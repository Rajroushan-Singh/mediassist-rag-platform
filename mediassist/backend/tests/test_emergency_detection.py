from app.services.emergency_detection import EmergencyDetectionService


def test_detects_urgent_breathing_emergency():
    service = EmergencyDetectionService()
    assert service.detect_emergency("My father is struggling to breathe")


def test_detects_severe_chest_pain():
    service = EmergencyDetectionService()
    assert service.detect_emergency("I am having chest pain")


def test_does_not_flag_general_headache_question():
    service = EmergencyDetectionService()
    assert not service.detect_emergency("What are common causes of a mild headache?")


def test_empty_message_is_not_an_emergency_match():
    service = EmergencyDetectionService()
    assert not service.detect_emergency("   ")
