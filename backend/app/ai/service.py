import time
import asyncio
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.database.models import User, FriendProfile, Setting, Conversation, Message, Memory
from app.ai.gemini import gemini_provider
from app.ai.prompts import build_sakhi_system_prompt
from app.ai.memory import extract_memory_from_message
from app.voice.sanitizer import sanitize_text_for_tts
from app.voice.tts import get_voice_for_gender

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
        t_start = time.perf_counter()

        # 1. Get or create conversation and save user message in a single consolidated commit
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
            db.flush()
            is_new_conversation = True

        user_message = Message(
            conversation_id=conversation.id,
            sender="user",
            content=message_text,
            input_type=input_type
        )
        db.add(user_message)
        db.commit()

        # 2. Fetch Friend Profile & Settings
        friend_profile = db.query(FriendProfile).filter_by(user_id=user.id).first()
        friend_name = friend_profile.friend_name if friend_profile else "Sakhi"
        gender = friend_profile.gender if friend_profile else "female"
        personality = friend_profile.personality if friend_profile else "friendly"
        # Gender is the SINGLE SOURCE OF TRUTH for companion voice
        voice_id = get_voice_for_gender(gender)

        setting = db.query(Setting).filter_by(user_id=user.id).first()
        lang_pref = setting.language_preference if setting else "auto"
        conv_mode = setting.default_mode if setting else "talk"

        # 3. Fetch User Memories for Context
        memories = db.query(Memory).filter_by(user_id=user.id).order_by(Memory.created_at.desc()).limit(10).all()
        memory_texts = [m.memory_text for m in memories]

        # 4. Fetch Recent Messages for Context (up to last 12 messages)
        recent_messages = db.query(Message).filter_by(
            conversation_id=conversation.id
        ).order_by(Message.created_at.desc()).limit(12).all()
        recent_messages.reverse()

        formatted_messages: List[Dict[str, str]] = []
        for msg in recent_messages:
            role = "user" if msg.sender == "user" else "assistant"
            formatted_messages.append({"role": role, "content": msg.content})

        # 5. Detect Language and Route Query (3-Tier Priority)
        from app.ai.prompts import detect_input_language, build_web_search_grounding_prompt
        from app.services.query_router import query_router, QueryType
        from app.services.web_search import (
            web_search_service,
            WebSearchNotConfiguredError,
            WebSearchProviderError,
            WebSearchEmptyResultError
        )
        from app.utils.datetime_utils import generate_direct_datetime_response

        detected_lang = lang_pref if lang_pref in ["telugu", "english"] else detect_input_language(message_text)

        t_route_start = time.perf_counter()
        route_res = query_router.route(message_text)
        route_ms = (time.perf_counter() - t_route_start) * 1000

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

        t_db_ready = time.perf_counter()
        db_prep_ms = (t_db_ready - t_start) * 1000

        ai_reply = ""
        searched = False
        sources = None
        search_timestamp = None
        search_ms = 0.0
        gemini_ms = 0.0

        # ===================================================================
        # TIER 1: PURE DATE / TIME QUERIES (Direct Asia/Kolkata Clock)
        # ===================================================================
        if route_res.query_type in [QueryType.CURRENT_DATE, QueryType.CURRENT_TIME]:
            ai_reply = generate_direct_datetime_response(
                target=route_res.sub_target or "today",
                detected_lang=detected_lang
            )
            searched = False

        # ===================================================================
        # TIER 2: WEB SEARCH (Live Queries via Tavily + Grounded Gemini)
        # ===================================================================
        elif route_res.query_type == QueryType.WEB_SEARCH:
            t_search_start = time.perf_counter()
            try:
                search_q = route_res.search_query or message_text
                logger.info(
                    f"[WEB_SEARCH] provider={web_search_service.provider} query={search_q} enabled={str(web_search_service.enabled).lower()}"
                )
                search_resp = await web_search_service.search(search_q)
                search_ms = (time.perf_counter() - t_search_start) * 1000
                logger.info(f"[WEB_SEARCH] success=true results={len(search_resp.results)}")

                searched = True
                search_timestamp = search_resp.timestamp
                sources = [
                    {"title": item.title, "url": item.url, "domain": item.domain}
                    for item in search_resp.results
                ]

                # Append strict evidence grounding to system prompt
                grounding_prompt = build_web_search_grounding_prompt(
                    query=search_q,
                    search_items=search_resp.results,
                    detected_language=detected_lang
                )
                grounded_instruction = f"{system_instruction}\n\n{grounding_prompt}"

                # Generate grounded response via Gemini
                t_gemini_start = time.perf_counter()
                ai_reply = await self.provider.generate_response(
                    system_instruction=grounded_instruction,
                    messages=formatted_messages
                )
                gemini_ms = (time.perf_counter() - t_gemini_start) * 1000

            except WebSearchNotConfiguredError:
                search_ms = (time.perf_counter() - t_search_start) * 1000
                logger.warning("[WEB_SEARCH] success=false error=not_configured")
                if detected_lang == "telugu":
                    ai_reply = "నాకు ప్రస్తుతం live internet access అందుబాటులో లేదు."
                elif detected_lang == "mixed":
                    ai_reply = "Naaku ippudu live internet access andubatulo ledu."
                else:
                    ai_reply = "I currently do not have access to live internet information."
                searched = False

            except WebSearchEmptyResultError:
                search_ms = (time.perf_counter() - t_search_start) * 1000
                logger.warning("[WEB_SEARCH] success=false error=empty_results")
                if detected_lang == "telugu":
                    ai_reply = "ప్రస్తుతానికి దీని గురించి తాజా సమాచారం కనుగొనలేకపోయాను. కొద్దిసేపటి తర్వాత మళ్లీ ప్రయత్నించండి."
                elif detected_lang == "mixed":
                    ai_reply = "Deeni gurinchi latest information verify cheyalekapoyanu. Konchem sepu tarwatha try cheyyi."
                else:
                    ai_reply = "I could not find any verified recent information on this topic. Please try again later."
                searched = True
                sources = []

            except WebSearchProviderError as prov_err:
                search_ms = (time.perf_counter() - t_search_start) * 1000
                logger.warning("[WEB_SEARCH] success=false error=provider_error")
                if detected_lang == "telugu":
                    ai_reply = "నాకు ప్రస్తుతం live information access చేయడంలో సమస్య ఉంది. కొద్దిసేపటి తర్వాత మళ్లీ ప్రయత్నించండి."
                elif detected_lang == "mixed":
                    ai_reply = "Naaku ippudu live information access cheyadamlo issue undi. Konchem sepu tarwatha malli try cheyyi."
                else:
                    ai_reply = "I am having trouble accessing live information right now. Please try again in a moment."
                searched = False

        # ===================================================================
        # TIER 3: NORMAL QUESTIONS (Standard Gemini Generation)
        # ===================================================================
        else:
            t_gemini_start = time.perf_counter()
            ai_reply = await self.provider.generate_response(
                system_instruction=system_instruction,
                messages=formatted_messages
            )
            gemini_ms = (time.perf_counter() - t_gemini_start) * 1000
            searched = False

        # 7. Response Processing & Strict Speech Sanitization
        t_post_start = time.perf_counter()
        display_text = ai_reply
        # Guarantee that speech_text never has URLs or technical metadata
        speech_text = sanitize_text_for_tts(display_text)

        # 8. Save Assistant Message
        assistant_message = Message(
            conversation_id=conversation.id,
            sender="assistant",
            content=display_text,
            input_type="text"
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        post_ms = (time.perf_counter() - t_post_start) * 1000
        total_ms = (time.perf_counter() - t_start) * 1000

        logger.info(
            f"[CHAT_LATENCY] route={route_res.query_type.value} db_prep_ms={db_prep_ms:.1f} "
            f"route_ms={route_ms:.1f} search_ms={search_ms:.1f} gemini_ms={gemini_ms:.1f} "
            f"post_ms={post_ms:.1f} total_ms={total_ms:.1f} voice_id={voice_id} gender={gender}"
        )

        # 9. Non-blocking Background Tasks: Memory extraction and Title generation
        # These operations do NOT block sending the response and starting TTS playback!
        async def _run_background_tasks(u_id: str, conv_id: str, u_msg: str, a_reply: str, is_new: bool):
            bg_db = None
            try:
                bg_db = SessionLocal()
                # A. Memory Candidate Check & Persistence
                memory_candidate = extract_memory_from_message(u_msg)
                if memory_candidate:
                    mem_text, mem_cat = memory_candidate
                    existing = bg_db.query(Memory).filter_by(
                        user_id=u_id,
                        memory_text=mem_text
                    ).first()
                    if not existing:
                        bg_db.add(Memory(user_id=u_id, memory_text=mem_text, category=mem_cat))
                        bg_db.commit()
                        logger.info(f"Background memory saved for user {u_id}")

                # B. Conversation Title Generation
                if is_new:
                    title = await self.provider.generate_title(u_msg, a_reply)
                    if title and title != "New Conversation":
                        c = bg_db.query(Conversation).filter_by(id=conv_id).first()
                        if c:
                            c.title = title
                            bg_db.commit()
            except Exception as bg_err:
                logger.debug(f"Background chat tasks error: {bg_err}")
            finally:
                if bg_db:
                    bg_db.close()

        asyncio.create_task(
            _run_background_tasks(user.id, conversation.id, message_text, ai_reply, is_new_conversation)
        )

        return {
            "reply": display_text,
            "display_text": display_text,
            "speech_text": speech_text,
            "conversation_id": conversation.id,
            "message_id": assistant_message.id,
            "response_id": assistant_message.id,
            "voice_id": voice_id,
            "gender": gender,
            "title": conversation.title,
            "sender": "assistant",
            "language": detected_lang,
            "searched": searched,
            "sources": sources,
            "search_timestamp": search_timestamp,
        }

chat_service = ChatService()
