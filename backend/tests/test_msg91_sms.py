import pytest
import secrets
from unittest.mock import AsyncMock, patch
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.core.phone import parse_and_validate_indian_phone
from app.services.sms.msg91 import MSG91Provider
from app.services.sms.service import sms_service
from app.services.sms.mock import MockSMSProvider

client = TestClient(app)

def test_indian_phone_parsing_and_normalization():
    # 1. Standard 10-digit
    res = parse_and_validate_indian_phone("9014722400")
    assert res.is_valid is True
    assert res.core_digits == "9014722400"
    assert res.e164 == "+919014722400"
    assert res.msg91_recipient == "919014722400"
    assert res.display == "+91 90147 22400"

    # 2. 11-digit with leading 0
    res_zero = parse_and_validate_indian_phone("09014722400")
    assert res_zero.is_valid is True
    assert res_zero.core_digits == "9014722400"
    assert res_zero.e164 == "+919014722400"
    assert res_zero.msg91_recipient == "919014722400"

    # 3. 12-digit with 91 prefix
    res_91 = parse_and_validate_indian_phone("919014722400")
    assert res_91.is_valid is True
    assert res_91.core_digits == "9014722400"

    # 4. E.164 with +91 and spaces/dashes
    res_formatted = parse_and_validate_indian_phone("+91 90147-22400")
    assert res_formatted.is_valid is True
    assert res_formatted.core_digits == "9014722400"

    # 5. Invalid: does not start with 6-9
    res_invalid_prefix = parse_and_validate_indian_phone("1014722400")
    assert res_invalid_prefix.is_valid is False
    assert "starting with 6, 7, 8, or 9" in res_invalid_prefix.error_message

    # 6. Invalid: incorrect number of digits
    res_short = parse_and_validate_indian_phone("9014722")
    assert res_short.is_valid is False
    assert "valid 10-digit" in res_short.error_message

def test_msg91_provider_configuration_validation():
    # Unconfigured provider
    provider = MSG91Provider(auth_key="", template_id="", sender_id="")
    missing = provider.validate_configuration()
    assert "MSG91_AUTH_KEY" in missing
    assert "MSG91_TEMPLATE_ID" in missing

    # Placeholder values treated as unconfigured
    provider_placeholder = MSG91Provider(
        auth_key="your_msg91_auth_key_here",
        template_id="your_msg91_dlt_template_id_here"
    )
    assert len(provider_placeholder.validate_configuration()) == 2

    # Valid configurations
    provider_valid = MSG91Provider(auth_key="real_key_123", template_id="template_456")
    assert len(provider_valid.validate_configuration()) == 0

@pytest.mark.asyncio
async def test_msg91_send_otp_success():
    provider = MSG91Provider(auth_key="test_authkey", template_id="test_template", sender_id="SAKHIA")

    # Mock successful HTTP 200 response from MSG91
    mock_response = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json"},
        json={"type": "success", "message": "req_abc12345"}
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        success, msg = await provider.send_otp("+91 90147 22400", "567890")
        assert success is True
        assert "successfully" in msg

        # Verify exact request parameters sent to MSG91
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["headers"]["authkey"] == "test_authkey"
        assert call_kwargs["params"]["template_id"] == "test_template"
        assert call_kwargs["params"]["mobile"] == "919014722400"
        assert call_kwargs["params"]["otp"] == "567890"
        assert call_kwargs["params"]["sender"] == "SAKHIA"
        assert call_kwargs["json"]["otp"] == "567890"

@pytest.mark.asyncio
async def test_msg91_send_otp_failure_cases():
    provider = MSG91Provider(auth_key="test_authkey", template_id="test_template")

    # 1. MSG91 returns HTTP 200 with error type (critical bug regression test)
    mock_error_resp = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json"},
        json={"type": "error", "message": "Authentication failed"}
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_error_resp
        success, msg = await provider.send_otp("9014722400", "123456")
        assert success is False
        assert "authentication failed" in msg.lower()

    # 2. Template not approved in DLT
    mock_template_err = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json"},
        json={"type": "error", "message": "Template ID not found or DLT unapproved"}
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_template_err
        success, msg = await provider.send_otp("9014722400", "123456")
        assert success is False
        assert "template" in msg.lower()

    # 3. Network timeout
    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout")):
        success, msg = await provider.send_otp("9014722400", "123456")
        assert success is False
        assert "timed out" in msg.lower()

