import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.database.models import User, FriendProfile, Setting, Conversation, Message, Memory
from app.ai.gemini import gemini_provider
from app.ai.prompts import build_sakhi_system_prompt
from app.ai.memory import extract_memory_from_message
from app.voice.sanitizer import sanitize_text_for_tts

logger = logging.getLogger("sakhi_ai.chat_service")

class ChatService:
    def __init__(self):
        self.provider = gemini_provider

    async def process_chat(
        self,
        db: Session,
        user: User,
        message_text: str,
        conversation_id: Optional[str] = None,
        input_type: str = "text"
    ) -> Dict[str, Any]:
        # 1. Get or create conversation
        conversation = None
        is_new_conversation = False

        if conversation_id:
            conversation = db.query(Conversation).filter_by(
                id=conversation_id,
                user_id=user.id
            ).first()

        if not conversation:
            conversation = Conversation(
                user_id=user.id,
                title="New Conversation"
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            is_new_conversation = True

        # 2. Save User Message
        user_message = Message(
            conversation_id=conversation.id,
            sender="user",
            content=message_text,
            input_type=input_type
        )
        db.add(user_message)
        db.commit()

        # 3. Check for Long-Term Memory Extraction
        memory_candidate = extract_memory_from_message(message_text)
        if memory_candidate:
            mem_text, mem_cat = memory_candidate
            # Avoid duplicate memory
            existing_mem = db.query(Memory).filter_by(
                user_id=user.id,
                memory_text=mem_text
            ).first()
            if not existing_mem:
                new_memory = Memory(
                    user_id=user.id,
                    memory_text=mem_text,
                    category=mem_cat
                )
                db.add(new_memory)
                db.commit()
                logger.info(f"Saved memory for user {user.id}: {mem_text}")

        # 4. Fetch Friend Profile & Settings
        friend_profile = db.query(FriendProfile).filter_by(user_id=user.id).first()
        friend_name = friend_profile.friend_name if friend_profile else "Sakhi"
        gender = friend_profile.gender if friend_profile else "female"
        personality = friend_profile.personality if friend_profile else "friendly"
        voice_id = friend_profile.voice_id if friend_profile else "female_friendly"

        setting = db.query(Setting).filter_by(user_id=user.id).first()
        lang_pref = setting.language_preference if setting else "auto"
        conv_mode = setting.default_mode if setting else "talk"

        # 5. Fetch User Memories for Context
        memories = db.query(Memory).filter_by(user_id=user.id).order_by(Memory.created_at.desc()).limit(10).all()
        memory_texts = [m.memory_text for m in memories]

        # 6. Detect Language and Build System Prompt
        from app.ai.prompts import detect_input_language
        detected_lang = lang_pref if lang_pref in ["telugu", "english"] else detect_input_language(message_text)

        system_instruction = build_sakhi_system_prompt(
            user_name=user.name,
            friend_name=friend_name,
            gender=gender,
            personality=personality,
            language_preference=lang_pref,
            conversation_mode=conv_mode,
            memories=memory_texts,
            detected_language=detected_lang,
            voice_id=voice_id
        )

        # 7. Fetch Recent Messages for Context (up to last 12 messages)
        recent_messages = db.query(Message).filter_by(
            conversation_id=conversation.id
        ).order_by(Message.created_at.desc()).limit(12).all()
        recent_messages.reverse()

        formatted_messages: List[Dict[str, str]] = []
        for msg in recent_messages:
            role = "user" if msg.sender == "user" else "assistant"
            formatted_messages.append({"role": role, "content": msg.content})

        # 8. Generate AI Response
        ai_reply = await self.provider.generate_response(
            system_instruction=system_instruction,
            messages=formatted_messages
        )

        display_text = ai_reply
        speech_text = sanitize_text_for_tts(display_text)

        # 9. Save Assistant Message (Must store display_text with emojis for chat history)
        assistant_message = Message(
            conversation_id=conversation.id,
            sender="assistant",
            content=display_text,
            input_type="text"
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        # 10. Non-blocking Background Title Generation (Optimizes response latency)
        async def _update_title_background(conv_id: str, u_msg: str, a_reply: str):
            try:
                title = await self.provider.generate_title(u_msg, a_reply)
                if title and title != "New Conversation":
                    from app.database.database import SessionLocal
                    bg_db = SessionLocal()
                    try:
                        c = bg_db.query(Conversation).filter_by(id=conv_id).first()
                        if c:
                            c.title = title
                            bg_db.commit()
                    finally:
                        bg_db.close()
            except Exception as te:
                logger.debug(f"Background title generation error: {te}")

        if is_new_conversation or conversation.title == "New Conversation":
            import asyncio
            asyncio.create_task(_update_title_background(conversation.id, message_text, ai_reply))

        return {
            "reply": display_text,
            "display_text": display_text,
            "speech_text": speech_text,
            "conversation_id": conversation.id,
            "message_id": assistant_message.id,
            "response_id": assistant_message.id,
            "title": conversation.title,
            "sender": "assistant",
            "language": detected_lang
        }

chat_service = ChatService()
