import os, json, socket, urllib.parse, urllib.request, urllib.error
import config
from cache import load_json, save_json
from logger import info, ok, warn, error, debug as log_debug
from references import parse_reference
from text_utils import clean_text

socket.setdefaulttimeout(6)

def http_get_json(url, timeout=6, debug=False):
    print(f"Fetching: {url}", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent":"sermon-ingest/0.1","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", errors="replace")
            log_debug(f"HTTP {getattr(r,'status',None)} {len(body)} chars", debug)
            return json.loads(body)
    except urllib.error.HTTPError as e:
        body = ""
        try: body = e.read().decode("utf-8", errors="replace")
        except Exception: pass
        raise RuntimeError(f"HTTP {e.code} for {url}. Body preview: {body[:400]}") from e
    except Exception as e:
        raise RuntimeError(f"Network/JSON error for {url}: {e}") from e

def translation_candidates(t):
    requested = (t or config.DEFAULT_TRANSLATION).upper()
    out = [requested]
    for f in config.TRANSLATION_FALLBACKS:
        f = f.upper()
        if f not in out: out.append(f)
    return out

def flatten_text(value, max_parts=2000):
    parts, seen = [], 0
    def collect(node):
        nonlocal seen
        if seen > max_parts: return
        seen += 1
        if node is None: return
        if isinstance(node, str): parts.append(node); return
        if isinstance(node, (int,float)): return
        if isinstance(node, list):
            for x in node: collect(x)
            return
        if isinstance(node, dict):
            for k in ["text","content","value","words"]:
                if k in node: collect(node[k]); return
            for k,v in node.items():
                if k.lower() in {"translation","book","links","audio","license","copyright","metadata","notes","footnotes"}:
                    continue
                collect(v)
    collect(value)
    return clean_text(" ".join(p for p in parts if p))

def extract_verses(data, debug=False):
    verses = []
    def add(num, txt):
        try: v = int(str(num).strip())
        except Exception: return
        txt = clean_text(txt)
        if txt: verses.append({"verse":v,"text":txt})
    # Explicitly check for HelloAO structure:
    if isinstance(data, dict) and "chapter" in data and isinstance(data["chapter"], dict):
        chapter_content = data["chapter"].get("content", [])
        if isinstance(chapter_content, list):
            for item in chapter_content:
                if isinstance(item, dict) and item.get("type") == "verse":
                    num = item.get("number")
                    val = item.get("content")
                    if num is not None and val is not None:
                        add(num, flatten_text(val))

    if not verses:
        candidates = []
        if isinstance(data, dict):
            candidates += [data.get("verses"), data.get("content")]
            if isinstance(data.get("chapter"), dict): candidates.append(data["chapter"].get("verses"))
            if isinstance(data.get("data"), dict): candidates.append(data["data"].get("verses"))
        for cand in candidates:
            if not isinstance(cand, list): continue
            for item in cand:
                if isinstance(item, dict):
                    num = item.get("verse") or item.get("verseNumber") or item.get("number") or item.get("v") or item.get("id")
                    val = item.get("text") if "text" in item else item.get("content") if "content" in item else item.get("value") if "value" in item else None
                    if num is not None and val is not None: add(num, flatten_text(val))
            if verses: break
    if not verses:
        visited = 0
        def visit(node):
            nonlocal visited
            if visited > 3000: return
            visited += 1
            if isinstance(node, dict):
                num = node.get("verse") or node.get("verseNumber") or node.get("number") or node.get("v")
                val = None
                for k in ["text","content","value"]:
                    if k in node: val = node[k]; break
                if num is not None and val is not None:
                    add(num, flatten_text(val)); return
                for k,v in node.items():
                    if k.lower() in {"translation","book","links","audio","license","copyright","metadata"}: continue
                    visit(v)
            elif isinstance(node, list):
                for x in node: visit(x)
        visit(data)
    dedup = {}
    for item in verses:
        if item["verse"] not in dedup and item["text"]: dedup[item["verse"]] = item["text"]
    result = [{"verse":v,"text":dedup[v]} for v in sorted(dedup)]
    log_debug(f"Extracted {len(result)} verses", debug)
    return result

def get_helloao_chapter(t, book, chapter, cache_root, debug=False):
    t, book = t.upper(), book.upper()
    path = os.path.join(cache_root, "bible", "helloao", t, f"{book}_{chapter}.json")
    cached = load_json(path)
    if cached is not None: return cached
    data = http_get_json(f"https://bible.helloao.org/api/{t}/{book}/{chapter}.json", 6, debug)
    save_json(path, data)
    return data

def bible_api_reference(parsed):
    if parsed.start_verse and parsed.end_verse and parsed.start_verse != parsed.end_verse:
        return f"{parsed.book_name} {parsed.chapter}:{parsed.start_verse}-{parsed.end_verse}"
    if parsed.start_verse: return f"{parsed.book_name} {parsed.chapter}:{parsed.start_verse}"
    return f"{parsed.book_name} {parsed.chapter}"

def fetch_from_bible_api(parsed, t, cache_root, debug=False):
    trans = (t or "WEB").lower()
    ref = bible_api_reference(parsed)
    enc = urllib.parse.quote(ref)
    path = os.path.join(cache_root, "bible", "bible-api", trans, f"{enc}.json")
    data = load_json(path)
    if data is None:
        data = http_get_json(f"https://bible-api.com/{enc}?translation={trans}", 6, debug)
        save_json(path, data)
    parts = []
    for item in data.get("verses", []):
        if item.get("verse") and item.get("text"):
            parts.append(f"{item['verse']} {clean_text(item['text'])}")
    if parts: return " ".join(parts), t.upper()
    txt = clean_text(data.get("text", ""))
    return (txt, t.upper()) if txt else ("", t.upper())

CANONICAL_BOOKS = [
    "GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT", "1SA", "2SA",
    "1KI", "2KI", "1CH", "2CH", "EZR", "NEH", "EST", "JOB", "PSA", "PRO",
    "ECC", "SNG", "ISA", "JER", "LAM", "EZK", "DAN", "HOS", "JOL", "AMO",
    "OBA", "JON", "MIC", "NAM", "HAB", "ZEP", "HAG", "ZEC", "MAL", "MAT",
    "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", "PHP",
    "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS", "1PE",
    "2PE", "1JN", "2JN", "3JN", "JUD", "REV"
]


def get_bolls_book_id(book_id_str):
    try:
        return CANONICAL_BOOKS.index(book_id_str.upper()) + 1
    except ValueError:
        return None


def get_bolls_chapter(t, book_id_str, chapter, cache_root, debug=False):
    t = t.upper()
    book_id_str = book_id_str.upper()
    book_num = get_bolls_book_id(book_id_str)
    if book_num is None:
        raise ValueError(f"Unknown book abbreviation for Bolls: {book_id_str}")
    path = os.path.join(cache_root, "bible", "bolls", t, f"{book_id_str}_{chapter}.json")
    cached = load_json(path)
    if cached is not None:
        return cached
    url = f"https://bolls.life/get-text/{t}/{book_num}/{chapter}/"
    data = http_get_json(url, 6, debug)
    save_json(path, data)
    return data


def extract_bolls_verses(data, start_verse=None, end_verse=None):
    verses = []
    for item in data:
        if isinstance(item, dict):
            num = item.get("verse")
            txt = clean_text(item.get("text", ""))
            if num is not None and txt:
                v = int(num)
                if start_verse is None:
                    verses.append({"verse": v, "text": txt})
                else:
                    end = end_verse or start_verse
                    if start_verse <= v <= end:
                        verses.append({"verse": v, "text": txt})
    return verses


def fetch_scripture_text(reference, translation, cache_root, debug=False):
    if not config.FETCH_SCRIPTURE_IF_MISSING: return "", translation
    parsed = parse_reference(reference)
    if not parsed:
        warn(f"Could not parse scripture reference: {reference}")
        return "", translation
    candidates = translation_candidates(translation)
    info(f"Fetching scripture: {reference} | requested={translation} | candidates={', '.join(candidates)} | book_id={parsed.book_id} chapter={parsed.chapter} verses={parsed.start_verse}-{parsed.end_verse}")
    for c in candidates:
        # Try Bolls Bible API first (supports ESV, NASB, NKJV, NIV, NLT, etc.)
        try:
            data = get_bolls_chapter(c, parsed.book_id, parsed.chapter, cache_root, debug)
            verses = extract_bolls_verses(data, parsed.start_verse, parsed.end_verse)
            if verses:
                ok(f"Fetched {reference} using Bolls API {c}: {len(verses)} verse(s).")
                return " ".join(f"{v['verse']} {v['text']}" for v in verses).strip(), c
        except Exception as e:
            warn(f"Bolls API failed for {c} {parsed.book_id} {parsed.chapter}: {e}")

        # Fallback to HelloAO
        try:
            data = get_helloao_chapter(c, parsed.book_id, parsed.chapter, cache_root, debug)
            print(f"Downloaded/cached {c} {parsed.book_id} {parsed.chapter}; extracting...", flush=True)
            verses = extract_verses(data, debug)
            print(f"Extracted {len(verses)} verse(s) from {c} {parsed.book_id} {parsed.chapter}", flush=True)
            if not verses: continue
            if parsed.start_verse is None: selected = verses
            else:
                end = parsed.end_verse or parsed.start_verse
                selected = [v for v in verses if parsed.start_verse <= v["verse"] <= end]
            if not selected: continue
            ok(f"Fetched {reference} using HelloAO {c}: {len(selected)} verse(s).")
            return " ".join(f"{v['verse']} {clean_text(v['text'])}" for v in selected).strip(), c
        except Exception as e:
            warn(f"HelloAO failed for {c} {parsed.book_id} {parsed.chapter}: {e}")
    backups = [c for c in candidates if c.upper() in {"WEB","KJV","ASV","BBE"}]
    for c in ["WEB","KJV","ASV"]:
        if c not in backups: backups.append(c)
    for c in backups:
        try:
            txt, used = fetch_from_bible_api(parsed, c, cache_root, debug)
            if txt:
                ok(f"Fetched {reference} using bible-api.com {used}.")
                return txt, used
        except Exception as e:
            warn(f"bible-api.com failed for {reference} {c}: {e}")
    error(f"All Bible API candidates failed for {reference}: {', '.join(candidates)}")
    return "", translation
