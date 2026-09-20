import re
import logging
from enum import Enum
from typing import Optional, List, Tuple
from pydantic import BaseModel

logger = logging.getLogger("sakhi_ai.query_router")

class QueryType(str, Enum):
    CURRENT_DATE = "CURRENT_DATE"
    CURRENT_TIME = "CURRENT_TIME"
    WEB_SEARCH = "WEB_SEARCH"
    NORMAL = "NORMAL"

class RouteResult(BaseModel):
    query_type: QueryType
    sub_target: Optional[str] = None  # 'today', 'tomorrow', 'yesterday', 'time', 'day'
    search_query: Optional[str] = None
    reason: str

# ---------------------------------------------------------------------------
# Changing-domain tokens (Disqualifies query from being pure Date/Time)
# ---------------------------------------------------------------------------
CHANGING_DOMAIN_TOKENS = {
    # Metals / Commodities
    "gold", "silver", "petrol", "diesel", "crude", "oil",
    # Finance / Stocks / Crypto
    "stock", "stocks", "share", "shares", "sensex", "nifty", "crypto",
    "bitcoin", "btc", "ethereum", "eth", "forex", "usd", "inr", "dollar", "rupee",
    # Sports
    "score", "scores", "cricket", "match", "matches", "ipl", "football",
    "world cup", "tournament", "who won",
    # Weather
    "weather", "temperature", "forecast", "climate", "rain", "humidity",
    # News & Events
    "news", "affairs", "election", "elections", "updates", "update", "headline",
    # Telugu / Tanglish
    "బంగారం", "ధర", "ధరలు", "రేటు", "రేట్లు", "రేట్", "వెండి", "గోల్డ్", "సిల్వర్",
    "వాతావరణం", "వర్షం", "వార్తలు", "సమాచారం", "స్కోర్", "మ్యాచ్",
    "bangaram", "dhara", "vendi", "varsham", "vartalu"
}

# ---------------------------------------------------------------------------
# Deterministic Patterns for Pure Date / Time (Priority 1)
# ---------------------------------------------------------------------------
TIME_PATTERNS = [
    # English
    r"\b(?:what(?:\s*is|'?s)?\s*(?:the\s*)?(?:current\s*)?time|current\s*time|time\s*now|what\s*time\s*is\s*it|tell\s*me\s*the\s*time|what'?s?\s*the\s*time\s*now)\b",
    # Telugu
    r"(?:ఇప్పుడు\s*)?(?:సమయం|టైమ్|టైం)\s*(?:ఎంత|ఏంటి|చెప్పు)",
    r"ఇప్పటి\s*(?:సమయం|టైమ్|టైం)",
    # Tanglish
    r"\b(?:ippudu\s*time\s*(?:entha|enti|cheppu)|time\s*(?:entha|enti|cheppu)|current\s*time\s*enti)\b",
]

DATE_TOMORROW_PATTERNS = [
    # English
    r"\b(?:what(?:\s*is|'?s)?\s*tomorrow'?s?\s*date|tomorrow'?s?\s*date|date\s*tomorrow|what\s*date\s*is\s*tomorrow|what\s*day\s*is\s*tomorrow)\b",
    r"^\s*tomorrow\s*\??\s*$",
    r"^\s*tomorrow\s*date\s*\??\s*$",
    # Telugu
    r"(?:రేపు|రేపటి)\s*(?:తేది|తేదీ|ఏ\s*తేది|ఏ\s*తేదీ|ఏ\s*రోజు|రోజు ఏంటి)",
    # Tanglish
    r"\b(?:repu)\s*(?:date\s*(?:enti|entha|cheppu)?|ye\s*roju|day\s*enti)\b",
    r"\b(?:tomorrow\s*date\s*(?:enti|entha|cheppu)?)\b",
]

