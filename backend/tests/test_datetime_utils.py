import zoneinfo
from datetime import datetime
import pytest
from app.utils.datetime_utils import (
    KOLKATA_TZ,
    get_current_datetime,
    get_current_date,
    get_current_time,
    get_current_day,
    get_relative_date,
    format_authoritative_runtime_context,
    generate_direct_datetime_response,
)

def test_kolkata_timezone():
    """Verify Asia/Kolkata timezone is strictly used."""
    dt = get_current_datetime()
    assert dt.tzinfo == zoneinfo.ZoneInfo("Asia/Kolkata")

def test_today_calculation():
    """Verify today date calculation is dynamic and matches runtime clock."""
    dt = get_current_datetime()
    today_str = get_current_date()
    assert today_str == dt.strftime("%Y-%m-%d")

def test_current_time_formatting():
    """Verify 12-hour AM/PM format without seconds."""
    time_str = get_current_time()
    assert any(time_str.endswith(period) for period in ["AM", "PM"])
    assert ":" in time_str

def test_current_day_name():
    """Verify weekday name matches runtime date."""
    day = get_current_day()
    assert day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def test_relative_date_calculations():
    """Verify offset dates for yesterday, today, and tomorrow."""
    today_info = get_relative_date(0)
    yesterday_info = get_relative_date(-1)
    tomorrow_info = get_relative_date(1)

    assert today_info["date_str"] != yesterday_info["date_str"]
    assert today_info["date_str"] != tomorrow_info["date_str"]
    assert yesterday_info["date_str"] < today_info["date_str"] < tomorrow_info["date_str"]

    # Verify Telugu month and day names exist
    assert len(today_info["telugu_month"]) > 0
    assert len(today_info["telugu_day"]) > 0

def test_runtime_context_formatting():
    """Verify authoritative context string contains Asia/Kolkata and required markers."""
    ctx = format_authoritative_runtime_context()
    assert "Asia/Kolkata" in ctx
    assert "Current Date:" in ctx
    assert "Current Time:" in ctx
    assert "Authoritative Server Time" in ctx

def test_direct_datetime_response_telugu():
    """Verify direct response generation for pure date/time queries in Telugu."""
    telugu_today = generate_direct_datetime_response("today", "telugu")
    assert "ఈరోజు" in telugu_today
    # Contains Telugu script
    assert any('\u0c00' <= char <= '\u0c7f' for char in telugu_today)

    telugu_tomorrow = generate_direct_datetime_response("tomorrow", "telugu")
    assert "రేపు" in telugu_tomorrow

    telugu_yesterday = generate_direct_datetime_response("yesterday", "telugu")
    assert "నిన్న" in telugu_yesterday

    telugu_time = generate_direct_datetime_response("time", "telugu")
    assert "సమయం" in telugu_time

def test_direct_datetime_response_english():
    """Verify direct response generation for pure date/time queries in English."""
    en_today = generate_direct_datetime_response("today", "english")
    assert "Today is" in en_today

    en_tomorrow = generate_direct_datetime_response("tomorrow", "english")
    assert "Tomorrow's date is" in en_tomorrow

    en_yesterday = generate_direct_datetime_response("yesterday", "english")
    assert "Yesterday's date was" in en_yesterday

    en_time = generate_direct_datetime_response("time", "english")
    assert "The current time is" in en_time

def test_direct_datetime_response_tanglish():
    """Verify direct response generation for pure date/time queries in Tanglish."""
    tang_today = generate_direct_datetime_response("today", "mixed")
    assert "Ivala" in tang_today

    tang_tomorrow = generate_direct_datetime_response("tomorrow", "mixed")
    assert "Repu" in tang_tomorrow

    tang_yesterday = generate_direct_datetime_response("yesterday", "mixed")
    assert "Ninna" in tang_yesterday

    tang_time = generate_direct_datetime_response("time", "mixed")
    assert "Ippudu time" in tang_time
