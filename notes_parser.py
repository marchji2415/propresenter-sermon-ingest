import re
import hashlib
import os
import config
from models import SlideItem
from references import SCRIPTURE_REF_RE, normalize_reference
from text_utils import clean_text
from ai_client import call_ai
from cache import load_json, save_json
from logger import ok, warn

TITLE_RE = re.compile(r"(?i)^\s*title\s*:\s*(.+)$")
POINT_RE = re.compile(r"(?i)^\s*(?:point\s*(\d+)[:.)-]?\s*|(\d+)[).:-]\s+)(.+)$")
LOOSE_NUMBERED_POINT_RE = re.compile(r"^\s*(\d{1,2})\s+([A-Z][A-Z0-9'’ ,:&/-]{4,90})$")
QUOTE_RE = re.compile(r'^(.*?)\s*["“\'‘](.*?)["”\'’]\s*$')


def looks_like_point_text(text):
    text = clean_text(text)
    if not text:
        return False

    # Avoid treating scripture references as points.
    if SCRIPTURE_REF_RE.search(text):
        return False

    words = text.split()
    if len(words) > 12:
        return False

    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False

    uppercase_ratio = sum(1 for c in letters if c.isupper()) / max(1, len(letters))
    return uppercase_ratio >= 0.75


def is_media_instruction(line):
    line_upper = line.upper()
    media_patterns = [
        r"\bAPPEAR\s*:",
        r"\bQUEUED?\b",
        r"\bREQUESTED\b",
        r"\bCREATIVE\b",
        r"\bTABLE\b",
        r"\bGRAPHICS?\b",
        r"\bVIDEOS?\b",
        r"\bSCREENS?\b",
        r"\bMEDIA\b",
        r"\bTBD\b",
        r"\bLOGOS?\b",
        r"\bPREP\b",
        r"\bBACKGROUNDS?\b",
        r"\bIMAGES?\b",
        r"\bCLIPS?\b"
    ]
    if line.startswith("(") and line.endswith(")"):
        return True
    for pat in media_patterns:
        if re.search(pat, line_upper):
            return True
    return False


def is_quote(line):
    if any(q in line for q in ['"', '“', '”', '‘', '’']):
        return True
    return False


def looks_like_author(text):
    text = text.strip()
    if not text:
        return True
    words = text.split()
    if len(words) > 4:
        return False
    if not all(w[0].isupper() or w[0] in "'-" for w in words if w and w[0].isalpha()):
        return False
    return True


def is_sermon_statement(line):
    cleaned = clean_text(line)
    if len(cleaned) < 20:
        return False
    if not re.match(r"^[A-Z\"'“‘]", cleaned):
        return False
    return True


def build_notes_parser_prompt(raw_text):
    return f"""You are formatting church sermon notes to prepare slides for church presentation software (ProPresenter 7).
Your task is to analyze the input text and segment it into a list of structured items.

Available item kinds and rules:
1. "title": The main sermon title (e.g. "SET THE MIND RIGHT"). There should only be one title.
2. "point": Numbered sermon points or major teaching slides (e.g., "1) THE OLD LIFE IS DEAD & GONE"). Fill "point_number" with the integer if present, or leave it null.
3. "scripture": Scripture references cited in the notes (e.g., "Col 3:1-11 NASB", "John 12:24-26"). Set "reference" to the normalized reference (e.g., "Colossians 3:1-11") and "translation" to the translation (e.g., "NASB", "ESV") if specified. Do not include full scripture verses in the text attribute - the engine will fetch the scripture automatically.
4. "quote": Direct quotes from authors, books, or historical figures. Capture the quote text in "text" and the author's name in "reference". Do NOT classify general Bible verses or normal sermon teaching points as quotes, even if they have quotation marks inside them. Only classify it as a quote if it is an actual quote from an author or person (e.g., Dietrich Bonhoeffer "When Christ calls...").
5. "sermon_statement": Key teaching sentences/statements by the preacher to be displayed on slides for the congregation to read. Usually 1-3 lines long.
6. "media_note": Production instructions to the media/graphics/creative team, videos, graphics, tables, or side notes (e.g., "Leopard print Book (i will queue it)", or "THIS TABLE HAS BEEN REQUESTED..."). If a table is requested, capture the table description and all its rows/headers in this item's text, preserving their layout.

Rules for quotes and statements:
- Personal side-notes and media instructions should always be "media_note" so they are kept in the production report and not shown on screen.
- Only classify as "quote" if there is an author or it is a book excerpt.
- If it is a key message, statement, or quote by the preacher, classify as "sermon_statement".

Return ONLY a JSON object with the following schema:
{{
  "items": [
    {{
      "kind": "title" | "point" | "scripture" | "quote" | "sermon_statement" | "media_note",
      "text": "The text content (leave empty for scripture)",
      "reference": "(optional) Scripture reference or quote author",
      "translation": "(optional) Bible translation for scripture",
      "point_number": (optional integer) Point number
    }}
  ]
}}

Input Sermon Notes:
{raw_text}
"""

