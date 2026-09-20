import logging
from typing import List, Tuple
import httpx
from app.services.sms.base import SMSProvider
from app.core.config import settings
from app.core.phone import parse_and_validate_indian_phone

logger = logging.getLogger("sakhi_ai.sms.msg91")

DUMMY_PLACEHOLDERS = {
    "your_msg91_auth_key_here",
    "your_msg91_dlt_template_id_here",
    "your_key",
    "your_template_id",
    "your_sender_id",
    "placeholder"
}

class MSG91Provider(SMSProvider):
    def __init__(
        self,
        auth_key: str = "",
        template_id: str = "",
        sender_id: str = ""
    ):
        self.auth_key = (auth_key or settings.MSG91_AUTH_KEY).strip()
        self.template_id = (template_id or settings.MSG91_TEMPLATE_ID).strip()
        self.sender_id = (sender_id or settings.MSG91_SENDER_ID).strip()

    def validate_configuration(self) -> List[str]:
        missing = []
        if not self.auth_key or self.auth_key.lower() in DUMMY_PLACEHOLDERS:
            missing.append("MSG91_AUTH_KEY")
        if not self.template_id or self.template_id.lower() in DUMMY_PLACEHOLDERS:
            missing.append("MSG91_TEMPLATE_ID")
        return missing

    async def send_otp(self, phone: str, otp: str) -> Tuple[bool, str]:
        missing = self.validate_configuration()
        if missing:
            logger.error("MSG91 configuration incomplete in .env: missing %s", ", ".join(missing))
            return False, "SMS service is not configured. Please configure MSG91 credentials."

        # Validate and normalize Indian mobile phone number
        parsed = parse_and_validate_indian_phone(phone)
        if not parsed.is_valid:
            masked = phone[:4] + "****" if len(phone) > 4 else "***"
            logger.warning("Attempted to send OTP to invalid Indian mobile number: %s", masked)
            return False, parsed.error_message or "Please provide a valid 10-digit Indian mobile number."

        recipient = parsed.msg91_recipient  # e.g., '919014722400'
        url = "https://control.msg91.com/api/v5/otp"

        headers = {
            "authkey": self.auth_key,
            "Content-Type": "application/json"
        }

        params = {
            "template_id": self.template_id,
            "mobile": recipient,
            "otp": otp,
            "otp_expiry": str(settings.OTP_EXPIRE_MINUTES)
        }
        if self.sender_id:
            params["sender"] = self.sender_id

        # Pass dynamic parameters in JSON body for DLT/MSG91 templates
        payload = {
            "otp": otp,
            "OTP": otp
        }

        masked_phone = f"{recipient[:4]}******{recipient[-2:]}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, params=params, json=payload)
                res_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}

                # Check for MSG91 explicit error responses
                if res_data.get("type") == "error":
                    error_msg = res_data.get("message") or f"MSG91 error (HTTP {response.status_code})"
                    logger.error("MSG91 API error for %s: %s", masked_phone, error_msg)

                    lowered = str(error_msg).lower()
                    if "authkey" in lowered or "ip not" in lowered or "unauthorized" in lowered:
                        return False, "SMS provider authentication failed. Please verify MSG91 Auth Key."
                    elif "template" in lowered or "dlt" in lowered:
                        return False, "SMS template configuration is invalid or pending DLT approval in MSG91."
                    elif "balance" in lowered or "credit" in lowered:
                        return False, "SMS provider balance insufficient. Please check MSG91 account."
                    else:
                        return False, f"SMS delivery rejected: {error_msg}"

                # Successful dispatch check
                if response.status_code in [200, 201] and (
                    res_data.get("type") == "success" or "request_id" in res_data
                ):
                    req_id = res_data.get("message") or res_data.get("request_id") or "ok"
                    logger.info("MSG91 successfully dispatched OTP to %s (req_id: %s)", masked_phone, req_id)
                    return True, "OTP dispatched successfully via MSG91."

                # Fallback success check if provider returned 200 without error type
                if response.status_code in [200, 201] and res_data.get("type") != "error":
                    logger.info("MSG91 dispatched OTP to %s (HTTP %s)", masked_phone, response.status_code)
                    return True, "OTP dispatched successfully via MSG91."

                err_msg = res_data.get("message") or f"MSG91 returned HTTP {response.status_code}"
                logger.error("MSG91 unexpected failure for %s: %s", masked_phone, err_msg)
                return False, f"SMS gateway returned an error: {err_msg}"

        except httpx.TimeoutException:
            logger.error("MSG91 request timed out for %s", masked_phone)
            return False, "SMS gateway timed out. Please try again in a moment."
        except Exception as e:
            logger.error("MSG91 network connection error for %s: %s", masked_phone, e)
            return False, "Unable to connect to SMS service. Please try again shortly."
