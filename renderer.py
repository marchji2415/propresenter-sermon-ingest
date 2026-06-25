import config
from ai_splitter import split_with_ai
from bible import fetch_scripture_text
from models import RenderSlide
from splitter import fallback_scripture_to_render_slides
from text_utils import clean_single_line, clean_multiline_text, to_caps
from logger import ok, warn

def scripture_to_slides(ref, trans, text, cache_root, ai_model, debug=False):
    if config.USE_AI_SPLITTER:
        try:
            slides = split_with_ai(ref, trans, text, cache_root, ai_model, debug)
            if slides:
                ok(f"AI split succeeded for {ref}: {len(slides)} slide(s).")
                return slides
        except Exception as e:
            warn(f"AI split failed for {ref}. Falling back to manual splitter. Reason: {e}")
    return fallback_scripture_to_render_slides(ref, trans, text)

def slide_items_to_render_slides(items, cache_root, translation_override=None, ai_model=None, debug=False):
    out = []
    for item in items:
        if item.kind == "title":
            title = clean_single_line(item.text).upper()
            out.append(RenderSlide("title", title, title)); continue
        if item.kind == "point":
            num = item.point_number or 1
            body = clean_single_line(item.text).upper()
            out.append(RenderSlide("point", f"POINT {num}", body, f"POINT {num}", num)); continue
        if item.kind == "scripture":
            ref = item.reference or item.text
            req = translation_override or item.translation or config.DEFAULT_TRANSLATION
            text = item.text.strip()
            used = req
            if not text:
                text, used = fetch_scripture_text(ref, req, cache_root, debug)
            if text:
                out.extend(scripture_to_slides(ref, used, text, cache_root, ai_model or (config.GEMINI_MODEL if config.AI_PROVIDER == 'gemini' else config.OPENROUTER_MODEL), debug))
            else:
                label = clean_single_line(f"{ref} {req}").upper()
                out.append(RenderSlide("scripture", label, to_caps(ref), label))
            continue
        if item.kind == "quote":
            quote_text = clean_single_line(item.text).upper()
            author = clean_single_line(item.reference).upper() if item.reference else "QUOTE"
            out.append(RenderSlide("quote", author, f'"{quote_text}"', author)); continue
        if item.kind == "sermon_statement":
            body = clean_single_line(item.text).upper()
            out.append(RenderSlide("sermon_statement", "SLIDE", body, "")); continue
    return out
