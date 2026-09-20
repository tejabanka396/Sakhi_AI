import re
import logging
from enum import Enum
from typing import Optional, Tuple
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
# Deterministic Patterns for Pure Date / Time (Priority 1)
# ---------------------------------------------------------------------------

TIME_PATTERNS = [
    # English
    r"\b(?:what(?:\s*is|'?s)?\s*(?:the\s*)?(?:current\s*)?time|current\s*time|time\s*now|what\s*time\s*is\s*it|tell\s*me\s*the\s*time)\b",
    # Telugu
    r"(?:ఇప్పుడు\s*)?(?:సమయం|టైమ్|టైం)\s*(?:ఎంత|ఏంటి|చెప్పు)",
    r"ఇప్పటి\s*(?:సమయం|టైమ్|టైం)",
    # Tanglish
    r"\b(?:ippudu\s*time\s*(?:entha|enti|cheppu)|time\s*(?:entha|enti|cheppu)|current\s*time\s*enti)\b",
]

DATE_TODAY_PATTERNS = [
    # English
    r"\b(?:what(?:\s*is|'?s)?\s*today'?s?\s*date|today'?s?\s*date|date\s*today|what\s*date\s*is\s*(?:it\s*)?today|what\s*day\s*is\s*today)\b",
    r"^\s*today\s*\??\s*$",
    r"^\s*today\s*date\s*\??\s*$",
    # Telugu
    r"(?:ఈ\s*రోజు|ఈరోజు|నేడు)\s*(?:తేది|తేదీ|తేది ఎంత|తేదీ ఎంత|తేది ఏంటి|తేదీ ఏంటి|ఏ\s*తేది|ఏ\s*తేదీ|ఏ\s*రోజు|రోజు ఏంటి)",
    # Tanglish
    r"\b(?:ivala|eeroju)\s*(?:date\s*(?:enti|entha|cheppu)?|ye\s*roju|day\s*enti)\b",
    r"\b(?:today\s*date\s*(?:enti|entha|cheppu)?)\b",
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

# ---------------------------------------------------------------------------
# Web Search Intent Triggers (Priority 2)
# ---------------------------------------------------------------------------

WEATHER_TRIGGERS = [
    r"\b(?:weather|temperature|forecast|climate|rain\s*today|humidity)\b",
    r"(?:వాతావరణం|ఎండ|వర్షం)",
    r"\b(?:weather\s*ela\s*undi|varsham\s*padutunda|climate\s*ela\s*undi)\b",
]

FINANCE_PRICE_TRIGGERS = [
    r"\b(?:gold\s*price|gold\s*rate|silver\s*rate|silver\s*price|petrol\s*price|diesel\s*price|stock\s*price|share\s*price|exchange\s*rate|crypto\s*price|bitcoin\s*price)\b",
    r"(?:బంగారం\s*ధర|వెండి\s*ధర|పెట్రోల్\s*ధర|షేర్\s*ధర)",
    r"\b(?:gold\s*rate\s*entha|bangaram\s*dhara|petrol\s*rate)\b",
]

SPORTS_LIVE_TRIGGERS = [
    r"\b(?:live\s*score|cricket\s*(?:latest\s*)?score|latest\s*cricket\s*score|latest\s*score|today'?s?\s*match|who\s*won\s*today|match\s*score|ipl\s*score|world\s*cup\s*score)\b",
    r"(?:మ్యాచ్\s*స్కోర్|ఈరోజు\s*మ్యాచ్|లైవ్\s*స్కోర్|ఎవరు\s*గెలిచారు)",
    r"\b(?:cricket\s*(?:latest\s*)?score|match\s*score|score\s*entha|eeroju\s*match|live\s*score)\b",
]

NEWS_CURRENT_EVENTS_TRIGGERS = [
    r"\b(?:latest\s*news|today'?s?\s*news|recent\s*news|breaking\s*news|news\s*today|what\s*happened\s*(?:today|yesterday|this\s*week|recently)|current\s*affairs)\b",
    r"\b(?:latest\s*updates?\s*(?:about|on)|recent\s*updates?\s*(?:about|on)|what'?s?\s*happening\s*in)\b",
    r"(?:తాజా\s*వార్తలు|ఈరోజు\s*వార్తలు|తాజా\s*సమాచారం|ఈరోజు\s*ఏం\s*జరిగింది|బ్రేకింగ్\s*న్యూస్)",
    r"\b(?:latest\s*news|ivala\s*news|taza\s*vartalu|em\s*jarigindi\s*ivala)\b",
]

TECH_RELEASE_TRIGGERS = [
    r"\b(?:latest\s*version\s*of|latest\s*release\s*of|current\s*version\s*of|latest\s*python\s*version|latest\s*ai\s*models?|latest\s*ai\s*news)\b",
    r"(?:తాజా\s*AI\s*వార్తలు|లేటెస్ట్\s*వెర్షన్)",
    r"\b(?:latest\s*ai\s*updates|latest\s*ai\s*news)\b",
]

EXPLICIT_SEARCH_TRIGGERS = [
    r"\b(?:search\s*the\s*web|search\s*online|look\s*up\s*online|google\s*this|browse\s*the\s*web)\b",
    r"(?:నెట్\s*లో\s*వెతుకు|వెబ్\s*సెర్చ్\s*చేయి)",
    r"\b(?:net\s*lo\s*vethuku|web\s*search\s*cheyyi)\b",
]

# ---------------------------------------------------------------------------
# Negative Patterns (Historical, Concept explanations -> Keep as NORMAL)
# ---------------------------------------------------------------------------
HISTORICAL_CONCEPT_PATTERNS = [
    r"\b(?:revolution|world\s*war|history\s*of|ancient|empire|dynasty|century|treaty\s*of|independence\s*movement)\b",
    r"\b(?:explain|concept\s*of|how\s*does|how\s*do|what\s*is\s*the\s*meaning\s*of|difference\s*between|tutorial|write\s*a\s*program|code\s*for|algorithm)\b",
    r"(?:వివరించు|అంటే\s*ఏంటి|చరిత్ర|భావన|సూత్రం)",
]

class QueryRouter:
    """
    Intelligently routes user queries following strict priority order:
    1. CURRENT_DATE / CURRENT_TIME (Direct backend Asia/Kolkata clock)
    2. WEB_SEARCH (Live/realtime queries requiring external evidence)
    3. NORMAL (Conversational, educational, study questions via Gemini)
    """

    def route(self, text: str) -> RouteResult:
        if not text or not text.strip():
            return RouteResult(
                query_type=QueryType.NORMAL,
                reason="Empty query defaults to normal"
            )

        clean = text.strip()
        lower = clean.lower()

        # ===================================================================
        # PRIORITY 1: Pure Date / Time Questions (NO Gemini, NO Web Search)
        # ===================================================================
        # Check Time
        for pattern in TIME_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                logger.info(f"[REALTIME_ROUTER] Routed to CURRENT_TIME: '{clean}'")
                return RouteResult(
                    query_type=QueryType.CURRENT_TIME,
                    sub_target="time",
                    reason="Matched direct time question"
                )

        # Check Tomorrow
        for pattern in DATE_TOMORROW_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                logger.info(f"[REALTIME_ROUTER] Routed to CURRENT_DATE (tomorrow): '{clean}'")
                return RouteResult(
                    query_type=QueryType.CURRENT_DATE,
                    sub_target="tomorrow",
                    reason="Matched direct tomorrow date question"
                )

        # Check Yesterday
        for pattern in DATE_YESTERDAY_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                logger.info(f"[REALTIME_ROUTER] Routed to CURRENT_DATE (yesterday): '{clean}'")
                return RouteResult(
                    query_type=QueryType.CURRENT_DATE,
                    sub_target="yesterday",
                    reason="Matched direct yesterday date question"
                )

        # Check Today
        for pattern in DATE_TODAY_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                # Distinguish "what day is today" from "today's date"
                is_day = bool(re.search(r"\b(?:what\s*day|యే\s*రోజు|ye\s*roju|ఏ\s*రోజు)\b", lower, re.IGNORECASE))
                sub_target = "day" if is_day else "today"
                logger.info(f"[REALTIME_ROUTER] Routed to CURRENT_DATE ({sub_target}): '{clean}'")
                return RouteResult(
                    query_type=QueryType.CURRENT_DATE,
                    sub_target=sub_target,
                    reason="Matched direct today date/day question"
                )

        # ===================================================================
        # PRIORITY 2: Web Search Intent (Live data, news, prices, sports, tech)
        # ===================================================================
        # First check if query is clearly educational or historical (French revolution, binary search, etc.)
        # unless it explicitly has live/current words like "today", "latest", "breaking"
        is_historical = any(re.search(p, lower, re.IGNORECASE) for p in HISTORICAL_CONCEPT_PATTERNS)
        has_explicit_live = any(
            re.search(p, lower, re.IGNORECASE) for p in [
                r"\b(?:today|latest|current|recent|breaking|live|now|2026)\b",
                r"(?:ఈరోజు|తాజా|ఇప్పుడు|లైవ్|నేడు)",
                r"\b(?:ivala|ippudu|eeroju)\b"
            ]
        )

        # If it's a concept or history WITHOUT explicit current inquiry, route to NORMAL
        if is_historical and not has_explicit_live:
            return RouteResult(
                query_type=QueryType.NORMAL,
                reason="Historical or educational concept query routed to NORMAL"
            )

        # Check live triggers
        all_web_triggers = [
            (WEATHER_TRIGGERS, "weather"),
            (FINANCE_PRICE_TRIGGERS, "financial_rate"),
            (SPORTS_LIVE_TRIGGERS, "sports_score"),
            (NEWS_CURRENT_EVENTS_TRIGGERS, "current_news"),
            (TECH_RELEASE_TRIGGERS, "tech_release"),
            (EXPLICIT_SEARCH_TRIGGERS, "explicit_search"),
        ]

        for trigger_list, category in all_web_triggers:
            for pattern in trigger_list:
                if re.search(pattern, lower, re.IGNORECASE):
                    # Clean search query for provider
                    search_q = self._clean_search_query(clean)
                    logger.info(f"[REALTIME_ROUTER] Routed to WEB_SEARCH ({category}): '{clean}' -> '{search_q}'")
                    return RouteResult(
                        query_type=QueryType.WEB_SEARCH,
                        search_query=search_q,
                        reason=f"Matched {category} trigger"
                    )

        # Generic live queries like "what happened in X today?" or "X today"
        generic_live_pattern = r"\b(?:what\s*happened\s*in\s+[\w\s]+\s+today|[\w\s]+\s+today\s*score|[\w\s]+\s+today\s*news)\b"
        if re.search(generic_live_pattern, lower, re.IGNORECASE):
            search_q = self._clean_search_query(clean)
            logger.info(f"[REALTIME_ROUTER] Routed to WEB_SEARCH (generic live): '{clean}'")
            return RouteResult(
                query_type=QueryType.WEB_SEARCH,
                search_query=search_q,
                reason="Matched generic live pattern"
            )

        # ===================================================================
        # PRIORITY 3: Normal Conversational / Educational Query (Gemini)
        # ===================================================================
        return RouteResult(
            query_type=QueryType.NORMAL,
            reason="Standard conversational/study query routed to Gemini"
        )

    def _clean_search_query(self, raw_query: str) -> str:
        """
        Strips conversational filler from user query to optimize search retrieval.
        E.g. 'Sakhi, tell me latest AI news' -> 'latest AI news'
             'ఈరోజు AI news ఏంటి?' -> 'latest AI news'
        """
        q = raw_query.strip()
        # Remove conversational greetings
        q = re.sub(r"(?i)\b(?:hi|hello|hey|sakhi|cheppu|babu|amma|please|tell\s*me)\b", "", q)
        # Remove trailing question fillers
        q = re.sub(r"(?i)\b(?:enti|entha|ela\s*undi|cheppu|kochem|bro|ra)\b", "", q)
        q = re.sub(r"[?!.,]+$", "", q).strip()
        return q if q else raw_query.strip()

query_router = QueryRouter()
