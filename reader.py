import os
from docx import Document
try:
    import fitz
except ImportError:
    fitz = None

def read_docx_text(path):
    doc = Document(path)
    return "\n".join(p.text.replace("\xa0", " ").strip() for p in doc.paragraphs if p.text.strip())

def read_pdf_text(path):
    if fitz is None:
        raise ImportError("Install PDF support with: pip install pymupdf")
    doc = fitz.open(path)
    return "\n".join(page.get_text("text") for page in doc)

def read_input_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx": return read_docx_text(path)
    if ext == ".pdf": return read_pdf_text(path)
    if ext == ".txt":
        with open(path, "r", encoding="utf-8") as f: return f.read()
    raise ValueError(f"Unsupported file type: {ext}")
