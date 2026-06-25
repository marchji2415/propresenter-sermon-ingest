import re
import config
from models import RenderSlide
from references import parse_reference
from text_utils import (
    clean_text,
    clean_slide_line,
    clean_multiline_text,
    clean_single_line,
    to_caps,
    line_fits,
    text_width_px,
    wrap_words_by_pixels,
)


def split_into_verses(text_body):
    text_body = clean_text(text_body)
    matches = list(re.finditer(r"(?:^|\s)(\d+)\s", text_body))
    if not matches:
        return [("", text_body)]

    first_val = int(matches[0].group(1))
    expected = first_val
    verse_indices = []
    for m in matches:
        val = int(m.group(1))
        if val == expected:
            verse_indices.append((m.start(1), m.end(1), val))
            expected += 1

    if verse_indices:
        verses = []
        first_start = verse_indices[0][0]
        if first_start > 0:
            prefix = text_body[:first_start].strip()
            if prefix:
                verses.append(("", prefix))
        for idx, (start, end, val) in enumerate(verse_indices):
            next_start = verse_indices[idx+1][0] if idx + 1 < len(verse_indices) else len(text_body)
            v_text = text_body[end:next_start].strip()
            verses.append((str(val), v_text))
        return verses

    return [("", text_body)]


def split_sentences_for_slide(text):
    text = clean_text(text)
    # Split after sentence-ending punctuation only: . ! ? ;
    pieces = re.split(r"(?<=[.!?;])\s+", text)
    return [p.strip() for p in pieces if p.strip()]


def reference_to_book_chapter(reference):
    parsed = parse_reference(reference)
    return clean_single_line(f"{parsed.book_name} {parsed.chapter}").upper() if parsed else clean_single_line(reference).upper()


def make_reference_label(book_chapter, translation, verse_nums):
    book_chapter = clean_single_line(book_chapter)
    translation = clean_single_line(translation)

    if not verse_nums:
        return clean_single_line(f"{book_chapter} {translation}").upper()

    first = str(verse_nums[0]).strip()
    last = str(verse_nums[-1]).strip()

    if first == last:
        return clean_single_line(f"{book_chapter}:{first} {translation}").upper()

    return clean_single_line(f"{book_chapter}:{first}-{last} {translation}").upper()


def wrap_slide_text(text):
    text = clean_text(text).upper()
    lines = []
    for sentence in split_sentences_for_slide(text):
        wrapped = wrap_words_by_pixels(sentence, config.BODY_W, getattr(config, "SOFT_MAX_CHARS_PER_LINE", 46))
        lines.extend(wrapped)
    return [clean_slide_line(line).upper() for line in lines if clean_slide_line(line)]


def would_fit(lines):
    if len(lines) > config.MAX_LINES_PER_SLIDE:
        return False
    if any(not line_fits(line, config.BODY_W) for line in lines):
        return False
    if len(lines) * config.LINE_HEIGHT > config.BODY_H:
        return False
    return True


def score_slide(lines):
    if not lines:
        return 999999

    chars = len(" ".join(lines))
    score = 0

    # 3-4 line slides.
    if len(lines) == 4:
        score -= 25
    elif len(lines) == 3:
        score -= 12
    elif len(lines) == 2:
        score += 18
    else:
        score += 35

    score += abs(chars - config.TARGET_CHARS_PER_SLIDE) * 0.12

    if chars < config.MIN_CHARS_PER_SLIDE and len(lines) < 4:
        score += (config.MIN_CHARS_PER_SLIDE - chars) * 0.7

    if chars > config.MAX_CHARS_PER_SLIDE:
        score += (chars - config.MAX_CHARS_PER_SLIDE) * 1.0

    widths = [text_width_px(line) for line in lines]
    if widths:
        avg = sum(widths) / len(widths)
        score += sum(abs(w - avg) / 90 for w in widths)
        if widths[-1] < config.BODY_W * 0.2:
            score += 10

    # Grammar based line ending scoring to improve reading flow
    if lines:
        last_line = lines[-1].strip()
        if last_line:
            last_char = last_line[-1]
            if last_char in {".", "!", "?", ";"}:
                score -= 40
            elif last_char in {",", ":"}:
                score -= 20

            clean_last_line = re.sub(r"[.,;:!?\"'“”‘’()]", "", last_line).strip()
            if clean_last_line:
                last_word = clean_last_line.split()[-1].upper()
                WEAK_ENDINGS = {
                    "AND", "OR", "BUT", "FOR", "SO", "WITH", "THE", "A", "AN", 
                    "OF", "TO", "IN", "ON", "AT", "BY", "FROM", "AS", "IF", "THAT"
                }
                if last_word in WEAK_ENDINGS:
                    score += 80

    return score


