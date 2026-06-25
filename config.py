import os

DEFAULT_TRANSLATION = "ESV"
TRANSLATION_FALLBACKS = ["BSB", "WEB", "KJV"]
FETCH_SCRIPTURE_IF_MISSING = True

ENABLE_AI_BY_DEFAULT = False
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/free")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

AI_PROVIDER = os.environ.get("AI_PROVIDER", "gemini").lower()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
GEMINI_API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
USE_AI_SPLITTER = ENABLE_AI_BY_DEFAULT and bool(GEMINI_API_KEY or OPENROUTER_API_KEY)
USE_AI_PARSER = ENABLE_AI_BY_DEFAULT and bool(GEMINI_API_KEY or OPENROUTER_API_KEY)

AI_MAX_RETRIES = 3
AI_BASE_SLEEP_SECONDS = 2
AI_TIMEOUT_SECONDS = 10

# Canvas dimensions
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
FONT_NAME = "Helvetica Neue"
FONT_FAMILY = "Helvetica Neue"
FONT_FACE = "Regular"

MARGIN_LEFT = 0
MARGIN_RIGHT = 0

IS_LABEL_BOLD = True
IS_BODY_BOLD = False
IS_POINT_LABEL_BOLD = True
IS_POINT_BODY_BOLD = True
IS_TITLE_BOLD = True

BODY_X = 160
BODY_Y = 80
BODY_W = 1600
BODY_H = 400
BODY_FONT_SIZE = 56

LABEL_X = 0
LABEL_Y = 480
LABEL_W = 1920
LABEL_H = 110
LABEL_FONT_SIZE = 64

MAX_LINES_PER_SLIDE = 4
IDEAL_LINES_PER_SLIDE = 3
LINE_HEIGHT = 76

SAFE_MAX_CHARS_PER_LINE = 48
MIN_CHARS_PER_SLIDE = 110
TARGET_CHARS_PER_SLIDE = 180
MAX_CHARS_PER_SLIDE = 210

POINT_NUMBER_X = 0
POINT_NUMBER_Y = 174
POINT_NUMBER_W = 1920
POINT_NUMBER_H = 84
POINT_NUMBER_FONT_SIZE = 72

POINT_CONTENT_X = 0
POINT_CONTENT_Y = 274
POINT_CONTENT_W = 1920
POINT_CONTENT_H = 400
POINT_CONTENT_FONT_SIZE = 88

TITLE_X = 0
TITLE_Y = 0
TITLE_W = 1920
TITLE_H = 600
TITLE_FONT_SIZE = 96

NIL_UUID = "00000000-0000-0000-0000-000000000000"

# Curated manual splitter tuning
TARGET_LINES_PER_SLIDE = 4
SOFT_MAX_CHARS_PER_LINE = 46

SELECTED_LOCATION = "midtown"

THEME_CONFIGS = {
    "midtown": {
        "canvas_width": 1920,
        "canvas_height": 1080,
        "font_name": "Helvetica Neue",
        "font_family": "Helvetica Neue",
        "font_face": "Regular",
        "is_label_bold": True,
        "is_body_bold": False,
        "is_point_label_bold": True,
        "is_point_body_bold": True,
        "is_title_bold": True,
        
        "title_x": 0,
        "title_y": 0,
        "title_w": 1920,
        "title_h": 600,
        "title_font_size": 96,
        
        "point_number_x": 0,
        "point_number_y": 174,
        "point_number_w": 1920,
        "point_number_h": 84,
        "point_number_font_size": 72,
        
        "point_content_x": 0,
        "point_content_y": 274,
        "point_content_w": 1920,
        "point_content_h": 400,
        "point_content_font_size": 88,
        
        "body_x": 160,
        "body_y": 80,
        "body_w": 1600,
        "body_h": 400,
        "body_font_size": 56,
        
        "label_x": 0,
        "label_y": 480,
        "label_w": 1920,
        "label_h": 110,
        "label_font_size": 64,
        
        "max_lines_per_slide": 4,
        "ideal_lines_per_slide": 3,
        "safe_max_chars_per_line": 48,
        "target_chars_per_slide": 180,
        "min_chars_per_slide": 110,
        "max_chars_per_slide": 210,
        "soft_max_chars_per_line": 46,
        "line_height": 76,
        "margin_left": 100,
        "margin_right": 100,
    },
    "downtown": {
        "canvas_width": 840,
        "canvas_height": 1080,
        "font_name": "HenusRegular",
        "font_family": "Henus",
        "font_face": "Regular",
        "is_label_bold": False,
        "is_body_bold": False,
        "is_point_label_bold": False,
        "is_point_body_bold": False,
        "is_title_bold": False,
        
        "title_x": 50,
        "title_y": 300,
        "title_w": 740,
        "title_h": 400,
        "title_font_size": 48,
        
        "point_number_x": 50,
        "point_number_y": 179.7,
        "point_number_w": 740.0,
        "point_number_h": 83.16,
        "point_number_font_size": 23.247,
        
        "point_content_x": 106.9,
        "point_content_y": 290.4,
        "point_content_w": 663.55,
        "point_content_h": 381.54,
        "point_content_font_size": 28.929,
        
        "body_x": 88.2,
        "body_y": 158.5,
        "body_w": 663.55,
        "body_h": 381.54,
        "body_font_size": 28.929,
        
        "label_x": 50.0,
        "label_y": 577.04,
        "label_w": 740.0,
        "label_h": 83.16,
        "label_font_size": 23.247,
        
        "max_lines_per_slide": 4,
        "ideal_lines_per_slide": 3,
        "safe_max_chars_per_line": 28,
        "target_chars_per_slide": 90,
        "min_chars_per_slide": 45,
        "max_chars_per_slide": 110,
        "soft_max_chars_per_line": 26,
        "line_height": 42,
        "margin_left": 0,
        "margin_right": 0,
    }
}