def ai_parsed_to_slide_items(parsed, translation_override=None):
    items = []
    for item in parsed.get("items", []):
        kind = item.get("kind", "").strip().lower()
        if kind not in {"title", "point", "scripture", "quote", "sermon_statement", "media_note"}:
            continue
            
        text = item.get("text") or ""
        reference = item.get("reference") or ""
        translation = translation_override or item.get("translation") or ""
        point_number = item.get("point_number")
        
        if point_number is not None:
            try:
                point_number = int(point_number)
            except:
                point_number = None
                
        if kind == "scripture":
            if not reference and text:
                reference = text
            text = ""
            
        items.append(
            SlideItem(
                kind=kind,
                text=text.strip(),
                reference=reference.strip() if reference else None,
                translation=translation.strip() if translation else None,
                point_number=point_number
            )
        )
    return items

def parse_sermon_notes_with_ai(raw_text, cache_root, translation_override=None, ai_model=None, debug=False):
    provider = config.AI_PROVIDER
    model = ai_model or (config.GEMINI_MODEL if provider == "gemini" else config.OPENROUTER_MODEL)
    
    if provider == "gemini" and not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    if provider == "openrouter" and not config.OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")
        
    key = hashlib.sha256(f"{provider}|{model}|{raw_text}|v3-parser".encode()).hexdigest()
    path = os.path.join(cache_root, "ai_parser", f"{key}.json")
    cached = load_json(path)
    
    if cached:
        ok(f"AI notes parser cache hit: {len(cached.get('items', []))} item(s).")
        return ai_parsed_to_slide_items(cached, translation_override)
        
    print(f"Calling AI notes parser ({provider}/{model})...", flush=True)
    prompt = build_notes_parser_prompt(raw_text)
    parsed = call_ai(prompt, provider, model, debug)
    
    save_json(path, parsed)
    return ai_parsed_to_slide_items(parsed, translation_override)

def parse_sermon_notes(raw_text, cache_root=None, translation_override=None, ai_model=None, debug=False):
    if config.USE_AI_PARSER and cache_root:
        try:
            return parse_sermon_notes_with_ai(
                raw_text,
                cache_root,
                translation_override=translation_override,
                ai_model=ai_model,
                debug=debug
            )
        except Exception as e:
            warn(f"AI notes parsing failed: {e}. Falling back to heuristic notes parser.")
            
    return parse_sermon_notes_heuristics(raw_text, translation_override)

