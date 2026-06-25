import re
from typing import Optional
from models import ParsedReference
from text_utils import clean_text
from logger import warn

BOOK_ID_MAP = {
    "GENESIS":"GEN","GEN":"GEN","EXODUS":"EXO","EXO":"EXO","LEVITICUS":"LEV","LEV":"LEV",
    "NUMBERS":"NUM","NUM":"NUM","DEUTERONOMY":"DEU","DEUT":"DEU","DEU":"DEU",
    "JOSHUA":"JOS","JOSH":"JOS","JOS":"JOS","JUDGES":"JDG","JDG":"JDG","RUTH":"RUT","RUT":"RUT",
    "1 SAMUEL":"1SA","1 SAM":"1SA","2 SAMUEL":"2SA","2 SAM":"2SA",
    "1 KINGS":"1KI","1 KGS":"1KI","2 KINGS":"2KI","2 KGS":"2KI",
    "1 CHRONICLES":"1CH","1 CHR":"1CH","2 CHRONICLES":"2CH","2 CHR":"2CH",
    "EZRA":"EZR","NEHEMIAH":"NEH","ESTHER":"EST","JOB":"JOB",
    "PSALM":"PSA","PSALMS":"PSA","PS":"PSA","PSA":"PSA","PROVERBS":"PRO","PROV":"PRO",
    "ECCLESIASTES":"ECC","ECC":"ECC","SONG OF SONGS":"SNG","SONG":"SNG","ISAIAH":"ISA","ISA":"ISA",
    "JEREMIAH":"JER","JER":"JER","LAMENTATIONS":"LAM","EZEKIEL":"EZK","EZEK":"EZK","DANIEL":"DAN","DAN":"DAN",
    "HOSEA":"HOS","JOEL":"JOL","AMOS":"AMO","OBADIAH":"OBA","JONAH":"JON","MICAH":"MIC","NAHUM":"NAM",
    "HABAKKUK":"HAB","ZEPHANIAH":"ZEP","HAGGAI":"HAG","ZECHARIAH":"ZEC","MALACHI":"MAL",
    "MATTHEW":"MAT","MATT":"MAT","MAT":"MAT","MARK":"MRK","MRK":"MRK","LUKE":"LUK","LUK":"LUK",
    "JOHN":"JHN","JHN":"JHN","ACTS":"ACT","ROMANS":"ROM","ROM":"ROM",
    "1 CORINTHIANS":"1CO","1 COR":"1CO","2 CORINTHIANS":"2CO","2 COR":"2CO",
    "GALATIANS":"GAL","EPHESIANS":"EPH","PHILIPPIANS":"PHP","PHIL":"PHP","COLOSSIANS":"COL","COL":"COL",
    "1 THESSALONIANS":"1TH","1 THESS":"1TH","2 THESSALONIANS":"2TH","2 THESS":"2TH",
    "1 TIMOTHY":"1TI","1 TIM":"1TI","2 TIMOTHY":"2TI","2 TIM":"2TI","TITUS":"TIT","PHILEMON":"PHM",
    "HEBREWS":"HEB","JAMES":"JAS","1 PETER":"1PE","1 PET":"1PE","2 PETER":"2PE","2 PET":"2PE",
    "1 JOHN":"1JN","1 JHN":"1JN","2 JOHN":"2JN","2 JHN":"2JN","3 JOHN":"3JN","3 JHN":"3JN",
    "JUDE":"JUD","REVELATION":"REV","REV":"REV",
}
BOOK_NAMES = sorted(BOOK_ID_MAP.keys(), key=len, reverse=True)
BOOK_PATTERN = "|".join([re.escape(b.title()) for b in BOOK_NAMES] + [re.escape(b) for b in BOOK_NAMES])
SCRIPTURE_REF_RE = re.compile(rf"(?i)\b(({BOOK_PATTERN})\.?)\s+(\d+)(?::(\d+)(?:-(\d+))?)?(?:\s+([A-Z]{{2,6}}))?\b")

def normalize_book_name(book):
    return re.sub(r"\s+", " ", book.replace(".", "").strip()).upper()

def parse_reference_from_match(match) -> Optional[ParsedReference]:
    original_book = match.group(1).replace(".", "").strip()
    book_id = BOOK_ID_MAP.get(normalize_book_name(original_book))
    if not book_id:
        warn(f"Could not map book name: {original_book}")
        return None
    chapter = int(match.group(3))
    start = int(match.group(4)) if match.group(4) else None
    end = int(match.group(5)) if match.group(5) else start
    translation = match.group(6)
    if start and end and start != end:
        original = f"{original_book} {chapter}:{start}-{end}"
    elif start:
        original = f"{original_book} {chapter}:{start}"
    else:
        original = f"{original_book} {chapter}"
    return ParsedReference(clean_text(original), original_book, book_id, chapter, start, end, translation)

def parse_reference(reference) -> Optional[ParsedReference]:
    match = SCRIPTURE_REF_RE.search(reference)
    return parse_reference_from_match(match) if match else None

def normalize_reference(match):
    parsed = parse_reference_from_match(match)
    if not parsed:
        return clean_text(match.group(0)), match.group(6)
    return parsed.original, parsed.translation
