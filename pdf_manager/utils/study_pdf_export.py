import os
from io import BytesIO

from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as RLImage,
    PageBreak,
)

from django.conf import settings


def generate_study_material_pdf(topic, study_text, diagrams=None):
    """
    Generates an AI Study Material PDF with embedded textbook diagrams.
    - Safe in-memory image handling
    - Transparency flattened on white
    - No temp files
    - No black images
    - No PDF corruption
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    story = []

    # --------------------------------------------------
    # TITLE
    # --------------------------------------------------
    story.append(Paragraph(f"<b>{topic} – AI Study Material</b>", styles["Title"]))
    story.append(Spacer(1, 0.3 * inch))

    # --------------------------------------------------
    # STUDY CONTENT
    # --------------------------------------------------
    for block in study_text.split("\n\n"):
        story.append(Paragraph(block.replace("\n", "<br/>"), styles["BodyText"]))
        story.append(Spacer(1, 0.2 * inch))

    # --------------------------------------------------
    # DIAGRAMS SECTION (FINAL FIX)
    # --------------------------------------------------
    if diagrams:
        story.append(PageBreak())
        story.append(Paragraph("<b>Related Diagrams</b>", styles["Heading2"]))
        story.append(Spacer(1, 0.25 * inch))

        for idx, diagram in enumerate(diagrams, start=1):
            image_path = os.path.join(settings.MEDIA_ROOT, diagram.image.name)

            if not os.path.exists(image_path):
                continue

            with PILImage.open(image_path) as img:

                # 🔥 CRITICAL FIX: flatten transparency on white
                if img.mode in ("RGBA", "LA") or (
                    img.mode == "P" and "transparency" in img.info
                ):
                    background = PILImage.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                else:
                    img = img.convert("RGB")

                img_buffer = BytesIO()
                img.save(img_buffer, format="JPEG", quality=90)
                img_buffer.seek(0)

                rl_img = RLImage(
                    img_buffer,
                    width=4 * inch,
                    height=3 * inch,
                )

            story.append(rl_img)
            story.append(Spacer(1, 0.15 * inch))
            story.append(Paragraph(f"Figure {idx}: Related diagram", styles["Italic"]))
            story.append(Spacer(1, 0.35 * inch))

    # --------------------------------------------------
    # BUILD PDF
    # --------------------------------------------------
    doc.build(story)
    buffer.seek(0)
    return buffer
