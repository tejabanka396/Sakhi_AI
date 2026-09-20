import re
import logging
from typing import List, Tuple
import httpx
from app.services.sms.base import SMSProvider
from app.core.config import settings

logger = logging.getLogger("sakhi_ai.sms.twilio")

class TwilioProvider(SMSProvider):
    def __init__(
        self,
        account_sid: str = "",
        auth_token: str = "",
        from_phone: str = ""
    ):
        self.account_sid = account_sid or settings.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or settings.TWILIO_AUTH_TOKEN
        self.from_phone = from_phone or settings.TWILIO_FROM_PHONE

    def validate_configuration(self) -> List[str]:
        missing = []
        if not self.account_sid:
            missing.append("TWILIO_ACCOUNT_SID")
        if not self.auth_token:
            missing.append("TWILIO_AUTH_TOKEN")
        if not self.from_phone:
            missing.append("TWILIO_FROM_PHONE")
        return missing

    def _normalize_phone(self, phone: str) -> str:
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            return f"+91{digits}"
        if not phone.startswith("+"):
            return f"+{digits}"
        return phone

    async def send_otp(self, phone: str, otp: str) -> Tuple[bool, str]:
        missing = self.validate_configuration()
        if missing:
            err = f"Twilio credentials missing in .env: {', '.join(missing)}"
            logger.error(err)
            return False, err

        recipient = self._normalize_phone(phone)
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

        data = {
            "From": self.from_phone,
            "To": recipient,
            "Body": f"Your Sakhi AI verification code is {otp}. Valid for 5 minutes. Do not share this code."
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    data=data,
                    auth=(self.account_sid, self.auth_token)
                )
                if response.status_code in [200, 201]:
                    logger.info(f"Twilio dispatched OTP to {recipient[:6]}****")
                    return True, "OTP dispatched successfully via Twilio."
                else:
                    msg = f"Twilio returned HTTP {response.status_code}: {response.text}"
                    logger.error(msg)
                    return False, msg
        except Exception as e:
            logger.error(f"Twilio connection error: {e}", exc_info=True)
            return False, f"Twilio network error: {str(e)}"
