from sentence_transformers import SentenceTransformer

# Lightweight & accurate model
model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_text(text):
    """
    Converts text into a semantic vector
    """
    return model.encode(text)
