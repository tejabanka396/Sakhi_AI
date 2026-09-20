import logging
from typing import List, Tuple
from app.services.sms.base import SMSProvider

logger = logging.getLogger("sakhi_ai.sms.mock")

class MockSMSProvider(SMSProvider):
    def __init__(self):
        self.sent_messages: List[dict] = []

    def validate_configuration(self) -> List[str]:
        return []

    async def send_otp(self, phone: str, otp: str) -> Tuple[bool, str]:
        # Never print the real OTP in production logs, only in debug mock
        self.sent_messages.append({"phone": phone, "otp": otp})
        logger.info(f"[MOCK SMS] OTP dispatched to {phone}")
        return True, "Mock OTP dispatched successfully."
