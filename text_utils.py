import os
import re
from PIL import ImageFont

import config
from logger import warn


GLUED_WORDS_MAP = {
    "RAISEDWITH": "RAISED WITH",
    "THEKINGDOM": "THE KINGDOM",
    "JESUSCHRIST": "JESUS CHRIST",
    "CHRISTJESUS": "CHRIST JESUS",
    "LORDJESUS": "LORD JESUS",
    "GODTHE": "GOD THE",
    "SONOF": "SON OF",
    "SPIRITOF": "SPIRIT OF",
    "CHRISTSIDE": "CHRIST SIDE",
    "HEAVENBOUND": "HEAVEN BOUND",
}


def fix_glued_common_words(text):
    """
    Conservative fixes for API/OCR/AI output where spaces disappear.
    Handles cases like:
    - THEREFORE,SINCE -> THEREFORE, SINCE
    - GOD.SET -> GOD. SET
    - 1IN -> 1 IN
    - RAISEDWITH -> RAISED WITH
    """
    text = str(text)

    # 1. Punctuation followed by word/digit (exclude quotes from lookahead to prevent inserting space before quote)
    text = re.sub(r",(?![0-9])(?=[A-Za-z0-9])", ", ", text)
    text = re.sub(r"\.(?![0-9])(?=[A-Za-z0-9])", ". ", text)
    text = re.sub(r":(?![0-9])(?=[A-Za-z0-9])", ": ", text)
    text = re.sub(r"([;!?])(?=[A-Za-z0-9])", r"\1 ", text)

    # 2. A closing quote followed by a letter/digit (e.g. "Hello,"he or test"word)
    text = re.sub(r'(?<=[A-Za-z0-9.,;:!?])([\"\'”’])(?=[A-Za-z0-9])', r'\1 ', text)

    # 3. verse number glued to first word: 1IN -> 1 IN
    text = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", text)

    # 4. punctuation must not have spaces preceding it
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)

    # Fix specific known glued words
    for glued, separated in GLUED_WORDS_MAP.items():
        text = re.sub(rf"\b{glued}\b", separated, text, flags=re.I)

    return text


def clean_text(text):
    if text is None:
        return ""

    text = str(text)
    
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    
    # Clean up literal newlines and raw carriage returns
    text = text.replace("\r", " ").replace("\n", " ")
    
    # Clean up forward/back-slash N markers (e.g. /N, \N, /n, \n) often used for manual page breaks
    text = re.sub(r"/\s*n", " ", text, flags=re.I)
    text = re.sub(r"\\\s*n", " ", text, flags=re.I)
    
    text = text.replace("\u00A0", " ")
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("”", '"').replace("“", '"')
    text = text.replace("…", "...")

    text = re.sub(r"\bLINE[_\s-]*BREAK\b", " ", text, flags=re.I)
    text = re.sub(r"\bNEW[_\s-]*LINE\b", " ", text, flags=re.I)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)

    text = re.sub(r"\[\[.*?\)\]", "", text)
    text = re.sub(r"\[[a-zA-Z]\]", "", text)

    text = fix_glued_common_words(text)

    # mixed-case glue from JSON/API extraction
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_slide_line(text):
    text = clean_text(text).replace("_", " ")
    text = re.sub(r"\s+", " ", text).strip()

    # Drop punctuation-only line leftovers such as "."
    if re.fullmatch(r"[\s\.,;:!?'\"“”‘’\-–—]+", text or ""):
        return ""

    return text


def clean_multiline_text(text):
    lines = []
    for raw in str(text or "").splitlines():
        line = clean_slide_line(raw)
        if line:
            lines.append(line)
    return "\n".join(lines).strip()


def clean_single_line(text):
    text = clean_multiline_text(text).replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()


def to_caps(text):
    return clean_text(text).upper().strip()


def safe_name(text, max_len=180):
    return clean_single_line(text).upper()[:max_len].strip()


def load_font(size):
    paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    warn("Font not found. Using Pillow default font.")
    return ImageFont.load_default()


_font_cache = {}

def get_font(font_name=None, font_size=None):
    if font_name is None:
        font_name = getattr(config, "FONT_NAME", "Arial")
    if font_size is None:
        font_size = getattr(config, "BODY_FONT_SIZE", 56)

    try:
        font_size = int(font_size)
    except:
        font_size = 28

    cache_key = (font_name, font_size)
    if cache_key in _font_cache:
        return _font_cache[cache_key]

    # Clean font name for checking inside local fonts folder
    clean_name = font_name.replace(" ", "").lower()
    local_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

    paths = [
        os.path.join(local_dir, f"{font_name}.ttf"),
        os.path.join(local_dir, f"{font_name}.otf"),
        os.path.join(local_dir, f"{clean_name}.ttf"),
        os.path.join(local_dir, f"{clean_name}.otf"),
        f"C:/Windows/Fonts/{font_name}.ttf",
        f"C:/Windows/Fonts/{font_name}.otf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    font = None
    for path in paths:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, font_size)
                break
            except:
                pass

    if font is None:
        try:
            font = ImageFont.load_default()
        except:
            pass

    _font_cache[cache_key] = font
    return font


def text_width_px(text, font=None):
    if font is None:
        font = get_font()
    bbox = font.getbbox(str(text))
    return bbox[2] - bbox[0]


def line_fits(text, max_width=None):
    if max_width is None:
        max_width = config.BODY_W
    margin_sub = getattr(config, "MARGIN_LEFT", 0) + getattr(config, "MARGIN_RIGHT", 0)
    # Apply an 80px safety margin to prevent wrapping in ProPresenter's text box due to internal padding/rendering difference
    return text_width_px(text) <= (max_width - margin_sub - 80)


def wrap_words_by_pixels(text, max_width=None, soft_max_chars=None):
    if max_width is None:
        max_width = config.BODY_W
    soft_max_chars = soft_max_chars or getattr(config, "SOFT_MAX_CHARS_PER_LINE", 46)
    words = clean_text(text).split()
    lines = []
    current = []

    for word in words:
        candidate = " ".join(current + [word])
        char_ok = len(candidate) <= soft_max_chars or not current
        pixel_ok = line_fits(candidate, max_width)

        if char_ok and pixel_ok:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]

    if current:
        lines.append(" ".join(current))

    return lines