DATE_YESTERDAY_PATTERNS = [
    # English
    r"\b(?:what(?:\s*was|'?s)?\s*yesterday'?s?\s*date|yesterday'?s?\s*date|date\s*yesterday|what\s*date\s*was\s*yesterday|what\s*day\s*was\s*yesterday)\b",
    r"^\s*yesterday\s*\??\s*$",
    r"^\s*yesterday\s*date\s*\??\s*$",
    # Telugu
    r"(?:నిన్న|నిన్నటి)\s*(?:తేది|తేదీ|ఏ\s*తేది|ఏ\s*తేదీ|ఏ\s*రోజు|రోజు ఏంటి)",
    # Tanglish
    r"\b(?:ninna)\s*(?:date\s*(?:enti|entha|cheppu)?|ye\s*roju|day\s*enti)\b",
    r"\b(?:yesterday\s*date\s*(?:enti|entha|cheppu)?)\b",
]

DATE_TODAY_PATTERNS = [
    # English
    r"\b(?:what(?:\s*is|'?s)?\s*today'?s?\s*date|today'?s?\s*date|date\s*today|what\s*date\s*is\s*(?:it\s*)?today|what\s*day\s*is\s*(?:it\s*)?today)\b",
    r"^\s*today\s*\??\s*$",
    r"^\s*today\s*date\s*\??\s*$",
    # Telugu
    r"(?:ఈ\s*రోజు|ఈరోజు|నేడు)\s*(?:తేది|తేదీ|తేది ఎంత|తేదీ ఎంత|తేది ఏంటి|తేదీ ఏంటి|ఏ\s*తేది|ఏ\s*తేదీ|ఏ\s*రోజు|రోజు ఏంటి)",
    # Tanglish
    r"\b(?:ivala|eeroju)\s*(?:date\s*(?:enti|entha|cheppu)?|ye\s*roju|day\s*enti)\b",
    r"\b(?:today\s*date\s*(?:enti|entha|cheppu)?)\b",
]

# ---------------------------------------------------------------------------
# Concept / Educational Guard Patterns (Priority 3 Check)
# Pure definitions without temporal intent route to NORMAL
# ---------------------------------------------------------------------------
CONCEPT_PATTERNS = [
    # English: "explain gold", "what is cricket", "what is photosynthesis", "how does weather forecasting work"
    r"^(?:explain|describe|define)\s+(?:what\s+(?:is\s+)?)?([a-z0-9\s\-]+?)(?:\s+rules|\s+concept|\s+algorithm|\s+in\s+simple\s+terms)?$",
    r"^what\s+(?:is|are|was|were)\s+(?:a\s+|an\s+|the\s+)?([a-z0-9\s\-]+?)(?:\s+rules|\s+concept|\s+algorithm)?$",
    r"^how\s+(?:does|do)\s+([a-z0-9\s\-]+?)\s+work$",
    # Telugu / Tanglish: "gold ante enti", "cricket ante emiti", "binary search gurinchi cheppu"
    r"^([a-z0-9\s\u0C00-\u0C7F]+?)\s+(?:ante\s*enti|ante\s*emiti|gurinchi\s*cheppu|gurinchi\s*vivarinchu|explain\s*cheyyi|explain\s*chey)$",
]

# Educational subjects that are strictly conceptual when appearing in concept patterns
STATIC_CONCEPT_TERMS = {
    "binary search", "photosynthesis", "recursion", "compiler", "operating system",
    "dbms", "transactions", "algorithm", "quicksort", "bubble sort", "data structure",
    "neural network", "machine learning", "gravity", "evolution", "atom", "molecule",
    "french revolution", "world war", "history", "ancient egypt", "cricket rules"
}

