from search.semantic_utils import embed_text
from .models import ExtractedText
import pickle
import os


def store_text_embeddings(pdf):
    """
    Generates and stores semantic embeddings for extracted textbook text
    """
    texts = ExtractedText.objects.filter(pdf=pdf)

    embeddings = []
    meta = []

    for text in texts:
        vector = embed_text(text.content)
        embeddings.append(vector)
        meta.append({"id": text.id, "page": text.page_number})

    os.makedirs("media/embeddings", exist_ok=True)

    with open(f"media/embeddings/pdf_{pdf.id}.pkl", "wb") as f:
        pickle.dump({"vectors": embeddings, "meta": meta}, f)