def test_api_unconfigured_sms_returns_clean_error():
    # Force unconfigured MSG91 provider
    unconfigured_provider = MSG91Provider(auth_key="", template_id="")
    sms_service.set_provider(unconfigured_provider)

    res = client.post("/api/auth/phone/request-otp", json={"phone": "9014722400"})
    assert res.status_code == 503
    data = res.json()
    # Must NOT leak MSG91_AUTH_KEY or raw env variable names to client!
    assert "MSG91_AUTH_KEY" not in data["detail"]
    assert "MSG91_TEMPLATE_ID" not in data["detail"]
    assert "SMS service is not configured" in data["detail"]

def test_api_phone_otp_security_workflow():
    mock_provider = MockSMSProvider()
    sms_service.set_provider(mock_provider)

    test_phone = f"+919{secrets.randbelow(900000000) + 100000000}"

    # 1. Invalid phone format rejected (422 for length or 400 for prefix)
    res_bad = client.post("/api/auth/phone/request-otp", json={"phone": "12345"})
    assert res_bad.status_code in (400, 422)

    res_bad_prefix = client.post("/api/auth/phone/request-otp", json={"phone": "1234567890"})
    assert res_bad_prefix.status_code == 400
    assert "starting with 6, 7, 8, or 9" in res_bad_prefix.json()["detail"]

    # 2. Request OTP succeeds
    res_ok = client.post("/api/auth/phone/request-otp", json={"phone": test_phone})
    assert res_ok.status_code == 200
    assert "debug_otp" not in res_ok.json()
    assert "raw_otp" not in res_ok.json()
    sent_otp = mock_provider.sent_messages[-1]["otp"]
    assert len(sent_otp) == 6

    # 3. Rate limiting enforced (HTTP 429)
    res_rate = client.post("/api/auth/phone/request-otp", json={"phone": test_phone})
    assert res_rate.status_code == 429
    assert "seconds before requesting" in res_rate.json()["detail"]

    # 4. Invalid OTP increments attempts and tells remaining attempts
    res_wrong = client.post("/api/auth/phone/verify-otp", json={
        "phone": test_phone,
        "otp": "000000"
    })
    assert res_wrong.status_code == 400
    assert "4 attempts remaining" in res_wrong.json()["detail"]

    # 5. Exhaust remaining attempts (total 5)
    for _ in range(4):
        client.post("/api/auth/phone/verify-otp", json={"phone": test_phone, "otp": "000000"})

    # 6th attempt with CORRECT OTP is locked out
    res_locked = client.post("/api/auth/phone/verify-otp", json={
        "phone": test_phone,
        "otp": sent_otp
    })
    assert res_locked.status_code == 400
    assert "too many invalid attempts" in res_locked.json()["detail"].lower()

