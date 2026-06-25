from dataclasses import dataclass
from typing import Optional

@dataclass
class SlideItem:
    kind: str
    text: str
    reference: Optional[str] = None
    translation: Optional[str] = None
    point_number: Optional[int] = None

@dataclass
class RenderSlide:
    kind: str
    name: str
    body: str
    label: str = ""
    point_number: Optional[int] = None

@dataclass
class ParsedReference:
    original: str
    book_name: str
    book_id: str
    chapter: int
    start_verse: Optional[int]
    end_verse: Optional[int]
    translation: Optional[str]
