import os, hashlib
import config
from cache import load_json, save_json
from logger import ok, warn
from models import RenderSlide
from splitter import make_reference_label, reference_to_book_chapter, validate_ai_split
from text_utils import clean_slide_line, clean_multiline_text, clean_single_line, to_caps


def ai_cache_key(ref, trans, text, provider, model):
    return hashlib.sha256(f"{provider}|{model}|{trans}|{ref}|{text}|v6-gemini-fast".encode()).hexdigest()


def ai_cache_path(root, key):
    return os.path.join(root, "ai", f"{key}.json")


def build_prompt(ref, trans, text):
    return (
        "You are formatting Bible scripture for church presentation slides.\\n"
        "ONLY choose readable line breaks and slide breaks.\\n"
        "Do NOT change, add, remove, paraphrase, or reorder scripture words.\\n"
        "Preserve verse numbers exactly. Output ALL CAPS.\\n"
        "Never output LINE_BREAK, NEW_LINE, <br>, underscores for spaces, or punctuation-only lines.\\n"
        "Make sure punctuation has correct spacing: comma/period/colon/semicolon must be followed by a space when another word follows.\\n"
        f"Max {config.MAX_LINES_PER_SLIDE} lines per slide. Prefer {config.IDEAL_LINES_PER_SLIDE}-{config.MAX_LINES_PER_SLIDE} lines.\\n"
        f"Target about {config.TARGET_CHARS_PER_SLIDE} characters per slide, max about {config.MAX_CHARS_PER_SLIDE}.\\n"
        "It is okay to put 2 short consecutive verses on one slide if readable.\\n"
        "Do not make one tiny slide per verse unless the verse is long or context demands it.\\n"
        "Split by context, sentence flow, meaning, and breath points.\\n"
        f"Text box: {config.BODY_W}px wide by {config.BODY_H}px tall, font size {config.BODY_FONT_SIZE}.\\n"
        'Return JSON only: {"slides":[{"verse_start":"1","verse_end":"2","lines":["1 LINE ONE","LINE TWO","2 LINE THREE"]}]}\\n\\n'
        f"Reference: {ref} {trans}\\nScripture text:\\n{text}\\n"
    )


from ai_client import call_ai


def ai_response_to_slides(ref, trans, parsed):
    book_chapter = reference_to_book_chapter(ref)
    slides = []

    for slide in parsed.get("slides", []):
        lines = [to_caps(clean_slide_line(x)) for x in slide.get("lines", []) if clean_slide_line(x)]
        if not lines:
            continue

        start = str(slide.get("verse_start", "")).strip()
        end = str(slide.get("verse_end", start)).strip()

        if start and end:
            nums = [start] if start == end else [start, end]
            label = clean_single_line(make_reference_label(book_chapter, trans, nums)).upper()
        else:
            label = clean_single_line(f"{ref} {trans}").upper()

        body = clean_multiline_text("\\n".join(lines)).upper()
        slides.append(RenderSlide("scripture", label, body, label))

    return slides


def split_with_ai(ref, trans, scripture_text, cache_root, model=None, debug=False):
    if not config.USE_AI_SPLITTER:
        return None

    provider = config.AI_PROVIDER
    model = model or (config.GEMINI_MODEL if provider == "gemini" else config.OPENROUTER_MODEL)

    # If provider key is missing, fail immediately to manual splitter.
    if provider == "gemini" and not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    if provider == "openrouter" and not config.OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")

    key = ai_cache_key(ref, trans, scripture_text, provider, model)
    path = ai_cache_path(cache_root, key)
    cached = load_json(path)

    if cached:
        valid, reason = validate_ai_split(scripture_text, cached)
        if valid:
            ok(f"AI split cache hit for {ref}: {len(cached.get('slides', []))} slide(s).")
            return ai_response_to_slides(ref, trans, cached)
        warn(f"AI split cache invalid for {ref}: {reason}. Recalling AI.")

    print(f"Calling {provider} for {ref}...", flush=True)
    parsed = call_ai(build_prompt(ref, trans, scripture_text), provider, model, debug)

    valid, reason = validate_ai_split(scripture_text, parsed)
    if not valid:
        raise RuntimeError(f"AI validation failed: {reason}")

    save_json(path, parsed)
    return ai_response_to_slides(ref, trans, parsed)
