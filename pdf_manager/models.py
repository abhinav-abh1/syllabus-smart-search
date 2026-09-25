from django.db import models
from django.contrib.auth.models import User


class UploadedPDF(models.Model):
    """
    Stores uploaded textbook PDF details
    Each PDF belongs to a specific user
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="uploaded_pdfs"
    )
    title = models.CharField(max_length=255)
    pdf_file = models.FileField(upload_to="pdfs/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.user.email})"


class ExtractedText(models.Model):
    """
    Stores extracted text paragraphs from the PDF
    Optimized with hashing to prevent duplicates
    """

    pdf = models.ForeignKey(UploadedPDF, on_delete=models.CASCADE, related_name="texts")
    page_number = models.IntegerField()
    content = models.TextField()

    # ✅ NEW: Detect definitions (existing logic preserved)
    is_definition = models.BooleanField(default=False)

    # ✅ NEW: Prevent duplicate paragraphs
    content_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA256 hash of paragraph content for deduplication",
    )

    def __str__(self):
        return f"{self.pdf.title} - Page {self.page_number}"


class ExtractedDiagram(models.Model):
    """
    Stores extracted diagrams/images related to topics
    Optimized with hashing to prevent duplicates
    """

    pdf = models.ForeignKey(
        UploadedPDF, on_delete=models.CASCADE, related_name="diagrams"
    )
    image = models.ImageField(upload_to="diagrams/")
    page_number = models.IntegerField()
    caption = models.CharField(max_length=255, blank=True, null=True)

    # ✅ NEW: Prevent duplicate images
    image_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="MD5 hash of image bytes for deduplication",
    )

    def __str__(self):
        return f"Diagram - {self.pdf.title} (Page {self.page_number})"
