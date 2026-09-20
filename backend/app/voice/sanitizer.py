import re

# Comprehensive emoji and symbol Unicode pattern
# Covers:
# - Unicode emoji ranges (Emoticons, Pictographs, Transport/Map, Supplemental)
# - Dingbats U+2700-U+27BF (includes U+2764 red heart, U+2728 sparkles)
# - Miscellaneous Symbols U+2600-U+26FF (hearts, stars, warning signs)
# - Miscellaneous Technical U+2300-U+23FF
# - Supplemental Symbols and Pictographs U+1F900-U+1F9FF
# - Symbols and Pictographs Extended-A U+1FA70-U+1FAFF
# - Symbols for Legacy Computing U+1FB00-U+1FBFF
# - Enclosed Alphanumerics & Ideographs U+24C2-U+1F251
# - Stars and heavy circles U+2B50, U+2B55
# - Combining Enclosing Keycap U+20E3
# - Variation selectors U+FE00-U+FE0F, U+E0100-U+E01EF
# - Zero-Width Joiner U+200D
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons (e.g. 😀, 😂, 😊)
    "\U0001F300-\U0001F5FF"  # Symbols & pictographs (e.g. 🔥, 👍, 🎉, 💯)
    "\U0001F680-\U0001F6FF"  # Transport & map symbols
    "\U0001F700-\U0001F77F"  # Alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs (e.g. 🤣, 🥳, 🥰)
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A (e.g. 🩰, 🩵, 🩷)
    "\U0001FB00-\U0001FBFF"  # Symbols for Legacy Computing
    "\U00002700-\U000027BF"  # Dingbats (includes \u2764 heavy black/red heart, \u2728 sparkles)
    "\U00002600-\U000026FF"  # Miscellaneous symbols (hearts \u2665, stars, warning)
    "\U00002300-\U000023FF"  # Miscellaneous Technical
    "\U000024C2-\U0001F251"  # Enclosed characters
    "\U00002B50"              # Star
    "\U00002B55"              # Heavy Large Circle
    "\U000020E3"              # Combining enclosing keycap
    "\U0000200D"              # Zero-width joiner
    "\U0000FE00-\U0000FE0F"  # Variation selectors
    "\U000E0100-\U000E01EF"  # Variation selectors supplement
    "]+",
    flags=re.UNICODE
)

# Educational/technical terms that follow 'smiling face' and must NOT be stripped
FACE_TECHNICAL_TERMS = (
    r"detection|recognition|classifier|classification|dataset|tracking|"
    r"analysis|filter|algorithm|model|system|application|technology|feature|benchmark"
)


