import pytest
from app.services.query_router import query_router, QueryType

def test_pure_time_queries():
    """Verify time questions route to CURRENT_TIME across languages."""
    time_queries = [
        "what time is it",
        "what time is it?",
        "What is the current time?",
        "what's the time now",
        "time now",
        "ఇప్పుడు టైమ్ ఎంత?",
        "సమయం ఎంత?",
        "ippudu time entha?",
        "time enti cheppu",
    ]
    for q in time_queries:
        res = query_router.route(q)
        assert res.query_type == QueryType.CURRENT_TIME, f"Failed on: {q}, got {res.query_type}"
        assert res.sub_target == "time"

def test_pure_date_today_queries():
    """Verify today date queries route to CURRENT_DATE across languages."""
    today_queries = [
        "what date is today",
        "what date is today?",
        "what is today's date?",
        "today's date",
        "today date",
        "today?",
        "what day is today",
        "what day is today?",
        "ఈరోజు తేది ఏంటి?",
        "ఈరోజు తేదీ ఎంత",
        "ఈరోజు తేదీ ఎంత?",
        "ఈరోజు ఏ రోజు?",
        "ivala date enti?",
        "today date enti?",
        "eeroju ye roju?",
    ]
    for q in today_queries:
        res = query_router.route(q)
        assert res.query_type == QueryType.CURRENT_DATE, f"Failed on: {q}, got {res.query_type}"

def test_pure_date_tomorrow_yesterday_queries():
    """Verify tomorrow and yesterday queries route to CURRENT_DATE."""
    tomorrow_queries = [
        "tomorrow date?",
        "what is tomorrow's date?",
        "రేపు ఏ తేదీ",
        "రేపు ఏ తేదీ?",
        "repu date enti?",
    ]
    for q in tomorrow_queries:
        res = query_router.route(q)
        assert res.query_type == QueryType.CURRENT_DATE, f"Failed on: {q}, got {res.query_type}"
        assert res.sub_target == "tomorrow"

    yesterday_queries = [
        "yesterday date?",
        "what was yesterday's date?",
        "నిన్న ఏ తేదీ?",
        "ninna date enti?",
    ]
    for q in yesterday_queries:
        res = query_router.route(q)
        assert res.query_type == QueryType.CURRENT_DATE, f"Failed on: {q}, got {res.query_type}"
        assert res.sub_target == "yesterday"

def test_required_realtime_web_search_assertions():
    """Verify all explicit mandatory real-time assertions from specifications route to WEB_SEARCH."""
    explicit_queries = [
        "today's gold price",
        "gold price today",
        "current gold rate",
        "gold rate in India today",
        "ivala gold rate entha",
        "ivala bangaram rate entha",
        "ఈరోజు బంగారం ధర ఎంత",
        "latest AI news",
        "today's cricket score",
        "current bitcoin price",
    ]
    for q in explicit_queries:
        res = query_router.route(q)
        assert res.query_type == QueryType.WEB_SEARCH, f"Failed required assertion on: {q}, got {res.query_type}"
        assert res.search_query is not None and len(res.search_query) > 0

def test_additional_english_web_search_queries():
    """Verify English live/current event inquiries route to WEB_SEARCH."""
    queries = [
        "current gold price",
        "latest gold rate",
        "latest gold price",
        "current silver price",
        "today's silver price",
        "latest news about AI",
        "live cricket score",
        "current weather",
        "today's weather",
        "current stock price",
        "latest stock price",
        "latest Bitcoin price",
        "current petrol price",
        "today's petrol price",
        "latest government news",
        "current news",
        "latest news",
        "what happened today",
        "what is happening now",
        "recent news",
        "latest updates",
        "today's gold price in India",
    ]
    for q in queries:
        res = query_router.route(q)
        assert res.query_type == QueryType.WEB_SEARCH, f"Failed on: {q}, got {res.query_type}"

