import pytest
import uuid
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from app.database.database import SessionLocal, engine
from app.database.models import (
    User, FriendProfile, Conversation, Message, Memory, Setting, OTPVerification, RefreshToken
)

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

def test_database_crud_and_cascades(db_session):
    # 1. Create User with unique random phone and email
    test_user_id = str(uuid.uuid4())
    random_phone = f"+91{random.randint(1000000000, 9999999999)}"
    user = User(
        id=test_user_id,
        name="Teja Test",
        email=f"teja_{uuid.uuid4().hex[:6]}@example.com",
        phone=random_phone,
        password_hash="fake_hash_for_test",
        auth_provider="email"
    )
    db_session.add(user)
    db_session.commit()

    retrieved_user = db_session.query(User).filter_by(id=test_user_id).first()
    assert retrieved_user is not None
    assert retrieved_user.name == "Teja Test"

    # 2. Create Friend Profile
    friend_profile = FriendProfile(
        id=str(uuid.uuid4()),
        user_id=test_user_id,
        friend_name="Anu",
        gender="female",
        voice_id="female_friendly",
        personality="friendly"
    )
    db_session.add(friend_profile)

    # 3. Create Settings
    setting = Setting(
        id=str(uuid.uuid4()),
        user_id=test_user_id,
        default_mode="talk",
        voice_enabled=True,
        always_speak=False,
        language_preference="auto"
    )
    db_session.add(setting)

    # 4. Create Conversation
    conv_id = str(uuid.uuid4())
    conversation = Conversation(
        id=conv_id,
        user_id=test_user_id,
        title="DBMS Discussion"
    )
    db_session.add(conversation)

    # 5. Create Telugu message with Unicode & emojis
    msg_user = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        sender="user",
        content="హలో అను, ఎలా ఉన్నావు? 😊 DBMS deadlocks explain cheyyi!",
        input_type="voice"
    )
    msg_assistant = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        sender="assistant",
        content="హాయ్ తేజా! నేను బాగున్నాను ❤️ Deadlock ante 4 conditions satisfy avali: Mutual Exclusion...",
        input_type="text"
    )
    db_session.add_all([msg_user, msg_assistant])

    # 6. Create Memory
    memory = Memory(
        id=str(uuid.uuid4()),
        user_id=test_user_id,
        memory_text="User wants to prepare DBMS for semester exams.",
        category="learning"
    )
    db_session.add(memory)

    # 7. Create OTP Record
    otp_record = OTPVerification(
        id=str(uuid.uuid4()),
        phone=random_phone,
        user_id=test_user_id,
        otp_hash="hashed_otp_sample",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        attempts=0,
        verified=False
    )
    db_session.add(otp_record)

    # 8. Create Refresh Token
    refresh_token = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=test_user_id,
        token_hash=f"token_hash_{uuid.uuid4().hex}",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    db_session.add(refresh_token)
    db_session.commit()

    # Verify everything exists and Unicode Telugu survived perfectly
    stored_conv = db_session.query(Conversation).filter_by(id=conv_id).first()
    assert len(stored_conv.messages) == 2
    contents = " ".join([m.content for m in stored_conv.messages])
    assert "హలో అను" in contents
    assert "😊" in contents
    assert "బాగున్నాను ❤️" in contents

    # 9. Verify Cascade Delete
    db_session.delete(user)
    db_session.commit()

    assert db_session.query(User).filter_by(id=test_user_id).first() is None
    assert db_session.query(FriendProfile).filter_by(user_id=test_user_id).first() is None
    assert db_session.query(Setting).filter_by(user_id=test_user_id).first() is None
    assert db_session.query(Conversation).filter_by(id=conv_id).first() is None
    assert db_session.query(Message).filter_by(conversation_id=conv_id).first() is None
    assert db_session.query(Memory).filter_by(user_id=test_user_id).first() is None
    assert db_session.query(RefreshToken).filter_by(user_id=test_user_id).first() is None
