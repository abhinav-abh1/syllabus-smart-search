import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import os
import io
import hashlib
from django.conf import settings
from .models import ExtractedText, ExtractedDiagram


# --------------------------------------------------
# OCR CONFIG (IMPROVED)
# --------------------------------------------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

OCR_CONFIG = "--oem 3 --psm 6"  # Best balance for textbooks


# --------------------------------------------------
# MAIN EXTRACTION FUNCTION
# --------------------------------------------------
def extract_pdf_content(uploaded_pdf):
    """
    Optimized hybrid PDF extraction:
    - Native text first
    - OCR fallback only when needed
    - Noise reduction
    - Duplicate prevention
    """

    pdf_path = uploaded_pdf.pdf_file.path
    doc = fitz.open(pdf_path)

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_number = page_index + 1

        # ===============================
        # TEXT EXTRACTION
        # ===============================
        raw_text = page.get_text("text").strip()

        # OCR fallback ONLY if text is weak
        if is_text_insufficient(raw_text):
            raw_text = extract_text_with_ocr(page)

        if raw_text:
            paragraphs = split_into_paragraphs(raw_text)

            for para in paragraphs:
                if not is_valid_paragraph(para):
                    continue

                content_hash = generate_hash(para)

                # Prevent duplicates (IMPORTANT)
                if ExtractedText.objects.filter(
                    pdf=uploaded_pdf, content_hash=content_hash
                ).exists():
                    continue

                ExtractedText.objects.create(
                    pdf=uploaded_pdf,
                    page_number=page_number,
                    content=para,
                    content_hash=content_hash,
                    is_definition=is_definition_paragraph(para),
                )

        # ===============================
        # IMAGE / DIAGRAM EXTRACTION
        # ===============================
        extract_diagrams(doc, page, uploaded_pdf, page_number)

    doc.close()


# --------------------------------------------------
# OCR FUNCTION (IMPROVED QUALITY)
# --------------------------------------------------
def extract_text_with_ocr(page):
    """
    Converts PDF page to high-quality image and extracts text via OCR
    """
    pix = page.get_pixmap(dpi=300, alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))

    text = pytesseract.image_to_string(img, lang="eng", config=OCR_CONFIG)

    return clean_ocr_text(text)


# --------------------------------------------------
# DIAGRAM EXTRACTION (DEDUPLICATION SAFE)
# --------------------------------------------------
def extract_diagrams(doc, page, uploaded_pdf, page_number):
    image_list = page.get_images(full=True)

    for img_index, img in enumerate(image_list):
        xref = img[0]
        base_image = doc.extract_image(xref)

        image_bytes = base_image["image"]
        image_ext = base_image["ext"]

        image_hash = hashlib.md5(image_bytes).hexdigest()

        if ExtractedDiagram.objects.filter(
            pdf=uploaded_pdf, image_hash=image_hash
        ).exists():
            continue

        image_name = f"{uploaded_pdf.id}_page{page_number}_{img_index}.{image_ext}"
        image_path = os.path.join(settings.MEDIA_ROOT, "diagrams", image_name)

        os.makedirs(os.path.dirname(image_path), exist_ok=True)

        with open(image_path, "wb") as f:
            f.write(image_bytes)

        ExtractedDiagram.objects.create(
            pdf=uploaded_pdf,
            page_number=page_number,
            image=f"diagrams/{image_name}",
            image_hash=image_hash,
            caption=None,
        )


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def is_text_insufficient(text):
    """
    Detects when OCR is needed
    """
    return not text or len(text) < 80


def is_valid_paragraph(text):
    """
    Filters noise
    """
    words = text.split()
    if len(words) < 6:
        return False
    if text.isupper():
        return False
    return True


def clean_ocr_text(text):
    """
    OCR noise cleanup
    """
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if len(line.split()) >= 4:
            lines.append(line)
    return " ".join(lines)


def split_into_paragraphs(text):
    paragraphs = []
    buffer = ""

    for line in text.split("\n"):
        line = line.strip()
        if line:
            buffer += " " + line
        else:
            if buffer.strip():
                paragraphs.append(buffer.strip())
                buffer = ""

    if buffer.strip():
        paragraphs.append(buffer.strip())

    return paragraphs


def generate_hash(text):
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def is_definition_paragraph(text):
    keywords = [
        "is defined as",
        "refers to",
        "is the process of",
        "can be defined as",
        "means",
        "is known as",
        "may be defined as",
        "can be described as",
    ]

    text_lower = text.lower()
    return any(k in text_lower for k in keywords)