# ---------------------------------------------------------------------------
# Real-Time Intent Signals (Priority 2)
# ---------------------------------------------------------------------------
TEMPORAL_SIGNALS = [
    # English
    r"\b(?:today|todays|today's|current|currently|now|right\s*now|latest|live|recent|recently)\b",
    r"\b(?:this\s*morning|this\s*evening|tonight|yesterday|tomorrow|this\s*week|this\s*month)\b",
    r"\b(?:updated|update|latest\s*update|breaking|happened\s*today|happening\s*now|2026)\b",
    # Telugu
    r"(?:ఈరోజు|ఇవాళ|ప్రస్తుతం|ఇప్పుడు|తాజా|ఇప్పటి|ఈ\s*వారం|ఈ\s*నెల|అప్డేట్|ఏమి\s*జరుగుతోంది|తాజా\s*వార్తలు|నిన్న|రేపు)",
    # Tanglish
    r"\b(?:ivala|ivvala|eeroju|eroju|ippudu|ippude|ippati|prastutam|taaja|em\s*jarugutundi)\b",
]

DOMAIN_SIGNALS = {
    "gold_silver": [
        r"\b(?:gold|silver|bangaram|vendi)\b",
        r"(?:బంగారం|వెండి|గోల్డ్|సిల్వర్)",
    ],
    "price_rate": [
        r"\b(?:price|prices|rate|rates|cost|dhara|rupee|inr|usd)\b",
        r"(?:ధర|ధరలు|రేటు|రేట్లు|రేట్|ఖరీదు)",
    ],
    "finance_crypto": [
        r"\b(?:stock|stocks|share\s*price|shares|sensex|nifty|crypto|bitcoin|btc|ethereum|eth|petrol|diesel|market\s*price|exchange\s*rate|forex|dollar\s*rate)\b",
        r"(?:పెట్రోల్|డీజిల్|షేర్|స్టాక్)",
    ],
    "sports": [
        r"\b(?:score|cricket|match|matches|ipl|world\s*cup|football|who\s*won)\b",
        r"(?:స్కోర్|మ్యాచ్|ఎవరు\s*గెలిచారు)",
    ],
    "weather": [
        r"\b(?:weather|temperature|forecast|climate|rain|humidity)\b",
        r"(?:వాతావరణం|ఎండ|వర్షం)",
    ],
    "news_events": [
        r"\b(?:news|current\s*affairs|election|election\s*result|updates?|what\s*happened|what\s*is\s*happening)\b",
        r"(?:వార్తలు|సమాచారం|తాజా\s*సమాచారం|ఏం\s*జరిగింది)",
    ],
    "tech_models": [
        r"\b(?:latest\s*version|latest\s*release|latest\s*ai|ai\s*news|ai\s*updates|deepmind|gemini\s*updates|chatgpt\s*updates)\b",
        r"(?:AI\s*వార్తలు)",
    ],
    "explicit_search": [
        r"\b(?:search\s*the\s*web|search\s*online|look\s*up\s*online|google\s*this|browse\s*the\s*web)\b",
        r"(?:నెట్\s*లో\s*వెతుకు|వెబ్\s*సెర్చ్)",
    ]
}

# Standalone dynamic patterns that immediately signal WEB_SEARCH even without dual signals
STANDALONE_DYNAMIC_PATTERNS = [
    r"\b(?:live\s*score|cricket\s*score|today'?s?\s*score|today'?s?\s*match|who\s*won\s*today)\b",
    r"\b(?:current\s*weather|today'?s?\s*weather|weather\s*today|rain\s*today|weather\s*forecast)\b",
    r"\b(?:latest\s*news|today'?s?\s*news|current\s*news|breaking\s*news|recent\s*news|news\s*today)\b",
    r"\b(?:what\s*happened\s*today|what\s*is\s*happening\s*now|what'?s?\s*happening\s*now)\b",
    r"(?:తాజా\s*వార్తలు|ఈరోజు\s*వార్తలు|లైవ్\s*స్కోర్|ఈరోజు\s*మ్యాచ్|ప్రస్తుతం\s*ఏమి\s*జరుగుతోంది)",
    r"\b(?:ivala\s*news|taza\s*vartalu|em\s*jarigindi\s*ivala|ippudu\s*em\s*jarugutundi)\b",
    r"\b(?:latest\s*ai\s*news|latest\s*ai\s*updates|latest\s*version\s*of)\b",
]

