import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth_full_lifecycle_and_isolation():
    # 1. Register User A
    user_a_email = f"user_a_{uuid.uuid4().hex[:6]}@example.com"
    reg_a = client.post("/api/auth/register", json={
        "name": "User Alpha",
        "email": user_a_email,
        "password": "PasswordA123!"
    })
    assert reg_a.status_code == 200
    data_a = reg_a.json()
    token_a = data_a["access_token"]
    refresh_a = data_a["refresh_token"]
    user_a_id = data_a["user"]["id"]
    assert data_a["user"]["name"] == "User Alpha"
    assert "friend_profile" in data_a

    # 2. Duplicate registration rejected
    dup_res = client.post("/api/auth/register", json={
        "name": "User Alpha Copy",
        "email": user_a_email,
        "password": "OtherPassword123"
    })
    assert dup_res.status_code == 400

    # 3. Invalid password login rejected
    bad_login = client.post("/api/auth/login", json={
        "email": user_a_email,
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401

    # 4. Valid login succeeded
    good_login = client.post("/api/auth/login", json={
        "email": user_a_email,
        "password": "PasswordA123!"
    })
    assert good_login.status_code == 200
    assert "access_token" in good_login.json()

    # 5. Refresh token works
    refresh_res = client.post("/api/auth/refresh", json={
        "refresh_token": refresh_a
    })
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()

    # 6. User profile me endpoint
    me_res = client.get("/api/users/me", headers={"Authorization": f"Bearer {token_a}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == user_a_email

    # 7. Update friend profile for User A
    friend_res = client.put("/api/friend/profile", headers={"Authorization": f"Bearer {token_a}"}, json={
        "friend_name": "Anu",
        "gender": "female",
        "voice_id": "female_friendly"
    })
    assert friend_res.status_code == 200
    assert friend_res.json()["friend_name"] == "Anu"

    # 8. Register User B
    user_b_email = f"user_b_{uuid.uuid4().hex[:6]}@example.com"
    reg_b = client.post("/api/auth/register", json={
        "name": "User Beta",
        "email": user_b_email,
        "password": "PasswordB123!"
    })
    assert reg_b.status_code == 200
    token_b = reg_b.json()["access_token"]

    # 9. Verify User B gets User B's friend profile (Sakhi, not Anu!)
    friend_b_res = client.get("/api/friend/profile", headers={"Authorization": f"Bearer {token_b}"})
    assert friend_b_res.status_code == 200
    assert friend_b_res.json()["friend_name"] == "Sakhi"  # User isolation verified!

    # 10. Test Phone OTP flow with Mock SMS Provider
    from app.services.sms.service import sms_service
    from app.services.sms.mock import MockSMSProvider
    from app.core.config import settings

    mock_provider = MockSMSProvider()
    sms_service.set_provider(mock_provider)

    phone_num = f"+919{secrets_rand_digits()}"
    otp_req = client.post("/api/auth/phone/request-otp", json={"phone": phone_num})
    assert otp_req.status_code == 200
    assert "debug_otp" not in otp_req.json()
    assert len(mock_provider.sent_messages) == 1
    sent_otp = mock_provider.sent_messages[-1]["otp"]

    # Immediate duplicate request should be rate-limited (429)
    rate_limit_req = client.post("/api/auth/phone/request-otp", json={"phone": phone_num})
    assert rate_limit_req.status_code == 429

    # Invalid OTP rejected
    bad_verify = client.post("/api/auth/phone/verify-otp", json={
        "phone": phone_num,
        "otp": "000000",
        "name": "Phone Friend"
    })
    assert bad_verify.status_code == 400

    # Valid OTP verified
    verify_req = client.post("/api/auth/phone/verify-otp", json={
        "phone": phone_num,
        "otp": sent_otp,
        "name": "Phone Friend"
    })
    assert verify_req.status_code == 200
    assert "access_token" in verify_req.json()

    # 11. Test Logout
    logout_res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token_a}"})
    assert logout_res.status_code == 200

    # Old refresh token should now fail
    ref_after_logout = client.post("/api/auth/refresh", json={"refresh_token": refresh_a})
    assert ref_after_logout.status_code == 401

def secrets_rand_digits():
    import secrets
    return f"{secrets.randbelow(900000000) + 100000000}"

def test_phone_otp_security_and_limits():
    from app.services.sms.service import sms_service
    from app.services.sms.mock import MockSMSProvider

    mock_provider = MockSMSProvider()
    sms_service.set_provider(mock_provider)

    # 1. Invalid phone format rejected (400 or 422)
    bad_phone = client.post("/api/auth/phone/request-otp", json={"phone": "12345"})
    assert bad_phone.status_code in (400, 422)

    bad_digits = client.post("/api/auth/phone/request-otp", json={"phone": "abcdefghij"})
    assert bad_digits.status_code == 400

    # 2. Valid request
    phone_num = f"+918{secrets_rand_digits()}"
    req = client.post("/api/auth/phone/request-otp", json={"phone": phone_num})
    assert req.status_code == 200
    sent_otp = mock_provider.sent_messages[-1]["otp"]

    # 3. Rate limiting triggered (429)
    req2 = client.post("/api/auth/phone/request-otp", json={"phone": phone_num})
    assert req2.status_code == 429
    assert "wait" in req2.json()["detail"].lower()

    # 4. Exceed 5 invalid attempts locks OTP
    for i in range(5):
        fail_res = client.post("/api/auth/phone/verify-otp", json={
            "phone": phone_num,
            "otp": f"99999{i}"
        })
        assert fail_res.status_code == 400

    # 6th attempt with CORRECT OTP should now be locked
    locked_res = client.post("/api/auth/phone/verify-otp", json={
        "phone": phone_num,
        "otp": sent_otp
    })
    assert locked_res.status_code == 400
    assert "too many invalid attempts" in locked_res.json()["detail"].lower()