def test_otp_expiry_and_replay_prevention():
    from datetime import datetime, timedelta, timezone
    from app.database.database import get_db
    from app.database.models import OTPVerification
    from app.services.sms.service import sms_service
    from app.services.sms.mock import MockSMSProvider

    mock_provider = MockSMSProvider()
    sms_service.set_provider(mock_provider)

    test_core = f"9{secrets.randbelow(900000000) + 100000000}"
    phone_with_zero = f"0{test_core}"
    phone_canonical = f"+91{test_core}"

    # Request with 11-digit leading 0 format
    req = client.post("/api/auth/phone/request-otp", json={"phone": phone_with_zero})
    assert req.status_code == 200
    sent_otp = mock_provider.sent_messages[-1]["otp"]

    # 1. Simulate expiration by updating expires_at to 10 minutes in the past
    db = next(get_db())
    db.query(OTPVerification).filter(
        OTPVerification.phone == phone_canonical
    ).update({"expires_at": datetime.now(timezone.utc) - timedelta(minutes=10)})
    db.commit()

    # Expired OTP should be rejected
    res_expired = client.post("/api/auth/phone/verify-otp", json={
        "phone": phone_canonical,
        "otp": sent_otp
    })
    assert res_expired.status_code == 400
    assert "expired" in res_expired.json()["detail"].lower()

    # 2. Reset expiry to valid future time for testing verification and replay
    db.query(OTPVerification).filter(
        OTPVerification.phone == phone_canonical
    ).update({"expires_at": datetime.now(timezone.utc) + timedelta(minutes=5), "attempts": 0})
    db.commit()

    # Verify using 10-digit raw format
    res_verify = client.post("/api/auth/phone/verify-otp", json={
        "phone": test_core,
        "otp": sent_otp
    })
    assert res_verify.status_code == 200
    data = res_verify.json()
    assert "access_token" in data
    assert data["user"]["phone"] == phone_canonical

    # 3. Replay attack test: Trying to verify the same OTP again should fail!
    res_replay = client.post("/api/auth/phone/verify-otp", json={
        "phone": test_core,
        "otp": sent_otp
    })
    assert res_replay.status_code == 400
    assert "no active otp" in res_replay.json()["detail"].lower()

def test_dev_sms_provider_workflow_and_security(monkeypatch):
    import io
    from app.services.sms.service import sms_service
    from app.services.sms.dev import DevSMSProvider
    from app.core.config import settings

    monkeypatch.setattr(settings, "SMS_PROVIDER", "dev")
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    sms_service.set_provider(None)  # reset cached provider

    provider = sms_service.get_provider()
    assert isinstance(provider, DevSMSProvider)

    # Capture stderr where DEV OTP is printed
    captured_stderr = io.StringIO()
    monkeypatch.setattr("sys.stderr", captured_stderr)

    test_phone = f"+919{secrets.randbelow(900000000) + 100000000}"

    # 1. Request DEV OTP
    res_req = client.post("/api/auth/phone/request-otp", json={"phone": test_phone})
    assert res_req.status_code == 200
    # Make sure OTP is never in response
    assert "debug_otp" not in res_req.json()
    assert "raw_otp" not in res_req.json()

    # Read the OTP from captured stderr
    output = captured_stderr.getvalue()
    assert "[DEV OTP]" in output
    import re
    match = re.search(r"Verification Code:\s*(\d{6})", output)
    assert match is not None
    dev_otp = match.group(1)

    # 2. Rate limiting enforced (429)
    res_cooldown = client.post("/api/auth/phone/request-otp", json={"phone": test_phone})
    assert res_cooldown.status_code == 429

    # 3. Verify with correct DEV OTP
    res_verify = client.post("/api/auth/phone/verify-otp", json={
        "phone": test_phone,
        "otp": dev_otp
    })
    assert res_verify.status_code == 200
    assert "access_token" in res_verify.json()

def test_dev_sms_provider_strictly_blocked_in_production(monkeypatch):
    from app.services.sms.service import sms_service
    from app.services.sms.dev import DevSMSProvider
    from app.services.sms.msg91 import MSG91Provider
    from app.core.config import settings

    # In production, DevSMSProvider must refuse to operate
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "SMS_PROVIDER", "dev")
    sms_service.set_provider(None)

    # SMSService should block DevSMSProvider and default to MSG91Provider
    resolved_provider = sms_service.get_provider()
    assert isinstance(resolved_provider, MSG91Provider)

    # Direct instantiation of DevSMSProvider in production also fails validation
    direct_dev = DevSMSProvider()
    missing = direct_dev.validate_configuration()
    assert len(missing) > 0
    assert "strictly prohibited in production" in missing[0]


