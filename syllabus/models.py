from django.db import models


class SyllabusTopic(models.Model):
    """
    Stores syllabus topics for matching with textbook content
    """

    name = models.CharField(max_length=255, unique=True)
    keywords = models.TextField(
        help_text="Comma-separated keywords related to the topic"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
