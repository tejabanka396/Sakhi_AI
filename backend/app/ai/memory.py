import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger("sakhi_ai.memory")

# Sensitive keywords that must NEVER be saved to memory
SENSITIVE_PATTERNS = [
    r"password", r"otp", r"cvv", r"credit\s*card", r"debit\s*card",
    r"api[_-]?key", r"secret", r"pin\s*code", r"bank\s*account"
]

# Patterns that suggest long-term personal facts or learning preferences
MEMORY_CANDIDATE_PATTERNS = [
    (r"(?:my favorite|favorite|chala ishtam|ishtamaina)\s+([a-zA-Z0-9\s]+)", "preference"),
    (r"(?:i want to learn|nerchukovali|preparing for|exam undi|chaduvutunnanu)\s+([a-zA-Z0-9\s]+)", "learning"),
    (r"(?:my goal|aim|target|dream)\s+(?:is to|ante)\s+([a-zA-Z0-9\s]+)", "goal"),
    (r"(?:i work at|naaku job|studying in|college)\s+([a-zA-Z0-9\s]+)", "personal"),
    (r"(?:remember that|gurthupettuko|note chesuko)\s+([a-zA-Z0-9\s]+)", "personal"),
]

def extract_memory_from_message(message: str) -> Optional[Tuple[str, str]]:
    """
    Extracts high-value long-term memory candidates while strictly ignoring sensitive data.
    Returns (memory_text, category) if found, else None.
    """
    msg_lower = message.lower().strip()

    # Rule 1: Never store messages containing passwords, OTPs, or financial secrets
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, msg_lower):
            logger.info("Blocked memory extraction due to sensitive keyword.")
            return None

    # Rule 2: Ignore very short or purely greeting messages
    if len(message.strip().split()) < 3:
        return None

    # Rule 3: Check explicit remember trigger: "remember that ...", "gurthupettuko ..."
    remember_match = re.search(r"(?:remember that|gurthupettuko|remember this)\s*:?\s*(.+)", message, re.IGNORECASE)
    if remember_match:
        fact = remember_match.group(1).strip()
        if len(fact) > 3:
            return (fact, "personal")

    # Rule 4: Match long-term preferences / learning goals
    for pattern, category in MEMORY_CANDIDATE_PATTERNS:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            # Capture the sentence containing this preference
            return (message.strip(), category)

    return None
