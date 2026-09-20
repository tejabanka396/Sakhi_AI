import asyncio
import re
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

try:
    from google import genai
    from google.genai import types
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False

try:
    import google.generativeai as legacy_genai
    HAS_LEGACY_GENAI = True
except ImportError:
    HAS_LEGACY_GENAI = False

from app.core.config import settings

logger = logging.getLogger("sakhi_ai.gemini")

class AIProvider(ABC):
    @abstractmethod
    async def generate_response(
        self,
        system_instruction: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> str:
        pass

    @abstractmethod
    async def generate_title(
        self,
        user_message: str,
        assistant_reply: str
    ) -> str:
        pass

class GeminiProvider(AIProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self.client = None
        self._cooldown_models: Dict[str, float] = {}

        if self.api_key:
            if HAS_GOOGLE_GENAI:
                try:
                    http_opts = types.HttpOptions(
                        retry_options=types.HttpRetryOptions(attempts=1),
                        timeout=15000
                    )
                    self.client = genai.Client(api_key=self.api_key, http_options=http_opts)
                    logger.info("Initialized modern Google GenAI Client with zero-wait failover.")
                except Exception as e:
                    logger.error(f"Failed to initialize Google GenAI Client: {e}")

            if HAS_LEGACY_GENAI:
                try:
                    legacy_genai.configure(api_key=self.api_key)
                    logger.info("Configured legacy google.generativeai fallback.")
                except Exception as e:
                    logger.error(f"Failed to configure legacy Gemini API: {e}")

    def _sync_generate_response(
        self,
        model_id: str,
        contents: Any,
        config: Any
    ) -> Optional[str]:
        """Runs synchronous generate_content via the official Google GenAI SDK."""
        response = self.client.models.generate_content(
            model=model_id,
            contents=contents,
            config=config
        )
        if response and response.text:
            return response.text.strip()
        return None

    def _sync_legacy_generate(
        self,
        model_id: str,
        system_instruction: str,
        contents: Any,
        temperature: float
    ) -> Optional[str]:
        """Runs legacy google.generativeai fallback if needed."""
        try:
            if self.api_key:
                legacy_genai.configure(api_key=self.api_key)
            legacy_model = legacy_genai.GenerativeModel(
                model_name=model_id,
                system_instruction=system_instruction,
                generation_config=legacy_genai.GenerationConfig(
                    temperature=temperature,
                    top_p=0.9,
                    top_k=40,
                    max_output_tokens=1000
                )
            )
            res = legacy_model.generate_content(contents)
            if res and res.text:
                return res.text.strip()
        except Exception as e:
            logger.error(f"Legacy Gemini fallback error: {e}")
        return None

    async def generate_response(
        self,
        system_instruction: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> str:
        if not self.api_key:
            logger.warning("No GEMINI_API_KEY set. Falling back to local conversational response.")
            return self._local_fallback_response(messages[-1]["content"] if messages else "")

        # 1. Primary: Use modern google-genai SDK
        if self.client and HAS_GOOGLE_GENAI:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature,
                top_p=0.9,
                top_k=40,
                max_output_tokens=1000,
            )

            contents = []
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg["content"])]
                    )
                )

            import time
            now = time.time()
            all_candidates = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", self.model_name, "gemini-3.7-flash", "gemini-3.6-flash"]
            models_to_try = []
            for m in all_candidates:
                if m and m not in models_to_try and now >= self._cooldown_models.get(m, 0):
                    models_to_try.append(m)

            if not models_to_try:
                models_to_try = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]

            last_error = None
            for model_id in models_to_try:
                try:
                    reply = await asyncio.to_thread(
                        self._sync_generate_response,
                        model_id,
                        contents,
                        config
                    )
                    if reply:
                        return reply
                except Exception as e:
                    last_error = e
                    self._cooldown_models[model_id] = time.time() + 60.0
                    logger.warning(f"Model {model_id} failed: {e}. Cooldown set; falling back to next available model.")

            logger.error(f"All Google GenAI models failed: {last_error}")

        # 2. Secondary: Fallback to legacy google.generativeai if modern client failed or unavailable
        if HAS_LEGACY_GENAI:
            try:
                legacy_contents = []
                for msg in messages:
                    role = "user" if msg["role"] == "user" else "model"
                    legacy_contents.append({"role": role, "parts": [msg["content"]]})

                reply = await asyncio.to_thread(
                    self._sync_legacy_generate,
                    self.model_name,
                    system_instruction,
                    legacy_contents,
                    temperature
                )
                if reply:
                    return reply
            except Exception as e:
                logger.error(f"Legacy Gemini fallback failed: {e}")

        # 3. No mock AI responses permitted - raise clear exception
        raise RuntimeError(f"Sakhi AI could not connect to Gemini. Please try again in a moment. ({last_error})")

    def _sync_generate_title(self, prompt: str, model_id: str) -> Optional[str]:
        res = self.client.models.generate_content(
            model=model_id,
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=30, temperature=0.3)
        )
        if res and res.text:
            return res.text.strip()
        return None

    async def generate_title(
        self,
        user_message: str,
        assistant_reply: str
    ) -> str:
        if not self.api_key:
            words = user_message.strip().split()
            return " ".join(words[:3]).capitalize() if words else "Friendly Chat"

        from app.ai.prompts import build_title_generation_prompt
        prompt = build_title_generation_prompt(user_message, assistant_reply)

        if self.client and HAS_GOOGLE_GENAI:
            import time
            now = time.time()
            models_to_try = []
            for m in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", self.model_name, "gemini-3.7-flash", "gemini-3.6-flash"]:
                if m and m not in models_to_try and now >= self._cooldown_models.get(m, 0):
                    models_to_try.append(m)
            if not models_to_try:
                models_to_try = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]

            for mid in models_to_try:
                try:
                    raw_title = await asyncio.to_thread(self._sync_generate_title, prompt, mid)
                    if raw_title:
                        title = raw_title.replace('"', '').replace("'", "").replace("#", "")
                        return title[:40] if title else "Friendly Chat"
                except Exception as e:
                    self._cooldown_models[mid] = time.time() + 60.0
                    logger.debug(f"Title generation for {mid} failed: {e}")

        if HAS_LEGACY_GENAI:
            try:
                if self.api_key:
                    legacy_genai.configure(api_key=self.api_key)
                model = legacy_genai.GenerativeModel(model_name=self.model_name)
                res = await asyncio.to_thread(model.generate_content, prompt)
                if res and res.text:
                    title = res.text.strip().replace('"', '').replace("'", "").replace("#", "")
                    return title[:40] if title else "Friendly Chat"
            except Exception as e:
                logger.warning(f"Legacy title generation failed: {e}")

        words = user_message.strip().split()
        return " ".join(words[:3]).capitalize() if words else "Friendly Chat"

gemini_provider = GeminiProvider()