def best_prefix_chunk(lines):
    """
    Choose 3-4 lines when possible.
    This avoids the old issue where the splitter created too many 2-line slides.
    """
    if len(lines) <= config.MAX_LINES_PER_SLIDE:
        return lines

    candidates = []
    for n in range(config.MAX_LINES_PER_SLIDE, 1, -1):
        chunk = lines[:n]
        if would_fit(chunk):
            candidates.append((score_slide(chunk), chunk))

    if candidates:
        return sorted(candidates, key=lambda x: x[0])[0][1]

    return lines[:config.MAX_LINES_PER_SLIDE]


def split_lines_optimally(lines):
    L = len(lines)
    if L == 0:
        return []
    if L <= config.MAX_LINES_PER_SLIDE:
        return [lines]

    memo = {}

    def solve(i):
        if i == L:
            return 0, []
        if i in memo:
            return memo[i]

        best_score = float('inf')
        best_partition = []

        for size in range(1, config.MAX_LINES_PER_SLIDE + 1):
            if i + size <= L:
                chunk = lines[i : i + size]
                if would_fit(chunk):
                    chunk_score = score_slide(chunk)
                    
                    # Penalize a single line hanging at the end to prevent single-line slides
                    if i + size == L and size == 1:
                        chunk_score += 150
                        
                    rem_score, rem_part = solve(i + size)
                    total = chunk_score + rem_score
                    if total < best_score:
                        best_score = total
                        best_partition = [chunk] + rem_part

        memo[i] = (best_score, best_partition)
        return memo[i]

    score, partition = solve(0)
    if not partition:
        # Fall back to greedy chunks
        partition = []
        rem = lines[:]
        while rem:
            partition.append(rem[:config.MAX_LINES_PER_SLIDE])
            rem = rem[config.MAX_LINES_PER_SLIDE:]
    return partition


def split_text_into_safe_clauses(text):
    # Split by major punctuation: , . ; : ! ? —
    raw_clauses = re.split(r"(?<=[,.;:!?—])\s+", text)
    safe_clauses = []
    
    for rc in raw_clauses:
        rc = rc.strip()
        if not rc:
            continue
            
        # Check if it fits on a slide when wrapped
        lines = wrap_slide_text(rc)
        if len(lines) <= config.MAX_LINES_PER_SLIDE:
            safe_clauses.append(rc)
        else:
            # It's too long! Split it by conjunctions or prepositions
            conj_pattern = r"\b(?:AND|BUT|OR|THAT|WHO|WHICH|FOR|SO|ALTHOUGH|BECAUSE|WHEN|WHERE|WHILE|WITH|TO|FROM|UNTIL|UNLESS)\b"
            sub_pieces = re.split(rf"(?<!\d)\s+(?={conj_pattern})", rc, flags=re.I)
            
            for sp in sub_pieces:
                sp = sp.strip()
                if not sp:
                    continue
                # Check if sp fits
                lines = wrap_slide_text(sp)
                if len(lines) <= config.MAX_LINES_PER_SLIDE:
                    safe_clauses.append(sp)
                else:
                    # Still too long! Split by words into chunks that fit
                    words = sp.split()
                    curr_chunk = []
                    for w in words:
                        test_chunk = " ".join(curr_chunk + [w])
                        if len(wrap_slide_text(test_chunk)) <= config.MAX_LINES_PER_SLIDE:
                            curr_chunk.append(w)
                        else:
                            if curr_chunk:
                                safe_clauses.append(" ".join(curr_chunk))
                            curr_chunk = [w]
                    if curr_chunk:
                        safe_clauses.append(" ".join(curr_chunk))
                        
    return safe_clauses


def score_candidate_slide(text, is_last_slide=False):
    lines = wrap_slide_text(text)
    if not lines or not would_fit(lines):
        return 999999
        
    # Line count preferences: strongly prefer 3-4 lines
    if len(lines) == 4:
        score = 0
    elif len(lines) == 3:
        score = 15
    elif len(lines) == 2:
        score = 45
    else: # 1 line
        score = 120
        if is_last_slide:
            score = 80

    # Character length balance
    chars = len(" ".join(lines))
    score += abs(chars - config.TARGET_CHARS_PER_SLIDE) * 0.2
    
    # Penalize extremely short slides
    if chars < config.MIN_CHARS_PER_SLIDE:
        score += (config.MIN_CHARS_PER_SLIDE - chars) * 1.5
        
    # Grammar checks at the end of the slide
    last_line = lines[-1].strip()
    if last_line:
        last_char = last_line[-1]
        if last_char in {".", "!", "?"}:
            score -= 50  # Strong sentence boundary bonus
        elif last_char == ";":
            score -= 30  # Semicolon boundary bonus
        elif last_char == ":":
            score -= 20
        elif last_char == ",":
            score -= 10  # Comma clause boundary bonus
            
        # Weak ending checks
        clean_last = re.sub(r"[.,;:!?\"'“”‘’()]", "", last_line).strip()
        if clean_last:
            last_word = clean_last.split()[-1].upper()
            WEAK_ENDINGS = {
                "AND", "OR", "BUT", "FOR", "SO", "WITH", "THE", "A", "AN", 
                "OF", "TO", "IN", "ON", "AT", "BY", "FROM", "AS", "IF", "THAT"
            }
            if last_word in WEAK_ENDINGS:
                score += 150  # Heavy penalty for ending on a preposition/conjunction
                
    return score


