import logging
from typing import Tuple, Optional
from app.core.config import settings
from app.services.sms.base import SMSProvider
from app.services.sms.msg91 import MSG91Provider
from app.services.sms.twilio import TwilioProvider
from app.services.sms.mock import MockSMSProvider
from app.services.sms.dev import DevSMSProvider

logger = logging.getLogger("sakhi_ai.sms.service")

class SMSService:
    def __init__(self):
        self._provider: Optional[SMSProvider] = None

    def set_provider(self, provider: Optional[SMSProvider]) -> None:
        self._provider = provider

    def get_provider(self) -> SMSProvider:
        if self._provider is not None:
            return self._provider
        provider_name = (settings.SMS_PROVIDER or "msg91").lower().strip()
        if provider_name == "msg91":
            return MSG91Provider()
        elif provider_name in ["dev", "development"]:
            # Strictly forbid DEV provider in production
            env = (settings.ENVIRONMENT or "").lower().strip()
            if env in ["production", "prod"]:
                logger.critical("DevSMSProvider blocked in production! Defaulting to MSG91.")
                return MSG91Provider()
            return DevSMSProvider()
        elif provider_name == "twilio":
            return TwilioProvider()
        elif provider_name in ["mock", "test"]:
            self._provider = MockSMSProvider()
            return self._provider
        else:
            logger.warning(f"Unknown SMS provider '{provider_name}'. Defaulting to MSG91.")
            return MSG91Provider()

    async def send_otp(self, phone: str, otp: str) -> Tuple[bool, str]:
        """
        Dispatches OTP to phone using configured SMS provider.
        """
        provider = self.get_provider()
        missing_vars = provider.validate_configuration()
        if missing_vars:
            logger.error(
                "SMS provider '%s' is missing configuration in .env: %s",
                settings.SMS_PROVIDER,
                ", ".join(missing_vars)
            )
            return False, "SMS service is not configured. Please configure MSG91 credentials."

        return await provider.send_otp(phone=phone, otp=otp)

sms_service = SMSService()