def sanitize_text_for_tts(text: str) -> str:
    """
    Cleans response text before passing to Text-to-Speech synthesis.
    Strictly guarantees that:
    1. Visual emojis and Unicode symbols are stripped.
    2. Spoken emoji names and descriptions ('winking face', 'smile face', 'red heart', etc.)
       are scrubbed so TTS NEVER pronounces them.
    3. Technical markdown/code/formatting artifacts are removed.
    4. Meaningful Telugu characters (U+0C00 to U+0C7F) are 100% preserved.
    """
    if not text or not text.strip():
        return ""

    cleaned = text

    # 1. Strip code blocks completely or replace with a conversational audio cue
    cleaned = re.sub(r"```[\w]*\n[\s\S]*?```", " [code snippet omitted] ", cleaned)

    # Convert markdown links [Label](url) -> Label
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)

    # Strip inline code `code` -> code
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)

    # Strip HTML/XML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)

    # 2. Strip actual Unicode emojis and decorative symbols
    cleaned = EMOJI_PATTERN.sub("", cleaned)

    # 3. Strip spoken emoji / symbol descriptive phrases
    # Compound descriptions (e.g. 'red heart smiling face', 'smiling face red heart', 'red heart, smiling face')
    compound_desc_patterns = [
        r"(?i)\b(?:red|pink|purple|blue|green|yellow|orange|black|white|brown|sparkling)?\s*heart\s*[,.]?\s*(?:and\s+)?(?:smiling|winking|smile)\s+face(?:\s+(?:emoji|symbol|icon))?\b",
        r"(?i)\b(?:smiling|winking|smile)\s+face(?:\s+(?:emoji|symbol|icon))?\s*[,.]?\s*(?:and\s+)?(?:red|pink|purple|blue|green|yellow|orange|black|white|brown|sparkling)?\s*heart(?:\s+(?:emoji|symbol|icon))?\b",
    ]
    for pattern in compound_desc_patterns:
        cleaned = re.sub(pattern, " ", cleaned)

    # Praise + heart: 'Great job! heart.', 'Awesome heart'
    cleaned = re.sub(
        r"(?i)\b(awesome|great\s+job|superb|well\s+done|congrats|congratulations)\s+heart(?=[\s.!?,;:]|$)",
        r"\1",
        cleaned
    )

    # Standalone heart preceded by punctuation like '! heart.' or '! heart'
    cleaned = re.sub(
        r"(?i)([!?,\n])\s*heart(?=[\s.!?,;:]|$)",
        r"\1",
        cleaned
    )

    # Heart emoji descriptions (preserves medical/educational terms)
    heart_desc_patterns = [
        # Color hearts: 'red heart', 'pink heart', 'blue heart', etc.
        r"(?i)\b(?:red|pink|blue|green|yellow|purple|orange|black|white|brown|sparkling)\s+heart(?:\s+(?:emoji|symbol|icon))?\b",
        # 'broken heart' except 'broken heart syndrome'
        r"(?i)\bbroken\s+heart(?!\s+syndrome)(?:\s+(?:emoji|symbol|icon))?\b",
        # Explicit heart emoji / symbol
        r"(?i)\bheart\s+(?:emoji|symbol|icon)\b",
        # Standalone decorative hearts: (heart), *heart*
        r"(?i)\((?:heart)\)",
        r"(?i)\*(?:heart)\*",
    ]
    for pattern in heart_desc_patterns:
        cleaned = re.sub(pattern, " ", cleaned)

    # Face descriptions (preserves technical phrases like 'smiling face detection')
    face_desc_patterns = [
        r"(?i)\bface\s+with\s+tears\s+of\s+joy\b",
        r"(?i)\bface\s+with\s+smiling\s+eyes\b",
        r"(?i)\bsmiling\s+face\s+with\s+(?:smiling\s+eyes|open\s+mouth|sunglasses)\b",
        r"(?i)\b(?:grinning|laughing|crying|sad|winking|smile|blushing|kissing)\s+face(?:\s+(?:emoji|symbol|icon))?\b",
        r"(?i)\bheart\s+eyes\b",
        r"(?i)\blaughing\s+emoji\b",
        r"(?i)\b(?:smiling|winking|smile)\s+face\s+(?:emoji|symbol|icon)\b",
        # Contextual smiling face (only if NOT followed by technical terms)
        rf"(?i)\b(?:smiling|winking|smile)\s+face(?!\s+(?:{FACE_TECHNICAL_TERMS}))\b",
    ]
    for pattern in face_desc_patterns:
        cleaned = re.sub(pattern, " ", cleaned)

    # Standalone sparkles preceded by punctuation or praise
    cleaned = re.sub(r"(?i)([!?,\n])\s*sparkles(?=[\s.!?,;:]|$)", r"\1", cleaned)
    cleaned = re.sub(r"(?i)\b(awesome|great\s+job|superb|well\s+done)\s+sparkles(?=[\s.!?,;:]|$)", r"\1", cleaned)

    # Other spoken emoji descriptions
    other_desc_patterns = [
        r"(?i)\b(?:fire|sparkles|thumbs\s*up|clapping\s+hands|party\s*popper|folded\s*hands)\s+(?:emoji|symbol|icon)\b",
        r"(?i)\bthumbs\s*up\b",
        r"(?i)\bclapping\s+hands\b",
        r"(?i)\bparty\s*popper\b",
        r"(?i)\bfire\s+emoji\b",
        r"(?i)\bfolded\s+hands\b",
        # Roleplay actions (*smiles*, (giggles))
        r"(?i)\*(?:smiles|laughs|giggles|chuckles|winks|nods|sighs|blushes|waves|whispers|gasps|shrugs|thinking)\*",
        r"(?i)\((?:smiles|laughs|giggles|chuckles|winks|nods|sighs|blushes|waves|whispers|gasps|shrugs|thinking)\)",
        # Text emoticons
        r"(?::\)|:-\)|:D|:-D|;\)|;-\)|:\(|:-\(|<3|</3|:P|:-P|xD|XD|\^_\^)",
    ]
    for pattern in other_desc_patterns:
        cleaned = re.sub(pattern, " ", cleaned)

    # 4. Strip markdown headers (#, ##, ### at line starts)
    cleaned = re.sub(r"^\s*#{1,6}\s*", "", cleaned, flags=re.MULTILINE)

    # Strip bold and italics (***text***, **text**, *text*, ___text___, __text__, _text_)
    cleaned = re.sub(r"\*{1,3}([^\*]+)\*{1,3}", r"\1", cleaned)
    cleaned = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", cleaned)

    # Strip blockquote indicators (> at line starts)
    cleaned = re.sub(r"^\s*>\s*", "", cleaned, flags=re.MULTILINE)

    # Strip decorative list markers (- , * , + , • ) at line starts
    cleaned = re.sub(r"^\s*[-*+•]\s+", "", cleaned, flags=re.MULTILINE)

    # Clean numbered list headers like "1. " or "2) " at line starts
    cleaned = re.sub(r"^\s*(\d+)[\.\)]\s+", r"\1: ", cleaned, flags=re.MULTILINE)

    # Strip horizontal rules (---, ___, ***)
    cleaned = re.sub(r"^\s*[-*_]{3,}\s*$", "", cleaned, flags=re.MULTILINE)

    # Strip decorative arrows (->, =>, ←, →, etc.)
    cleaned = re.sub(r"[-=]>\s*", "", cleaned)
    cleaned = re.sub(r"[←→↑↓↔↕↖↗↘↙]", "", cleaned)

    # Strip leftover rogue formatting symbols
    cleaned = re.sub(r"[~|\\^]", "", cleaned)

    # 5. Collapse whitespace and newlines
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n+", ". ", cleaned)
    cleaned = re.sub(r"\n+", " ", cleaned)

    # 6. Clean orphan punctuation left behind by removed descriptions
    cleaned = re.sub(r"\s+([.!?,;:])", r"\1", cleaned)
    cleaned = re.sub(r"([!?])\s*\.+", r"\1", cleaned)
    cleaned = re.sub(r",\s*([.!?])", r"\1", cleaned)

    # Clean duplicate non-ellipsis dots
    cleaned = re.sub(r"\.{4,}", "...", cleaned)
    cleaned = re.sub(r"(?<!\.)\.\.(?!\.)", ".", cleaned)
    cleaned = re.sub(r"!{2,}", "!", cleaned)
    cleaned = re.sub(r"\?{2,}", "?", cleaned)

    # Strip leading punctuation (unless it's a natural ellipsis '...')
    cleaned = re.sub(r"^(?!\.{3})[\s.,;:]+", "", cleaned)

    # Normalize space around punctuation
    cleaned = re.sub(r"\s+([.!?,;:])", r"\1", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = cleaned.strip()

    # 7. Return "" if nothing meaningful remains (no Telugu or alphanumeric characters)
    if not re.search(r"[\w\u0C00-\u0C7F]", cleaned):
        return ""

    # Complete explanation preserved (never truncate speech)
    return cleaned
