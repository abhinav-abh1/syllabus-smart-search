import fitz  # PyMuPDF
from PIL import Image
import os
from django.conf import settings
from .models import ExtractedText, ExtractedDiagram


def extract_pdf_content(uploaded_pdf):
    """
    Extracts text and images from a PDF and stores them in the database
    """

    pdf_path = uploaded_pdf.pdf_file.path
    doc = fitz.open(pdf_path)

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_number = page_index + 1

        # -------------------------------
        # TEXT EXTRACTION
        # -------------------------------
        text = page.get_text("text")

        if text.strip():
            paragraphs = split_into_paragraphs(text)

            for para in paragraphs:
                ExtractedText.objects.create(
                    pdf=uploaded_pdf,
                    page_number=page_number,
                    content=para,
                    is_definition=is_definition_paragraph(para),
                )

        # -------------------------------
        # IMAGE / DIAGRAM EXTRACTION
        # -------------------------------
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            image_name = f"{uploaded_pdf.id}_page{page_number}_{img_index}.{image_ext}"
            image_path = os.path.join(settings.MEDIA_ROOT, "diagrams", image_name)

            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)

            ExtractedDiagram.objects.create(
                pdf=uploaded_pdf,
                page_number=page_number,
                image=f"diagrams/{image_name}",
                caption=None,
            )

    doc.close()


def split_into_paragraphs(text):
    """
    Splits raw text into meaningful paragraphs
    """
    lines = text.split("\n")
    paragraphs = []
    buffer = ""

    for line in lines:
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


def is_definition_paragraph(text):
    """
    Simple heuristic to detect definition paragraphs
    """
    definition_keywords = [
        "is defined as",
        "refers to",
        "is the process of",
        "can be defined as",
        "means",
        "is known as",
    ]

    text_lower = text.lower()
    return any(keyword in text_lower for keyword in definition_keywords)