def partition_clauses_optimally(clauses):
    L = len(clauses)
    if L == 0:
        return []
        
    memo = {}
    
    def solve(i):
        if i == L:
            return 0, []
        if i in memo:
            return memo[i]
            
        best_score = float('inf')
        best_partition = []
        
        # Try to group clauses[i:j]
        for j in range(i + 1, min(i + 16, L + 1)):
            chunk_text = " ".join(clauses[i:j])
            lines = wrap_slide_text(chunk_text)
            
            if len(lines) <= config.MAX_LINES_PER_SLIDE and would_fit(lines):
                is_last = (j == L)
                chunk_score = score_candidate_slide(chunk_text, is_last)
                
                rem_score, rem_part = solve(j)
                total = chunk_score + rem_score
                
                if total < best_score:
                    best_score = total
                    best_partition = [chunk_text] + rem_part
                    
        memo[i] = (best_score, best_partition)
        return memo[i]
        
    score, partition = solve(0)
    if not partition:
        # Fallback: greedy
        partition = []
        curr = []
        for c in clauses:
            test = " ".join(curr + [c])
            if len(wrap_slide_text(test)) <= config.MAX_LINES_PER_SLIDE and would_fit(wrap_slide_text(test)):
                curr.append(c)
            else:
                if curr:
                    partition.append(" ".join(curr))
                curr = [c]
        if curr:
            partition.append(" ".join(curr))
            
    return partition


def extract_verse_numbers_from_text(text, valid_verses):
    matches = re.findall(r"(?:^|\s|\[)(\d+)(?:\s|\])", text)
    return [int(m) for m in matches if int(m) in valid_verses]


def fallback_scripture_to_render_slides(reference, translation, scripture_text):
    book_chapter = reference_to_book_chapter(reference)
    
    # 1. Split into verses to extract valid verse numbers for label mapping
    parsed_verses = split_into_verses(scripture_text)
    valid_verses = set()
    for num, txt in parsed_verses:
        if num:
            try:
                valid_verses.add(int(num))
            except:
                pass

    # 2. Clean scripture text
    scripture_text = clean_text(scripture_text)
    
    # 3. Split into safe clauses
    clauses = split_text_into_safe_clauses(scripture_text)
    
    # 4. Partition clauses optimally
    chunks = partition_clauses_optimally(clauses)
    
    # 5. Build render slides
    slides = []
    active_verses = []
    
    for chunk in chunks:
        # Extract verses that start inside this slide
        verses_in_slide = extract_verse_numbers_from_text(chunk, valid_verses)
        if verses_in_slide:
            active_verses = verses_in_slide
            
        label = make_reference_label(book_chapter, translation, active_verses)
        body = clean_single_line(chunk).upper()
        
        slides.append(RenderSlide("scripture", label, body, label))
        
    return slides


def normalize_words(text):
    text = clean_text(text).lower()
    text = re.sub(r"[^a-z0-9' ]", " ", text)
    return [w for w in text.split() if w]


def validate_ai_split(original, parsed):
    # Kept for optional AI mode. Manual splitter is default.
    slides = parsed.get("slides", [])
    if not slides:
        return False, "No slides returned."

    all_lines = []

    for i, slide in enumerate(slides, start=1):
        lines = slide.get("lines", [])

        if not lines:
            return False, f"Slide {i} has no lines."

        if len(lines) > config.MAX_LINES_PER_SLIDE:
            return False, f"Slide {i} has too many lines."

        for raw in lines:
            if re.search(r"LINE[_\s-]*BREAK|NEW[_\s-]*LINE|<br\s*/?>", str(raw), re.I):
                return False, f"Slide {i} contains line-break artifact."

            line = clean_slide_line(raw)

            if not line:
                return False, f"Slide {i} has empty/punctuation-only line."

            if not line_fits(line, config.BODY_W):
                return False, f"Line too wide on slide {i}: {line}"

            all_lines.append(line)

    if normalize_words(original) != normalize_words(" ".join(all_lines)):
        return False, "Word validation failed. AI changed, added, or removed words."

    return True, "OK"
