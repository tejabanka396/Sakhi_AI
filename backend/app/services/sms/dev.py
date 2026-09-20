import logging
import sys
from typing import List, Tuple
from app.services.sms.base import SMSProvider
from app.core.config import settings
from app.core.phone import parse_and_validate_indian_phone

logger = logging.getLogger("sakhi_ai.sms.dev")

class DevSMSProvider(SMSProvider):
    """
    Secure Development SMS Provider.
    Used strictly in non-production environments when SMS_PROVIDER=dev.
    Does NOT send external SMS.
    Prints the generated 6-digit OTP exclusively to backend development logs/terminal.
    Hard-blocked if ENVIRONMENT=production.
    """
    def validate_configuration(self) -> List[str]:
        env = (settings.ENVIRONMENT or "").lower().strip()
        if env in ["production", "prod"]:
            return ["DevSMSProvider is strictly prohibited in production! Set SMS_PROVIDER=msg91"]
        return []

    async def send_otp(self, phone: str, otp: str) -> Tuple[bool, str]:
        env = (settings.ENVIRONMENT or "").lower().strip()
        if env in ["production", "prod"]:
            logger.critical("SECURITY VIOLATION: DevSMSProvider triggered in PRODUCTION environment!")
            return False, "Development SMS provider is disabled in production."

        parsed = parse_and_validate_indian_phone(phone)
        if not parsed.is_valid:
            logger.warning("DevSMSProvider received invalid phone: %s", phone[:4] + "..." if len(phone) > 4 else "...")
            return False, parsed.error_message or "Please enter a valid Indian mobile number."

        # Output ONLY to development logger and terminal
        border = "=" * 58
        logger.info("\n%s\n  [DEV SMS GATEWAY] Real SMS bypassed (DEV mode)\n  Recipient: %s (%s)\n  Verification Code (OTP): %s\n  Valid for: %d minutes\n%s",
                    border, parsed.display, parsed.e164, otp, settings.OTP_EXPIRE_MINUTES, border)

        # Ensure visible in local developer terminal even if loglevel is filtered
        try:
            print(
                f"\n{'=' * 58}\n"
                f"  [DEV OTP] Mobile: {parsed.display} ({parsed.e164})\n"
                f"  [DEV OTP] Verification Code: {otp}\n"
                f"  [DEV OTP] Valid for: {settings.OTP_EXPIRE_MINUTES} minutes\n"
                f"{'=' * 58}\n",
                file=sys.stderr,
                flush=True
            )
        except Exception:
            pass

        return True, f"Development OTP generated for {parsed.display}. Check backend logs."
