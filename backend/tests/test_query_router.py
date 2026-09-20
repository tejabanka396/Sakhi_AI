import pytest
from app.services.query_router import query_router, QueryType

def test_pure_time_queries():
    """Verify time questions route to CURRENT_TIME across languages."""
    time_queries = [
        "what time is it?",
        "What is the current time?",
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
        "what is today's date?",
        "today date",
        "today?",
        "what day is today?",
        "ఈరోజు తేది ఏంటి?",
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

def test_realtime_web_search_queries():
    """Verify current/live events route to WEB_SEARCH."""
    web_queries = [
        "today's news",
        "latest AI news",
        "latest version of Python",
        "current gold price in India",
        "what happened in AI today?",
        "latest cricket score",
        "who won today's match?",
        "current weather in Visakhapatnam",
        "ఈరోజు latest AI news ఏంటి?",
        "ఈరోజు వార్తలు ఏంటి?",
        "ప్రస్తుతం బంగారం ధర ఎంత?",
        "ivala latest news enti?",
        "ivala cricket latest score enti?",
        "today gold rate entha?",
        "ippudu weather ela undi?",
    ]
    for q in web_queries:
        res = query_router.route(q)
        assert res.query_type == QueryType.WEB_SEARCH, f"Failed on: {q}, got {res.query_type}"
        assert res.search_query is not None and len(res.search_query) > 0

def test_normal_educational_queries_do_not_trigger_search():
    """Verify educational and historical concepts do not trigger web search."""
    normal_queries = [
        "Explain binary search.",
        "photosynthesis explain cheyyi",
        "How does a compiler work?",
        "What is recursion in computer science?",
        "Explain what happened in the French Revolution.",
        "Hi Sakhi, how are you today?",
        "Tell me an interesting bedtime story.",
        "DBMS lo transactions ante enti?",
    ]
    for q in normal_queries:
        res = query_router.route(q)
        assert res.query_type == QueryType.NORMAL, f"Failed on: {q}, got {res.query_type} ({res.reason})"
