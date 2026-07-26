from backend.app.services.conversation_router_service import (
    get_conversation_reply,
)
def test_router_handles_supported_casual_messages() -> None:
    messages = [
        "Hello!",
        "GOOD MORNING",
        "What's up?",
        "Thank you.",
        "OK",
        "Bye!",
        "\u09b9\u09cd\u09af\u09be\u09b2\u09cb",
        "\u09a7\u09a8\u09cd\u09af\u09ac\u09be\u09a6",
        "\u09a0\u09bf\u0995 \u0986\u099b\u09c7",
    ]
    for message in messages:
        conversation_reply = (
            get_conversation_reply(
                message
            )
        )
        assert conversation_reply is not None
        assert conversation_reply.answer.strip()
def test_router_does_not_capture_mixed_policy_question() -> None:
    conversation_reply = get_conversation_reply(
        (
            "Good morning, what is the "
            "maternity leave policy?"
        )
    )
    assert conversation_reply is None
def test_router_handles_bengali_greeting() -> None:
    conversation_reply = get_conversation_reply(
        "\u09b9\u09be\u0987"
    )
    assert conversation_reply is not None
    assert conversation_reply.intent == "greeting"
    assert conversation_reply.answer.startswith(
        "\u09b9\u09cd\u09af\u09be\u09b2\u09cb"
    )
