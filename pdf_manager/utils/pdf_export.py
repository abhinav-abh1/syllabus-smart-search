from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from io import BytesIO


def generate_search_result_pdf(topic, explanation, contents):
    """
    Generates a downloadable PDF for search results
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

    # Title
    story.append(Paragraph(f"<b>{topic}</b>", styles["Title"]))
    story.append(Spacer(1, 0.3 * inch))

    # AI Explanation
    story.append(Paragraph("<b>AI Explanation</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(explanation, styles["BodyText"]))
    story.append(Spacer(1, 0.3 * inch))

    # Extracted Content
    story.append(Paragraph("<b>Textbook References</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.2 * inch))

    for item in contents:
        text = f"Page {item.page_number}: {item.content}"
        story.append(Paragraph(text, styles["BodyText"]))
        story.append(Spacer(1, 0.15 * inch))

    doc.build(story)
    buffer.seek(0)
    return buffer
