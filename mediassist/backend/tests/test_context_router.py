from app.services.context.context_router import ContextRouter


def test_routes_general_health_question_to_rag():
    decision = ContextRouter().route("What can cause headaches?")
    assert decision.use_medical_rag
    assert not decision.use_personal_health


def test_routes_personal_medical_question_to_both_contexts():
    decision = ContextRouter().route("I am taking a medication and have a rash")
    assert decision.use_medical_rag
    assert decision.use_personal_health


def test_greeting_does_not_retrieve_health_context():
    decision = ContextRouter().route("Hello there")
    assert not decision.use_medical_rag
    assert not decision.use_personal_health


def test_keyword_inside_other_word_does_not_trigger_retrieval():
    decision = ContextRouter().route("I visited Spain last year")
    assert not decision.use_medical_rag
