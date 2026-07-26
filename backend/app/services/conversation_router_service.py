import re
from dataclasses import dataclass
@dataclass(
    frozen=True,
    slots=True,
)
class ConversationReply:
    intent: str
    answer: str
def normalize_conversation_message(
    message: str,
) -> str:
    normalized = (
        message.casefold()
        .replace("\u2019", "'")
        .replace("\u2018", "'")
    )
    normalized = re.sub(
        r"[^\w\s'\u0980-\u09ff]",
        " ",
        normalized,
    )
    return re.sub(
        r"\s+",
        " ",
        normalized,
    ).strip()
def reply(
    intent: str,
    answer: str,
) -> ConversationReply:
    return ConversationReply(
        intent=intent,
        answer=answer,
    )
CONVERSATION_REPLIES: dict[
    str,
    ConversationReply,
] = {}
def register_replies(
    messages: tuple[str, ...],
    intent: str,
    answer: str,
) -> None:
    conversation_reply = reply(
        intent=intent,
        answer=answer,
    )
    for message in messages:
        normalized_message = (
            normalize_conversation_message(
                message
            )
        )
        CONVERSATION_REPLIES[
            normalized_message
        ] = conversation_reply
register_replies(
    (
        "hi",
        "hello",
        "hey",
        "hi there",
        "hello there",
        "hi sir",
        "hello sir",
    ),
    "greeting",
    (
        "Hello! How can I help you with "
        "your company policies today?"
    ),
)
register_replies(
    (
        "good morning",
        "good morning sir",
        "morning",
    ),
    "greeting",
    (
        "Good morning! How can I assist "
        "you with company policies today?"
    ),
)
register_replies(
    ("good afternoon",),
    "greeting",
    (
        "Good afternoon! How can I assist "
        "you with company policies today?"
    ),
)
register_replies(
    ("good evening",),
    "greeting",
    (
        "Good evening! How can I assist "
        "you with company policies today?"
    ),
)
register_replies(
    (
        "assalamu alaikum",
        "assalamualaikum",
        "salam",
    ),
    "greeting",
    (
        "Wa alaikum assalam! How can I "
        "assist you today?"
    ),
)
register_replies(
    (
        "how are you",
        "how are you doing",
        "how r u",
    ),
    "greeting",
    (
        "I am ready to assist. What would "
        "you like to know about your "
        "company policies?"
    ),
)
register_replies(
    (
        "what's up",
        "whats up",
        "what is up",
        "sup",
    ),
    "greeting",
    (
        "Hello! I am ready to help with "
        "company policies and HR-related "
        "questions."
    ),
)
register_replies(
    (
        "thanks",
        "thank you",
        "thank you so much",
        "many thanks",
    ),
    "gratitude",
    "You're welcome!",
)
register_replies(
    (
        "ok",
        "okay",
        "alright",
        "all right",
        "got it",
        "understood",
    ),
    "acknowledgement",
    (
        "Understood. What would you like "
        "to check next?"
    ),
)
register_replies(
    (
        "bye",
        "goodbye",
        "see you",
        "see you later",
    ),
    "farewell",
    "Goodbye! Have a great day.",
)
register_replies(
    ("good night",),
    "farewell",
    "Good night! Take care.",
)
register_replies(
    (
        "\u09b9\u09be\u0987",
        "\u09b9\u09cd\u09af\u09be\u09b2\u09cb",
        "\u09b9\u09c7\u09b2\u09cb",
    ),
    "greeting",
    (
        "\u09b9\u09cd\u09af\u09be\u09b2\u09cb! "
        "\u0986\u099c \u0995\u09cb\u09ae\u09cd"
        "\u09aa\u09be\u09a8\u09bf\u09b0 "
        "\u09a8\u09c0\u09a4\u09bf\u09ae\u09be"
        "\u09b2\u09be \u09b8\u09ae\u09cd\u09aa"
        "\u09b0\u09cd\u0995\u09c7 \u0995\u09c0 "
        "\u099c\u09be\u09a8\u09a4\u09c7 "
        "\u099a\u09be\u09a8?"
    ),
)
register_replies(
    (
        "\u09b6\u09c1\u09ad \u09b8\u0995\u09be\u09b2",
        "\u09b8\u09c1\u09aa\u09cd\u09b0\u09ad\u09be\u09a4",
    ),
    "greeting",
    (
        "\u09b6\u09c1\u09ad \u09b8\u0995\u09be"
        "\u09b2! \u0986\u099c \u0995\u09c0\u09ad"
        "\u09be\u09ac\u09c7 \u09b8\u09b9\u09be"
        "\u09df\u09a4\u09be \u0995\u09b0\u09a4"
        "\u09c7 \u09aa\u09be\u09b0\u09bf?"
    ),
)
register_replies(
    (
        "\u0986\u09b8\u09b8\u09be\u09b2\u09be\u09ae\u09c1 "
        "\u0986\u09b2\u09be\u0987\u0995\u09c1\u09ae",
        "\u09b8\u09be\u09b2\u09be\u09ae",
    ),
    "greeting",
    (
        "\u0993\u09df\u09be\u09b2\u09be\u0987"
        "\u0995\u09c1\u09ae \u0986\u09b8\u09b8"
        "\u09be\u09b2\u09be\u09ae! \u0986\u099c "
        "\u0995\u09c0\u09ad\u09be\u09ac\u09c7 "
        "\u09b8\u09b9\u09be\u09df\u09a4\u09be "
        "\u0995\u09b0\u09a4\u09c7 \u09aa\u09be"
        "\u09b0\u09bf?"
    ),
)
register_replies(
    (
        "\u0995\u09c7\u09ae\u09a8 \u0986\u099b\u09c7\u09a8",
    ),
    "greeting",
    (
        "\u0986\u09ae\u09bf \u09b8\u09b9\u09be"
        "\u09df\u09a4\u09be \u0995\u09b0\u09be"
        "\u09b0 \u099c\u09a8\u09cd\u09af "
        "\u09aa\u09cd\u09b0\u09b8\u09cd\u09a4"
        "\u09c1\u09a4\u0964 \u0995\u09cb\u09ae"
        "\u09cd\u09aa\u09be\u09a8\u09bf\u09b0 "
        "\u09a8\u09c0\u09a4\u09bf\u09ae\u09be"
        "\u09b2\u09be \u09b8\u09ae\u09cd\u09aa"
        "\u09b0\u09cd\u0995\u09c7 \u0995\u09c0 "
        "\u099c\u09be\u09a8\u09a4\u09c7 "
        "\u099a\u09be\u09a8?"
    ),
)
register_replies(
    (
        "\u0995\u09bf \u0996\u09ac\u09b0",
        "\u0995\u09c0 \u0996\u09ac\u09b0",
    ),
    "greeting",
    (
        "\u0986\u09ae\u09bf \u0995\u09cb\u09ae"
        "\u09cd\u09aa\u09be\u09a8\u09bf\u09b0 "
        "\u09a8\u09c0\u09a4\u09bf\u09ae\u09be"
        "\u09b2\u09be \u098f\u09ac\u0982 HR-"
        "\u09b8\u0982\u0995\u09cd\u09b0\u09be"
        "\u09a8\u09cd\u09a4 \u09aa\u09cd\u09b0"
        "\u09b6\u09cd\u09a8\u09c7 \u09b8\u09b9"
        "\u09be\u09df\u09a4\u09be \u0995\u09b0"
        "\u09be\u09b0 \u099c\u09a8\u09cd\u09af "
        "\u09aa\u09cd\u09b0\u09b8\u09cd\u09a4"
        "\u09c1\u09a4\u0964"
    ),
)
register_replies(
    (
        "\u09a7\u09a8\u09cd\u09af\u09ac\u09be\u09a6",
        "\u0985\u09a8\u09c7\u0995 "
        "\u09a7\u09a8\u09cd\u09af\u09ac\u09be\u09a6",
    ),
    "gratitude",
    (
        "\u0986\u09aa\u09a8\u09be\u0995\u09c7 "
        "\u09b8\u09cd\u09ac\u09be\u0997\u09a4\u09ae!"
    ),
)
register_replies(
    (
        "\u09a0\u09bf\u0995 \u0986\u099b\u09c7",
        "\u0986\u099a\u09cd\u099b\u09be",
        "\u09ac\u09c1\u099d\u09c7\u099b\u09bf",
    ),
    "acknowledgement",
    (
        "\u09ac\u09c1\u099d\u09c7\u099b\u09bf"
        "\u0964 \u098f\u09b0\u09aa\u09b0 "
        "\u0995\u09cb\u09a8 \u09ac\u09bf\u09b7"
        "\u09df\u099f\u09bf \u09af\u09be\u099a"
        "\u09be\u0987 \u0995\u09b0\u09a4\u09c7 "
        "\u099a\u09be\u09a8?"
    ),
)
register_replies(
    (
        "\u09ac\u09bf\u09a6\u09be\u09af\u09bc",
    ),
    "farewell",
    (
        "\u09ac\u09bf\u09a6\u09be\u09df! "
        "\u0986\u09aa\u09a8\u09be\u09b0 "
        "\u09a6\u09bf\u09a8\u099f\u09bf "
        "\u09b8\u09c1\u09a8\u09cd\u09a6\u09b0 "
        "\u09b9\u09cb\u0995\u0964"
    ),
)
register_replies(
    (
        "\u0986\u09b2\u09cd\u09b2\u09be\u09b9 "
        "\u09b9\u09be\u09ab\u09c7\u099c",
    ),
    "farewell",
    (
        "\u0986\u09b2\u09cd\u09b2\u09be\u09b9 "
        "\u09b9\u09be\u09ab\u09c7\u099c! "
        "\u09ad\u09be\u09b2\u09cb \u09a5\u09be"
        "\u0995\u09ac\u09c7\u09a8\u0964"
    ),
)
def get_conversation_reply(
    message: str,
) -> ConversationReply | None:
    normalized_message = (
        normalize_conversation_message(
            message
        )
    )
    return CONVERSATION_REPLIES.get(
        normalized_message
    )
