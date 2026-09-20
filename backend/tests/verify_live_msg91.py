"""
Live MSG91 SMS Delivery Verification Script
Run this script to verify real SMS delivery to your mobile phone:
    python tests/verify_live_msg91.py <YOUR_10_DIGIT_PHONE_NUMBER>
"""
import sys
import asyncio
from pathlib import Path

# Ensure backend root is on Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.core.phone import parse_and_validate_indian_phone
from app.services.sms.msg91 import MSG91Provider

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

async def verify_real_msg91_delivery(target_phone: str):
    print("=" * 60)
    print(" Sakhi AI -- Live MSG91 SMS Delivery Verification")
    print("=" * 60)

    # 1. Configuration check
    provider = MSG91Provider()
    missing = provider.validate_configuration()

    print(f"SMS Provider: {settings.SMS_PROVIDER}")
    print(f"Sender ID:    {settings.MSG91_SENDER_ID or '(None)'}")
    print(f"Auth Key:     {'[Configured]' if settings.MSG91_AUTH_KEY else '[MISSING]'}")
    print(f"Template ID:  {'[Configured]' if settings.MSG91_TEMPLATE_ID else '[MISSING]'}")
    print("-" * 60)

    if missing:
        print(f"[!] Configuration check: Missing {', '.join(missing)} in backend/.env")
        print("Please configure your real MSG91 credentials before running live delivery.")
        return False

    # 2. Phone validation
    parsed = parse_and_validate_indian_phone(target_phone)
    if not parsed.is_valid:
        print(f"[!] Phone validation error: {parsed.error_message}")
        return False

    print(f"[*] Target Phone: {parsed.display} (MSG91 Recipient: {parsed.msg91_recipient})")

    # 3. Generate sample 6-digit verification code
    import secrets
    test_otp = f"{secrets.randbelow(900000) + 100000}"
    print(f"[*] Generating secure 6-digit test OTP...")

    # 4. Dispatch via real MSG91 API
    print("[*] Calling MSG91 v5 API (https://control.msg91.com/api/v5/otp)...")
    success, message = await provider.send_otp(parsed.e164, test_otp)

    print("-" * 60)
    if success:
        print(f"[SUCCESS] {message}")
        print(f"Please check your mobile phone ({parsed.display}) now for the SMS!")
        return True
    else:
        print(f"[FAILED] Delivery response: {message}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tests/verify_live_msg91.py <10_DIGIT_INDIAN_PHONE_NUMBER>")
        sys.exit(1)

    phone_arg = sys.argv[1]
    asyncio.run(verify_real_msg91_delivery(phone_arg))
