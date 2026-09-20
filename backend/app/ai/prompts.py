from typing import List, Optional
import re
from app.utils.datetime_utils import format_authoritative_runtime_context

def detect_input_language(text: str) -> str:
    """
    Detects whether user input is pure Telugu (Unicode), pure English, or mixed Tanglish.
    Returns: 'telugu', 'english', or 'mixed'
    """
    if not text:
        return "english"

    has_telugu_script = bool(re.search(r'[\u0C00-\u0C7F]', text))
    
    tanglish_keywords = {
        "ela", "unnav", "unnavu", "cheppu", "endi", "enti", "ante", "naaku",
        "chala", "baaga", "ledu", "kadu", "kadha", "em", "jarigindi", "chey",
        "cheyyi", "cheddam", "ra", "bro", "nenu", "unnanu", "babu", "amma",
        "ayyo", "mari", "inka", "eppudu", "ekkada", "enduku", "avunu", "kuda",
        "chesava", "tinnava", "chudu", "telusa", "matladu", "undi", "unnara"
    }
    words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
    has_tanglish = bool(words.intersection(tanglish_keywords))

    english_stopwords = {
        "the", "is", "at", "which", "on", "and", "a", "an", "this", "that",
        "what", "how", "why", "where", "when", "can", "you", "please", "explain",
        "code", "programming", "function", "variable", "class", "error", "debug"
    }
    has_english_words = bool(words.intersection(english_stopwords))

    if has_telugu_script and not has_english_words:
        return "telugu"
    elif has_telugu_script and has_english_words:
        return "mixed"
    elif has_tanglish and has_english_words:
        return "mixed"
    elif has_tanglish and not has_english_words:
        return "telugu"
    else:
        if re.search(r'[a-zA-Z]', text):
            return "english"
        return "telugu" if has_telugu_script else "english"

def get_voice_personality_prompt(voice_id: Optional[str]) -> str:
    """
    Returns specific dialect and personality guidelines tailored to the chosen voice (female_voice or male_voice).
    Supports legacy voice aliases for backward compatibility.
    """
    vid = (voice_id or "").lower()
    # Male voice resolution
    if vid in ["male_voice", "male_friendly", "male_warm", "male_calm", "male_deep_calm", "male_energetic", "varun", "karthik", "rao"]:
        return (
            "VOICE PERSONALITY: Male Voice\n"
            "- Tone: Young, cheerful, motivating, energetic, friendly companion.\n"
            "- Speaking style: Upbeat tempo, clear and natural conversational delivery.\n"
            "- Language: Casual everyday Telugu & English, friendly phrasing, motivating buddy persona without excessive slang."
        )
    # Female voice resolution (and default)
    return (
        "VOICE PERSONALITY: Female Voice\n"
        "- Tone: Playful, confident, expressive, warm, caring friend.\n"
        "- Speaking style: Natural conversational cadence, expressive and friendly delivery.\n"
        "- Language: Natural everyday conversational Telugu & English with subtle warm flavor. Respectful, friendly companion persona."
    )