def parse_sermon_notes_heuristics(raw_text, translation_override=None):
    raw_lines = [clean_text(line) for line in raw_text.splitlines()]
    raw_lines = [line for line in raw_lines if line]

    # Pre-pass: merge wrapped lines (like split sentences, quotes)
    merged_lines = []
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        while i + 1 < len(raw_lines):
            next_line = raw_lines[i + 1]
            is_continuation = False
            first_char = next_line.strip()[0] if next_line.strip() else ""
            
            if first_char.islower():
                is_continuation = True
            elif line.endswith(",") or line.split()[-1].lower() in {"and", "or", "but", "of", "to", "for", "with", "in", "on", "at"}:
                if not (TITLE_RE.match(next_line) or POINT_RE.match(next_line) or LOOSE_NUMBERED_POINT_RE.match(next_line) or SCRIPTURE_REF_RE.search(next_line)):
                    is_continuation = True
            elif (line.count('"') % 2 != 0 or line.count('“') != line.count('”') or line.count('‘') != line.count('’')):
                if not (TITLE_RE.match(next_line) or POINT_RE.match(next_line) or LOOSE_NUMBERED_POINT_RE.match(next_line) or SCRIPTURE_REF_RE.search(next_line)):
                    is_continuation = True
                    
            if is_continuation:
                line = f"{line} {next_line}"
                i += 1
            else:
                break
        merged_lines.append(line)
        i += 1

    raw_lines = merged_lines

    items = []
    default_translation = translation_override or config.DEFAULT_TRANSLATION
    auto_point_number = 1
    i = 0

    current_media_note_lines = []

    def flush_media_note():
        nonlocal current_media_note_lines
        if current_media_note_lines:
            text = "\n".join(current_media_note_lines)
            items.append(SlideItem("media_note", text))
            current_media_note_lines = []

    while i < len(raw_lines):
        line = raw_lines[i]
        upper = line.upper()

        if "ALL VERSES IN" in upper:
            possible = re.findall(r"\b(ESV|NIV|NASB|BSB|WEB|KJV|ASV|LSB|NLT|NKJV)\b", upper)
            if possible and not translation_override:
                default_translation = possible[-1]
            i += 1
            continue

        title = TITLE_RE.match(line)
        point = POINT_RE.match(line)
        loose_point = LOOSE_NUMBERED_POINT_RE.match(line)
        scripture_match = SCRIPTURE_REF_RE.search(line)

        # Flush media note if we hit any standard slide triggers
        if title or point or loose_point or scripture_match:
            flush_media_note()

        if title:
            items.append(SlideItem("title", title.group(1)))
            i += 1
            continue

        if point:
            explicit = point.group(1) or point.group(2)
            num = int(explicit) if explicit else auto_point_number
            text = point.group(3).strip()
            if i + 1 < len(raw_lines) and looks_like_point_text(raw_lines[i + 1]):
                text = f"{text} {raw_lines[i + 1]}"
                i += 1
            auto_point_number = num + 1
            items.append(SlideItem("point", text, point_number=num))
            i += 1
            continue

        if loose_point and looks_like_point_text(loose_point.group(2)):
            num = int(loose_point.group(1))
            text = loose_point.group(2).strip()
            if i + 1 < len(raw_lines) and looks_like_point_text(raw_lines[i + 1]):
                text = f"{text} {raw_lines[i + 1]}"
                i += 1
            auto_point_number = num + 1
            items.append(SlideItem("point", text, point_number=num))
            i += 1
            continue

        if scripture_match:
            reference, inline_translation = normalize_reference(scripture_match)
            items.append(
                SlideItem(
                    "scripture",
                    "",
                    reference=reference,
                    translation=translation_override or inline_translation or default_translation,
                )
            )
            i += 1
            continue

        # Media instructions / side notes
        if is_media_instruction(line):
            flush_media_note()
            current_media_note_lines.append(line)
            i += 1
            continue

        if current_media_note_lines:
            if len(line) < 40 or not is_sermon_statement(line):
                current_media_note_lines.append(line)
                i += 1
                continue
            else:
                flush_media_note()

        # Quotes
        if is_quote(line):
            quote_match = QUOTE_RE.match(line)
            if quote_match and looks_like_author(quote_match.group(1)):
                author = quote_match.group(1).strip()
                quote_text = quote_match.group(2).strip()
                items.append(SlideItem("quote", quote_text, reference=author))
            else:
                items.append(SlideItem("quote", line))
            i += 1
            continue

        # Sermon statements
        if is_sermon_statement(line):
            items.append(SlideItem("sermon_statement", line))
            i += 1
            continue

        i += 1

    flush_media_note()
    return items
