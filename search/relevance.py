import pickle
import numpy as np
import os
import re
import logging

from sklearn.metrics.pairwise import cosine_similarity
from django.core.cache import cache

from pdf_manager.models import ExtractedText, ExtractedDiagram
from pdf_manager.embedding_utils import store_text_embeddings

from .semantic_utils import embed_text
from .ai_reference import generate_reference_definition

logger = logging.getLogger(__name__)


# ==================================================
# AI Reference Definition (CACHED + SAFE)
# ==================================================
def get_reference_definition(topic: str) -> str | None:
    """
    Generate (or retrieve from cache) a short reference definition.
    Returns None if generation fails so the caller can handle it gracefully.
    """
    if not topic or not topic.strip():
        return None

    cache_key = f"ref_def_{topic.lower().strip()}"
    cached = cache.get(cache_key)

    # Only return cached value if it is a non-empty string
    if isinstance(cached, str) and cached.strip():
        return cached

    try:
        definition = generate_reference_definition(topic)

        # Validate the response
        if not definition or not isinstance(definition, str) or not definition.strip():
            logger.warning(f"Gemini returned empty/invalid definition for topic: {topic}")
            return None

        # Cache only valid definitions
        cache.set(cache_key, definition.strip(), timeout=60 * 60 * 24)  # 24 hours
        return definition.strip()

    except Exception as e:
        logger.error(f"Failed to generate reference definition for '{topic}': {e}")
        return None


# ==================================================
# Noise / TOC / Heading Detection
# ==================================================
def is_noise_text(text: str) -> bool:
    """Filter out table of contents, chapter headings, page numbers, etc."""
    if not text:
        return True

    text = text.lower().strip()

    # Too short to be a real definition
    if len(text.split()) < 8:
        return True

    patterns = [
        r"^chapter\s+\d+",
        r"^unit\s+\d+",
        r"^section\s+\d+",
        r"^contents?$",
        r"^summary$",
        r"^objectives?$",
        r"^introduction$",
        r"^\d+[\.\-—]\s",           # numbered list
        r"^page\s+\d+",
        r"^figure\s+\d+",
        r"^table\s+\d+",
        r"^exercise",
        r"^questions?",
    ]
    return any(re.match(p, text) for p in patterns)


# ==================================================
# Definition-Style Heuristic Scoring
# ==================================================
def definition_style_score(content: str, topic: str) -> float:
    score = 0.0
    text = content.lower().strip()
    topic = topic.lower().strip()

    # Topic appears at the beginning → strong definition signal
    if text.startswith(topic) or text.startswith(f"the {topic}"):
        score += 0.25

    strong_defs = [
        "is defined as",
        "can be defined as",
        "is defined to be",
        "refers to",
        "is known as",
        "means",
        "is a",
        "is an",
    ]
    if any(phrase in text for phrase in strong_defs):
        score += 0.30

    # Mild boost for shorter, denser paragraphs
    word_count = len(text.split())
    if 15 <= word_count <= 120:
        score += 0.10
    elif word_count > 180:
        score -= 0.15

    # Penalize procedural / implementation language
    if any(w in text for w in ["implementation", "procedure", "steps", "algorithm", "pseudocode"]):
        score -= 0.20

    return score


# ==================================================
# Heading-Aware Proximity Bonus
# ==================================================
def heading_proximity_bonus(text_obj, all_texts, topic: str) -> float:
    topic = topic.lower()
    page = text_obj.page_number

    # Look for headings on the same page that contain the topic
    for t in all_texts:
        if t.page_number != page:
            continue
        content = t.content.strip()
        # Simple heading detection: mostly uppercase or short + topic present
        if (content.isupper() or len(content.split()) <= 8) and topic in content.lower():
            return 0.15

    return 0.0


# ==================================================
# MAIN SEMANTIC RETRIEVAL LOGIC
# ==================================================
def find_relevant_content(pdf, topic_name: str):
    """
    Hybrid semantic retrieval:
    - Cached AI reference definition (safe)
    - Semantic similarity
    - Definition-style heuristics
    - Noise filtering
    - Definition priority boost
    - Page clustering
    - Confidence threshold
    """

    topic_name = (topic_name or "").strip()
    if not topic_name:
        return None

    # 1️⃣ Generate AI reference definition (SAFE)
    reference_definition = get_reference_definition(topic_name)

    if not reference_definition:
        logger.warning(f"No reference definition available for topic: {topic_name}")
        return None

    # 2️⃣ Embed reference definition
    try:
        reference_vector = embed_text(reference_definition).reshape(1, -1)
    except Exception as e:
        logger.error(f"Embedding failed for reference definition: {e}")
        return None

    # 3️⃣ Load / generate textbook embeddings
    embedding_file = f"media/embeddings/pdf_{pdf.id}.pkl"

    try:
        if not os.path.exists(embedding_file):
            logger.info(f"Embeddings missing for PDF {pdf.id}. Generating now...")
            store_text_embeddings(pdf)

        with open(embedding_file, "rb") as f:
            data = pickle.load(f)

        vectors = np.array(data["vectors"])
        meta = data["meta"]

        if len(vectors) == 0 or len(meta) == 0:
            logger.warning(f"Empty embeddings for PDF {pdf.id}")
            return None

    except Exception as e:
        logger.error(f"Failed to load embeddings for PDF {pdf.id}: {e}")
        return None

    # 4️⃣ Compute semantic similarity
    try:
        similarities = cosine_similarity(reference_vector, vectors)[0]
    except Exception as e:
        logger.error(f"Cosine similarity failed: {e}")
        return None

    # Fetch all text once
    all_texts = list(ExtractedText.objects.filter(pdf=pdf))
    text_lookup = {t.id: t for t in all_texts}

    # 5️⃣ Hybrid scoring
    scored = []

    for sim, meta_item in zip(similarities, meta):
        text_obj = text_lookup.get(meta_item["id"])
        if not text_obj:
            continue

        # Skip noise / TOC / very short text
        if is_noise_text(text_obj.content):
            continue

        style_bonus = definition_style_score(text_obj.content, topic_name)
        heading_bonus = heading_proximity_bonus(text_obj, all_texts, topic_name)

        final_score = float(sim) + style_bonus + heading_bonus

        # Strong priority for paragraphs already marked as definitions
        if getattr(text_obj, "is_definition", False):
            final_score += 0.35

        scored.append((final_score, text_obj))

    if not scored:
        return None

    # 6️⃣ Rank results
    scored.sort(key=lambda x: x[0], reverse=True)

    best_score, best_text = scored[0]

    # Clamp confidence between 0 and 100
    confidence = round(max(0.0, min(best_score, 1.0)) * 100, 2)

    # 7️⃣ Confidence threshold
    if confidence < 60:          # slightly lowered for better recall
        return None

    # 8️⃣ Page clustering (definition context)
    definition_page = best_text.page_number
    allowed_pages = {definition_page - 1, definition_page, definition_page + 1}

    explanations = [
        t for score, t in scored[1:]
        if t.page_number in allowed_pages and t.id != best_text.id
    ][:3]

    # 9️⃣ Diagrams from nearby pages
    diagrams = ExtractedDiagram.objects.filter(
        pdf=pdf,
        page_number__in=allowed_pages
    )

    explanation_reason = (
        "Selected using semantic similarity against an AI-generated reference "
        "definition, combined with definition-style linguistic patterns, "
        "heading proximity, definition priority boosting, noise filtering, "
        "and contextual page clustering."
    )

    return {
        "definition": best_text,
        "confidence": confidence,
        "reason": explanation_reason,
        "explanations": explanations,
        "diagrams": diagrams,
    }