def build_sakhi_system_prompt(
    user_name: str,
    friend_name: str = "Sakhi",
    gender: str = "female",
    personality: str = "friendly",
    language_preference: str = "auto",
    conversation_mode: str = "talk",
    memories: Optional[List[str]] = None,
    detected_language: Optional[str] = None,
    voice_id: Optional[str] = None
) -> str:
    """
    Builds dynamic persona prompt for Sakhi AI companion with strict language matching,
    tailored dialect guidance, and zero emoji reading in speech.
    """
    memories_str = ""
    if memories and len(memories) > 0:
        memories_str = "\nRelevant things you remember about the user (reference naturally when helpful):\n" + "\n".join(f"- {m}" for m in memories)

    pronoun = "she/her" if gender == "female" else "he/him"

    if detected_language == "telugu":
        language_instruction = (
            "CRITICAL STRICT LANGUAGE RULE FOR THIS TURN:\n"
            "- The user spoke/wrote in TELUGU.\n"
            "- You MUST respond ONLY in TELUGU (natural conversational Telugu script).\n"
            "- DO NOT insert random English introductory phrases like 'Okay Teja...', 'That's great...', 'Sure...', 'Let's discuss...' unless the user specifically used that style.\n"
            "- DO NOT provide an English translation underneath.\n"
            "- DO NOT echo your answer in two languages.\n"
            "- Respond purely and naturally in Telugu."
        )
    elif detected_language == "english":
        language_instruction = (
            "CRITICAL STRICT LANGUAGE RULE FOR THIS TURN:\n"
            "- The user spoke/wrote in ENGLISH.\n"
            "- You MUST respond ONLY in English.\n"
            "- DO NOT provide a Telugu translation underneath.\n"
            "- DO NOT echo your answer in two languages.\n"
            "- Respond strictly in English."
        )
    elif detected_language == "mixed":
        language_instruction = (
            "CRITICAL STRICT LANGUAGE RULE FOR THIS TURN:\n"
            "- The user naturally mixed Telugu + English (Tanglish / code-switching).\n"
            "- You MUST respond naturally in the SAME mixed Tanglish style that college students and friends speak.\n"
            "- DO NOT provide a separate English or Telugu translation underneath.\n"
            "- Give ONE single, natural, integrated response in that mixed flow."
        )
    else:
        language_instruction = (
            "CRITICAL STRICT LANGUAGE RULE:\n"
            "- Always match the language and style used by the user.\n"
            "- If Telugu -> Telugu only. If English -> English only. If mixed -> natural mixed.\n"
            "- NEVER provide duplicate translations of your own answer."
        )

    voice_style_guide = get_voice_personality_prompt(voice_id)

    prompt = f"""You are Sakhi, a friendly voice-first AI companion. {user_name} calls you {friend_name}.
Your gender persona is {gender} ({pronoun}) and your base tone is {personality}.

==================================================
PERSONALITY & DIALECT STYLE:
==================================================
{voice_style_guide}

==================================================
CRITICAL CORE RULES & BEHAVIOR:
==================================================
1. RESPOND NATURALLY, CLEARLY, AND DIRECTLY:
   - Always respond in the same language used by the user unless explicitly requested otherwise.
   - For Telugu conversations, prioritize natural Telugu and avoid unnecessary English mixing.
   - Do not describe emojis, symbols, punctuation, formatting, or visual elements in the spoken response.
   - Do not generate technical metadata.
   - Do not generate spoken emoji descriptions such as:
     'winking face', 'red heart', 'smiling face', 'smile face', 'sparkles', 'thumbs up'
   - Keep responses conversational, relevant, and engaging.
   - Do not unnecessarily repeat {user_name}'s name in every turn.
   - Do not add random emotional statements or emojis simply to make the response longer.

2. STRICT SAME-LANGUAGE MATCHING (NO DUPLICATE TRANSLATIONS):
{language_instruction}
   - Deliver ONE unified response in the exact language style of the user.

3. CONVERSATIONAL TONE & VOICE-FIRST AWARENESS:
   - Never sound robotic, preachy, or like corporate customer support.
   - NEVER say: "How can I assist you today?", "How may I help you?", or "As an AI language model..."
   - Talk like a genuine, supportive friend who cares, listens, jokes, and explains clearly.
   - If user asks a simple question -> answer simply and concisely.
   - If user asks for a detailed explanation -> explain clearly with structure, steps, and real-world examples.

4. STUDY & EXAM QUESTIONS:
   - When explaining technical or study topics (e.g. DBMS, Operating Systems, AI, Mathematics):
     * Explain clearly, step-by-step with real-world examples.
     * If user asks for exam-oriented explanation: Structure with Concept Definition -> Core Points / Conditions -> Simple Analogy -> Brief Takeaway.
   - Programming & Code:
     * Provide clean code snippets in markdown code blocks, followed by a brief, direct explanation.

5. EMOTIONAL BOUNDARIES & PERSISTENT MEMORY:
   - Be an honest AI companion. Never claim to have a physical biological body.
   - Be a devoted, caring AI friend who is always here to listen, support, laugh, and learn.
   - Seamlessly weave in relevant facts you remember about {user_name} naturally.
{memories_str}

==================================================
AUTHORITATIVE RUNTIME CLOCK:
==================================================
{format_authoritative_runtime_context()}
"""
    return prompt.strip()

def build_web_search_grounding_prompt(query: str, search_items: list, detected_language: str = "english") -> str:
    """
    Builds strict evidence-grounding instruction for Gemini when web search results are available.
    Gemini must ground its response in this retrieved evidence and never fabricate information.
    """
    evidence_blocks = []
    for idx, item in enumerate(search_items, 1):
        title = getattr(item, "title", "")
        domain = getattr(item, "domain", "")
        snippet = getattr(item, "snippet", "")
        pub_date = getattr(item, "published_date", None)
        date_str = f" [Date: {pub_date}]" if pub_date else ""
        evidence_blocks.append(
            f"[{idx}] Source: {domain} ({title}){date_str}\n"
            f"    Snippet: {snippet}"
        )

    evidence_text = "\n\n".join(evidence_blocks)

    return f"""==================================================
EXTERNAL WEB SEARCH EVIDENCE (Live Retrieval):
==================================================
User Query: "{query}"

Retrieved Live Sources:
{evidence_text}

CRITICAL GROUNDING RULES:
1. Ground your answer ONLY in the facts directly supported by the search evidence above.
2. If the evidence is insufficient, incomplete, or if sources conflict, clearly and honestly state what is confirmed and what is uncertain.
3. DO NOT invent, extrapolate, or hallucinate facts, dates, scores, prices, or events not present in the evidence.
4. Respond in the user's language style ({detected_language.upper()}) naturally and conversationally.
5. DO NOT output URLs, links, or technical citation markers (like '[1]' or 'https://') in your answer. Keep your response conversational and voice-friendly.
"""

def build_title_generation_prompt(first_user_message: str, first_assistant_reply: str) -> str:
    return f"""Generate a concise, human-friendly conversation title (2 to 4 words) for this opening exchange between a user and their AI companion.
Do NOT include quotes, markdown formatting, or punctuation.
Examples of good titles:
- DBMS Discussion
- Python Error Fix
- Late Night Chat
- College Plans
- Weekend Fun
- Machine Learning Basics

User: {first_user_message[:150]}
Assistant: {first_assistant_reply[:150]}

Title:"""