class QueryRouter:
    """
    Intelligently routes user queries following strict priority order:
    1. CURRENT_DATE / CURRENT_TIME (Direct backend Asia/Kolkata clock, NO Gemini, NO Tavily)
    2. WEB_SEARCH (Live/realtime queries requiring external evidence via Tavily)
    3. NORMAL (Conversational, educational, conceptual questions via Gemini)
    """

    def route(self, text: str) -> RouteResult:
        if not text or not text.strip():
            logger.info("[REALTIME_ROUTER] route=NORMAL reason=empty_query")
            return RouteResult(
                query_type=QueryType.NORMAL,
                reason="empty_query"
            )

        clean = text.strip()
        lower = clean.lower()
        # Normalize typography: replace curly quotes and collapse spaces
        lower = lower.replace("’", "'").replace("‘", "'").replace("`", "'")
        lower_norm = re.sub(r"\s+", " ", lower)
        # Stripped of punctuation for easy token/boundary inspection
        lower_clean = re.sub(r"[?!.,:;\"()]+", " ", lower_norm).strip()

        # Check for changing domain keywords to avoid falsely routing live queries to Date/Time
        has_changing_domain = any(tok in lower_norm for tok in CHANGING_DOMAIN_TOKENS)

        # ===================================================================
        # PRIORITY 1: Pure Date / Time Questions (NO Gemini, NO Web Search)
        # Only execute if the query is NOT inquiring about domain commodities/events
        # ===================================================================
        if not has_changing_domain:
            # Check Time
            for pattern in TIME_PATTERNS:
                if re.search(pattern, lower_norm, re.IGNORECASE):
                    logger.info(f"[REALTIME_ROUTER] route=CURRENT_TIME reason=current_time")
                    return RouteResult(
                        query_type=QueryType.CURRENT_TIME,
                        sub_target="time",
                        reason="current_time"
                    )

            # Check Tomorrow
            for pattern in DATE_TOMORROW_PATTERNS:
                if re.search(pattern, lower_norm, re.IGNORECASE):
                    logger.info(f"[REALTIME_ROUTER] route=CURRENT_DATE reason=tomorrow_date")
                    return RouteResult(
                        query_type=QueryType.CURRENT_DATE,
                        sub_target="tomorrow",
                        reason="tomorrow_date"
                    )

            # Check Yesterday
            for pattern in DATE_YESTERDAY_PATTERNS:
                if re.search(pattern, lower_norm, re.IGNORECASE):
                    logger.info(f"[REALTIME_ROUTER] route=CURRENT_DATE reason=yesterday_date")
                    return RouteResult(
                        query_type=QueryType.CURRENT_DATE,
                        sub_target="yesterday",
                        reason="yesterday_date"
                    )

            # Check Today
            for pattern in DATE_TODAY_PATTERNS:
                if re.search(pattern, lower_norm, re.IGNORECASE):
                    is_day = bool(re.search(r"\b(?:what\s*day|యే\s*రోజు|ye\s*roju|ఏ\s*రోజు)\b", lower_norm, re.IGNORECASE))
                    sub_target = "day" if is_day else "today"
                    logger.info(f"[REALTIME_ROUTER] route=CURRENT_DATE reason=today_date")
                    return RouteResult(
                        query_type=QueryType.CURRENT_DATE,
                        sub_target=sub_target,
                        reason="today_date"
                    )

        # ===================================================================
        # PRIORITY 3 CHECK: Concept / Educational Guard
        # Check if query is purely conceptual (e.g. "what is gold", "explain cricket")
        # CRITICAL RULE: A live/temporal modifier OVERRIDES the concept guard!
        # ===================================================================
        has_temporal_signal = any(re.search(p, lower_norm, re.IGNORECASE) for p in TEMPORAL_SIGNALS)
        # Also check for Telugu/Tanglish price inquiry words (e.g. "entha", "enti", "ధర ఎంత")
        has_tanglish_price_inquiry = bool(re.search(r"\b(?:entha|enti|dhara)\b|(?:ధర|రేటు|రేట్)", lower_norm))

        # Check Concept Guard ONLY if there is NO live/temporal modifier
        if not has_temporal_signal:
            is_concept = False
            for c_pat in CONCEPT_PATTERNS:
                m = re.match(c_pat, lower_clean, re.IGNORECASE)
                if m:
                    subject = m.group(1).strip() if m.groups() else lower_clean
                    # If subject is a pure commodity name WITHOUT price/rate request (e.g. "gold", "cricket", "silver", "binary search")
                    if not any(pr_word in subject for pr_word in ["price", "rate", "dhara", "score", "cost", "ధర", "రేటు", "రేట్"]):
                        is_concept = True
                        break

            # Static study concepts (e.g. "photosynthesis", "binary search", "how does weather forecasting work")
            if any(term in lower_clean for term in STATIC_CONCEPT_TERMS) or is_concept:
                logger.info(f"[REALTIME_ROUTER] route=NORMAL reason=conceptual_question")
                return RouteResult(
                    query_type=QueryType.NORMAL,
                    reason="conceptual_question"
                )

        # ===================================================================
        # PRIORITY 2: WEB SEARCH INTENT DETECTION
        # ===================================================================
        # 1. Standalone dynamic queries (e.g. "latest news", "live cricket score", "current weather")
        for s_pat in STANDALONE_DYNAMIC_PATTERNS:
            if re.search(s_pat, lower_norm, re.IGNORECASE):
                cleaned_q = self._clean_search_query(clean)
                logger.info(f"[REALTIME_ROUTER] route=WEB_SEARCH reason=standalone_dynamic")
                return RouteResult(
                    query_type=QueryType.WEB_SEARCH,
                    search_query=cleaned_q,
                    reason="standalone_dynamic"
                )

        # 2. Domain signal detection
        detected_domains = []
        for domain_name, patterns in DOMAIN_SIGNALS.items():
            for p in patterns:
                if re.search(p, lower_norm, re.IGNORECASE):
                    detected_domains.append(domain_name)
                    break

        # 3. Decision Rules:
        # Case A: Live/Temporal Signal + Dynamic Domain Signal
        if has_temporal_signal and detected_domains:
            reason = f"temporal+{detected_domains[0]}"
            cleaned_q = self._clean_search_query(clean)
            logger.info(f"[REALTIME_ROUTER] route=WEB_SEARCH reason={reason}")
            return RouteResult(
                query_type=QueryType.WEB_SEARCH,
                search_query=cleaned_q,
                reason=reason
            )

        # Case B: Conversational price / rate / score requests
        # E.g. "gold rate?", "gold rate today?", "how much is gold today?", "ivala gold rate entha?",
        # "ivala bangaram rate entha?", "ippudu gold price entha?", "ఈరోజు బంగారం ధర ఎంత"
        is_metal_query = "gold_silver" in detected_domains
        is_price_query = "price_rate" in detected_domains or has_tanglish_price_inquiry or bool(re.search(r"\b(?:how\s*much|cost|rate|price)\b", lower_norm))
        if is_metal_query and is_price_query:
            reason = "temporal+gold_price" if has_temporal_signal else "conversational_gold_price"
            cleaned_q = self._clean_search_query(clean)
            logger.info(f"[REALTIME_ROUTER] route=WEB_SEARCH reason={reason}")
            return RouteResult(
                query_type=QueryType.WEB_SEARCH,
                search_query=cleaned_q,
                reason=reason
            )

        # Case C: Financial/crypto/fuel price inquiry
        is_fin_query = "finance_crypto" in detected_domains
        if is_fin_query and (has_temporal_signal or is_price_query):
            reason = "finance_market_rate"
            cleaned_q = self._clean_search_query(clean)
            logger.info(f"[REALTIME_ROUTER] route=WEB_SEARCH reason={reason}")
            return RouteResult(
                query_type=QueryType.WEB_SEARCH,
                search_query=cleaned_q,
                reason=reason
            )

        # Case D: Weather inquiry
        if "weather" in detected_domains:
            reason = "weather_inquiry"
            cleaned_q = self._clean_search_query(clean)
            logger.info(f"[REALTIME_ROUTER] route=WEB_SEARCH reason={reason}")
            return RouteResult(
                query_type=QueryType.WEB_SEARCH,
                search_query=cleaned_q,
                reason=reason
            )

        # Case E: Sports score inquiry
        if "sports" in detected_domains and (has_temporal_signal or "score" in lower_norm or "won" in lower_norm):
            reason = "sports_score"
            cleaned_q = self._clean_search_query(clean)
            logger.info(f"[REALTIME_ROUTER] route=WEB_SEARCH reason={reason}")
            return RouteResult(
                query_type=QueryType.WEB_SEARCH,
                search_query=cleaned_q,
                reason=reason
            )

        # Case F: Explicit web search request
        if "explicit_search" in detected_domains:
            reason = "explicit_web_search"
            cleaned_q = self._clean_search_query(clean)
            logger.info(f"[REALTIME_ROUTER] route=WEB_SEARCH reason={reason}")
            return RouteResult(
                query_type=QueryType.WEB_SEARCH,
                search_query=cleaned_q,
                reason=reason
            )

        # Case G: Generic live phrase (e.g. "what happened in X today")
        if has_temporal_signal and bool(re.search(r"\b(?:what\s*happened|happening|updates?|news)\b", lower_norm)):
            reason = "temporal+current_events"
            cleaned_q = self._clean_search_query(clean)
            logger.info(f"[REALTIME_ROUTER] route=WEB_SEARCH reason={reason}")
            return RouteResult(
                query_type=QueryType.WEB_SEARCH,
                search_query=cleaned_q,
                reason=reason
            )

        # ===================================================================
        # PRIORITY 3: Normal Conversational / Educational Query (Gemini)
        # ===================================================================
        logger.info("[REALTIME_ROUTER] route=NORMAL reason=conversational")
        return RouteResult(
            query_type=QueryType.NORMAL,
            reason="conversational"
        )

    def _clean_search_query(self, raw_query: str) -> str:
        """
        Transforms conversational user input (English, Telugu, Tanglish) into an effective,
        clean search query for Tavily without losing key terms.
        Examples:
          "today's gold price in India" -> "today gold price India"
          "ivala gold rate entha?"     -> "today gold price India"
          "ivala bangaram rate entha"  -> "today gold price India"
          "ఈరోజు బంగారం ధర ఎంత"        -> "today gold price India"
          "ivala cricket score enti?"  -> "today live cricket score"
          "latest AI news"             -> "latest AI news"
        """
        q = raw_query.strip()
        lower = q.lower().replace("’", "'").replace("‘", "'")

        # 1. Specialized Gold & Silver Price Normalizer
        is_gold = bool(re.search(r"\b(?:gold|bangaram)\b|(?:బంగారం|గోల్డ్)", lower))
        is_silver = bool(re.search(r"\b(?:silver|vendi)\b|(?:వెండి|సిల్వర్)", lower))
        is_price_rate = bool(
            re.search(r"\b(?:price|prices|rate|rates|cost|dhara|entha|how\s*much)\b|(?:ధర|ధరలు|రేటు|రేట్లు|రేట్)", lower)
        )

        if is_gold and (is_price_rate or "gold rate" in lower or "gold price" in lower):
            # Time modifier
            if any(w in lower for w in ["current", "currently", "ippudu", "ప్రస్తుతం", "now", "right now"]):
                time_term = "current"
            elif any(w in lower for w in ["latest", "taaja", "తాజా"]):
                time_term = "latest"
            else:
                time_term = "today"

            # Regional modifier
            region = "India"
            if "hyderabad" in lower:
                region = "Hyderabad"
            elif "vijayawada" in lower:
                region = "Vijayawada"
            elif "visakhapatnam" in lower or "vizag" in lower:
                region = "Visakhapatnam"
            elif "delhi" in lower:
                region = "Delhi"
            elif "mumbai" in lower:
                region = "Mumbai"
            elif "chennai" in lower:
                region = "Chennai"
            elif "bangalore" in lower or "bengaluru" in lower:
                region = "Bangalore"

            return f"{time_term} gold price {region}"

        if is_silver and is_price_rate:
            if any(w in lower for w in ["current", "currently", "ippudu", "ప్రస్తుతం"]):
                time_term = "current"
            elif any(w in lower for w in ["latest", "taaja", "తాజా"]):
                time_term = "latest"
            else:
                time_term = "today"
            return f"{time_term} silver price India"

        # 2. Specialized Cricket Score Normalizer
        is_cricket = bool(re.search(r"\b(?:cricket|match|ipl)\b", lower))
        is_score = bool(re.search(r"\b(?:score|winner|won|స్కోర్)\b", lower))
        if is_cricket and is_score:
            if any(w in lower for w in ["ivala", "eeroju", "today", "live", "ఈరోజు", "ippudu"]):
                return "today live cricket score"
            return "live cricket score"

        # 3. General Search Query Cleaning
        q_clean = q

        # Translate common Telugu / Tanglish temporal and domain stems to English keywords for Tavily
        q_clean = re.sub(r"(?:ఈరోజు|ఇవాళ|\b(?:eeroju|ivala|ivvala)\b)", "today", q_clean, flags=re.IGNORECASE)
        q_clean = re.sub(r"(?:ప్రస్తుతం|ఇప్పుడు|\b(?:ippudu|ippude)\b)", "current", q_clean, flags=re.IGNORECASE)
        q_clean = re.sub(r"(?:తాజా|\b(?:taaja)\b)", "latest", q_clean, flags=re.IGNORECASE)
        q_clean = re.sub(r"(?:వార్తలు|\b(?:vartalu)\b)", "news", q_clean, flags=re.IGNORECASE)
        q_clean = re.sub(r"(?:వాతావరణం)", "weather", q_clean, flags=re.IGNORECASE)
        q_clean = re.sub(r"(?:బంగారం|గోల్డ్|\b(?:bangaram)\b)", "gold", q_clean, flags=re.IGNORECASE)
        q_clean = re.sub(r"(?:వెండి|సిల్వర్|\b(?:vendi)\b)", "silver", q_clean, flags=re.IGNORECASE)
        q_clean = re.sub(r"(?:ధర|ధరలు|రేటు|రేట్లు|రేట్|\b(?:dhara)\b)", "price", q_clean, flags=re.IGNORECASE)

        # Remove conversational greeting and fluff words
        filler_patterns = [
            r"(?i)\b(?:sakhi|cheppu|tell\s*me|please|can\s*you|do\s*you\s*know|what\s*is|what\s*are|what's|how\s*much\s*is)\b",
            r"(?i)\b(?:babu|amma|bro|ra|koddiga|konchem|kuda|andi)\b",
            r"(?i)\b(?:enti|entha|ela\s*undi|em\s*jarigindi|jarugutundi)\b",
        ]
        for fp in filler_patterns:
            q_clean = re.sub(fp, " ", q_clean)

        # Remove trailing and punctuation marks
        q_clean = re.sub(r"[?!.,:;\"'()]+", " ", q_clean)
        q_clean = re.sub(r"\s+", " ", q_clean).strip()

        return q_clean if len(q_clean) >= 3 else q.strip()

query_router = QueryRouter()
