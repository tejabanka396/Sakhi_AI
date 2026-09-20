from datetime import datetime, timedelta, timezone
from typing import Dict, Any

try:
    import zoneinfo
    KOLKATA_TZ = zoneinfo.ZoneInfo("Asia/Kolkata")
except Exception:
    KOLKATA_TZ = timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")

TELUGU_MONTHS = {
    1: "జనవరి",
    2: "ఫిబ్రవరి",
    3: "మార్చి",
    4: "ఏప్రిల్",
    5: "మే",
    6: "జూన్",
    7: "జూలై",
    8: "ఆగస్టు",
    9: "సెప్టెంబర్",
    10: "అక్టోబర్",
    11: "నవంబర్",
    12: "డిసెంబర్",
}

TELUGU_DAYS = {
    "Monday": "సోమవారం",
    "Tuesday": "మంగళవారం",
    "Wednesday": "బుధవారం",
    "Thursday": "గురువారం",
    "Friday": "శుక్రవారం",
    "Saturday": "శనివారం",
    "Sunday": "ఆదివారం",
}

def get_current_datetime() -> datetime:
    """
    Returns the dynamic runtime datetime in Asia/Kolkata timezone.
    Never cached at startup.
    """
    return datetime.now(KOLKATA_TZ)

def get_current_date() -> str:
    """Returns YYYY-MM-DD in Asia/Kolkata."""
    return get_current_datetime().strftime("%Y-%m-%d")

def get_current_time(include_seconds: bool = False) -> str:
    """Returns formatted 12-hour time in Asia/Kolkata, e.g. '01:05 PM'."""
    fmt = "%I:%M:%S %p" if include_seconds else "%I:%M %p"
    return get_current_datetime().strftime(fmt)

def get_current_day() -> str:
    """Returns current weekday name in English, e.g. 'Sunday'."""
    return get_current_datetime().strftime("%A")

def get_relative_date(offset_days: int = 0) -> Dict[str, Any]:
    """
    Calculates date offset from today in Asia/Kolkata (e.g. -1 for yesterday, 1 for tomorrow).
    """
    dt = get_current_datetime() + timedelta(days=offset_days)
    day_name = dt.strftime("%A")
    return {
        "date_str": dt.strftime("%Y-%m-%d"),
        "day": dt.day,
        "month": dt.month,
        "month_name": dt.strftime("%B"),
        "telugu_month": TELUGU_MONTHS.get(dt.month, dt.strftime("%B")),
        "year": dt.year,
        "day_name": day_name,
        "telugu_day": TELUGU_DAYS.get(day_name, day_name),
        "formatted_display": dt.strftime("%d %B %Y"),
    }

def format_authoritative_runtime_context() -> str:
    """
    Builds the authoritative runtime context string to inject into Gemini system instructions.
    """
    now = get_current_datetime()
    time_str = now.strftime("%I:%M %p")
    day_name = now.strftime("%A")
    date_str = now.strftime("%Y-%m-%d")
    month_name = now.strftime("%B")
    return (
        "CURRENT RUNTIME INFORMATION (Authoritative Server Time):\n"
        f"- Current Date: {date_str} ({day_name}, {now.day} {month_name} {now.year})\n"
        f"- Current Time: {time_str} IST\n"
        "- Timezone: Asia/Kolkata\n"
        "- Note: These values are generated directly from the server clock. Never guess or hallucinate current date/time."
    )

def generate_direct_datetime_response(target: str, detected_lang: str = "english") -> str:
    """
    Directly generates accurate date/time responses from the Asia/Kolkata clock
    without invoking Gemini, eliminating latency and guaranteeing accuracy.
    target: 'today' | 'tomorrow' | 'yesterday' | 'time' | 'day'
    detected_lang: 'telugu' | 'english' | 'mixed'
    """
    lang = detected_lang.lower() if detected_lang else "english"

    if target == "time":
        time_str = get_current_time()
        if lang == "telugu":
            return f"ఇప్పుడు సమయం {time_str} (IST)."
        elif lang == "mixed":
            return f"Ippudu time {time_str} IST."
        else:
            return f"The current time is {time_str} (IST)."

    elif target == "today":
        info = get_relative_date(0)
        if lang == "telugu":
            return f"ఈరోజు {info['day']} {info['telugu_month']} {info['year']}, {info['telugu_day']}."
        elif lang == "mixed":
            return f"Ivala {info['day']} {info['month_name']} {info['year']}, {info['day_name']}."
        else:
            return f"Today is {info['day_name']}, {info['month_name']} {info['day']}, {info['year']}."

    elif target == "tomorrow":
        info = get_relative_date(1)
        if lang == "telugu":
            return f"రేపు తేది {info['day']} {info['telugu_month']} {info['year']}, {info['telugu_day']}."
        elif lang == "mixed":
            return f"Repu date {info['day']} {info['month_name']} {info['year']}, {info['day_name']}."
        else:
            return f"Tomorrow's date is {info['day_name']}, {info['month_name']} {info['day']}, {info['year']}."

    elif target == "yesterday":
        info = get_relative_date(-1)
        if lang == "telugu":
            return f"నిన్న తేది {info['day']} {info['telugu_month']} {info['year']}, {info['telugu_day']}."
        elif lang == "mixed":
            return f"Ninna date {info['day']} {info['month_name']} {info['year']}, {info['day_name']}."
        else:
            return f"Yesterday's date was {info['day_name']}, {info['month_name']} {info['day']}, {info['year']}."

    elif target == "day":
        info = get_relative_date(0)
        if lang == "telugu":
            return f"ఈరోజు {info['telugu_day']}."
        elif lang == "mixed":
            return f"Ivala {info['day_name']}."
        else:
            return f"Today is {info['day_name']}."

    # Fallback to today
    info = get_relative_date(0)
    return f"Today is {info['day_name']}, {info['month_name']} {info['day']}, {info['year']}."