def set_location_theme(location_name):
    global CANVAS_WIDTH, CANVAS_HEIGHT, FONT_NAME, FONT_FAMILY, FONT_FACE
    global IS_LABEL_BOLD, IS_BODY_BOLD, IS_POINT_LABEL_BOLD, IS_POINT_BODY_BOLD, IS_TITLE_BOLD
    global TITLE_X, TITLE_Y, TITLE_W, TITLE_H, TITLE_FONT_SIZE
    global POINT_NUMBER_X, POINT_NUMBER_Y, POINT_NUMBER_W, POINT_NUMBER_H, POINT_NUMBER_FONT_SIZE
    global POINT_CONTENT_X, POINT_CONTENT_Y, POINT_CONTENT_W, POINT_CONTENT_H, POINT_CONTENT_FONT_SIZE
    global BODY_X, BODY_Y, BODY_W, BODY_H, BODY_FONT_SIZE
    global LABEL_X, LABEL_Y, LABEL_W, LABEL_H, LABEL_FONT_SIZE
    global MAX_LINES_PER_SLIDE, IDEAL_LINES_PER_SLIDE, SAFE_MAX_CHARS_PER_LINE
    global TARGET_CHARS_PER_SLIDE, MIN_CHARS_PER_SLIDE, MAX_CHARS_PER_SLIDE
    global SOFT_MAX_CHARS_PER_LINE, LINE_HEIGHT
    global SELECTED_LOCATION
    global MARGIN_LEFT, MARGIN_RIGHT
    
    loc = location_name.lower().strip()
    if loc not in {"midtown", "downtown"}:
        raise ValueError(f"Unknown location theme: {location_name}")
        
    SELECTED_LOCATION = loc
    cfg = THEME_CONFIGS[loc]
    
    CANVAS_WIDTH = cfg["canvas_width"]
    CANVAS_HEIGHT = cfg["canvas_height"]
    FONT_NAME = cfg["font_name"]
    FONT_FAMILY = cfg["font_family"]
    FONT_FACE = cfg["font_face"]
    
    MARGIN_LEFT = cfg.get("margin_left", 0)
    MARGIN_RIGHT = cfg.get("margin_right", 0)
    
    IS_LABEL_BOLD = cfg["is_label_bold"]
    IS_BODY_BOLD = cfg["is_body_bold"]
    IS_POINT_LABEL_BOLD = cfg["is_point_label_bold"]
    IS_POINT_BODY_BOLD = cfg["is_point_body_bold"]
    IS_TITLE_BOLD = cfg["is_title_bold"]
    
    TITLE_X = cfg["title_x"]
    TITLE_Y = cfg["title_y"]
    TITLE_W = cfg["title_w"]
    TITLE_H = cfg["title_h"]
    TITLE_FONT_SIZE = cfg["title_font_size"]
    
    POINT_NUMBER_X = cfg["point_number_x"]
    POINT_NUMBER_Y = cfg["point_number_y"]
    POINT_NUMBER_W = cfg["point_number_w"]
    POINT_NUMBER_H = cfg["point_number_h"]
    POINT_NUMBER_FONT_SIZE = cfg["point_number_font_size"]
    
    POINT_CONTENT_X = cfg["point_content_x"]
    POINT_CONTENT_Y = cfg["point_content_y"]
    POINT_CONTENT_W = cfg["point_content_w"]
    POINT_CONTENT_H = cfg["point_content_h"]
    POINT_CONTENT_FONT_SIZE = cfg["point_content_font_size"]
    
    BODY_X = cfg["body_x"]
    BODY_Y = cfg["body_y"]
    BODY_W = cfg["body_w"]
    BODY_H = cfg["body_h"]
    BODY_FONT_SIZE = cfg["body_font_size"]
    
    LABEL_X = cfg["label_x"]
    LABEL_Y = cfg["label_y"]
    LABEL_W = cfg["label_w"]
    LABEL_H = cfg["label_h"]
    LABEL_FONT_SIZE = cfg["label_font_size"]
    
    MAX_LINES_PER_SLIDE = cfg["max_lines_per_slide"]
    IDEAL_LINES_PER_SLIDE = cfg["ideal_lines_per_slide"]
    SAFE_MAX_CHARS_PER_LINE = cfg["safe_max_chars_per_line"]
    
    TARGET_CHARS_PER_SLIDE = cfg["target_chars_per_slide"]
    MIN_CHARS_PER_SLIDE = cfg["min_chars_per_slide"]
    MAX_CHARS_PER_SLIDE = cfg["max_chars_per_slide"]
    
    SOFT_MAX_CHARS_PER_LINE = cfg["soft_max_chars_per_line"]
    LINE_HEIGHT = cfg["line_height"]