def test_telugu_and_tanglish_web_search_queries():
    """Verify Telugu and Tanglish real-time queries route to WEB_SEARCH."""
    telugu_queries = [
        "ఇవాళ బంగారం రేటు ఎంత",
        "ఈరోజు గోల్డ్ రేట్ ఎంత",
        "ప్రస్తుతం బంగారం ధర ఎంత",
        "ఇప్పటి బంగారం ధర ఎంత",
        "తాజా బంగారం ధర",
        "ఈరోజు వెండి ధర ఎంత",
        "తాజా వార్తలు ఏంటి",
        "ఇవాళ తాజా వార్తలు ఏంటి",
        "ప్రస్తుతం ఏమి జరుగుతోంది",
        "ఇప్పటి తాజా సమాచారం ఏంటి",
    ]
    for q in telugu_queries:
        res = query_router.route(q)
        assert res.query_type == QueryType.WEB_SEARCH, f"Failed on Telugu query: {q}, got {res.query_type}"

    tanglish_queries = [
        "today gold rate entha",
        "current gold price entha",
        "ippudu gold rate entha",
        "latest gold rate enti",
        "ivala silver rate entha",
        "latest news enti",
        "ivala latest news enti",
        "ippudu em jarugutundi",
        "current news enti",
    ]
    for q in tanglish_queries:
        res = query_router.route(q)
        assert res.query_type == QueryType.WEB_SEARCH, f"Failed on Tanglish query: {q}, got {res.query_type}"

def test_conversational_question_forms():
    """Verify natural conversational forms with varied punctuation and question words route to WEB_SEARCH."""
    conv_queries = [
        "gold rate?",
        "gold rate today?",
        "what is gold rate today?",
        "how much is gold today?",
        "today gold price in India?",
        "what's the current gold price?",
        "do you know today's gold rate?",
        "tell me latest gold rate",
        "ivala gold rate entha?",
        "today bangaram rate entha?",
        "ippudu gold price entha?",
    ]
    for q in conv_queries:
        res = query_router.route(q)
        assert res.query_type == QueryType.WEB_SEARCH, f"Failed on conversational form: {q}, got {res.query_type}"

def test_punctuation_and_case_insensitivity():
    """Verify router handles casing, extra spaces, and varying punctuation correctly."""
    cases = [
        ("TODAY'S GOLD PRICE?", QueryType.WEB_SEARCH),
        ("today's gold price!!!", QueryType.WEB_SEARCH),
        ("  current gold rate  ", QueryType.WEB_SEARCH),
        ("Ivala Gold Rate Entha?", QueryType.WEB_SEARCH),
        ("WHAT DATE IS TODAY?", QueryType.CURRENT_DATE),
        ("  WHAT TIME IS IT?  ", QueryType.CURRENT_TIME),
        ("EXPLAIN GOLD", QueryType.NORMAL),
        ("What Is Gold???", QueryType.NORMAL),
    ]
    for text, expected in cases:
        res = query_router.route(text)
        assert res.query_type == expected, f"Failed on '{text}': expected {expected}, got {res.query_type}"

def test_concept_guard_educational_queries_route_to_normal():
    """Verify educational, historical, and conceptual questions remain NORMAL without triggering search."""
    normal_queries = [
        "explain gold",
        "what is gold",
        "Explain what gold is.",
        "What is gold?",
        "explain cricket",
        "Explain cricket rules.",
        "what is cricket",
        "what is binary search",
        "Explain binary search",
        "what is photosynthesis",
        "How does weather forecasting work?",
        "Explain Bitcoin.",
        "What is a stock?",
        "What is silver?",
        "photosynthesis explain cheyyi",
        "gold ante enti",
        "cricket ante emiti",
        "binary search gurinchi cheppu",
        "Hi Sakhi, how are you today?",
        "Tell me an interesting bedtime story.",
        "DBMS lo transactions ante enti?",
    ]
    for q in normal_queries:
        res = query_router.route(q)
        assert res.query_type == QueryType.NORMAL, f"Failed on: {q}, got {res.query_type} ({res.reason})"

def test_search_query_cleaning():
    """Verify _clean_search_query produces effective search strings for Tavily."""
    samples = [
        ("today's gold price in India", "today gold price India"),
        ("ivala gold rate entha?", "today gold price India"),
        ("ivala bangaram rate entha", "today gold price India"),
        ("ఈరోజు బంగారం ధర ఎంత", "today gold price India"),
        ("ivala cricket score enti?", "today live cricket score"),
        ("latest AI news", "latest AI news"),
    ]
    for raw, expected in samples:
        cleaned = query_router._clean_search_query(raw)
        assert expected.lower() in cleaned.lower() or cleaned.lower() == expected.lower(), (
            f"Query cleaner failed for '{raw}': got '{cleaned}', expected '{expected}'"
        )
