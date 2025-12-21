import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from pdf_manager.models import ExtractedText, ExtractedDiagram
from .semantic_utils import embed_text
from .ai_reference import generate_reference_definition
import os
from pdf_manager.embedding_utils import store_text_embeddings


# --------------------------------------------------
# Definition-style heuristic scoring
# --------------------------------------------------
def definition_style_score(content, topic):
    score = 0
    text = content.lower()
    topic = topic.lower()

    # Topic appears early → definition-like
    if topic in text[:120]:
        score += 0.15

    # Common definition phrases
    definition_phrases = [
        "is defined as",
        "refers to",
        "can be defined as",
        "is a ",
        "is an ",
    ]
    if any(p in text for p in definition_phrases):
        score += 0.20

    # Penalize lists / bullets
    if text.count("•") > 2 or text.count("-") > 4:
        score -= 0.15

    # Penalize very long paragraphs
    if len(text.split()) > 220:
        score -= 0.10

    return score


# --------------------------------------------------
# Heading-aware proximity boost (SAFE)
# --------------------------------------------------
def heading_proximity_bonus(text_obj, all_texts, topic):
    """
    Soft boost if paragraph is near a heading-like line
    """
    bonus = 0
    topic = topic.lower()

    # Identify heading-like paragraphs on same page
    headings = [
        t
        for t in all_texts
        if t.page_number == text_obj.page_number
        and len(t.content.split()) <= 10
        and topic in t.content.lower()
    ]

    # If any heading exists on the page → boost nearby paragraphs
    if headings:
        bonus += 0.15

    return bonus


# --------------------------------------------------
# Main semantic search logic
# --------------------------------------------------
def find_relevant_content(pdf, topic_name):
    """
    Hybrid Semantic Retrieval with:
    - AI reference definition
    - Semantic similarity
    - Definition-style heuristics
    - Heading-aware proximity boost
    - Page clustering
    - Confidence threshold
    """

    # 1️⃣ Generate AI reference definition (hidden)
    reference_definition = generate_reference_definition(topic_name)

    # 2️⃣ Embed reference definition
    reference_vector = embed_text(reference_definition).reshape(1, -1)

    # 3️⃣ Load stored textbook embeddings
    embedding_file = f"media/embeddings/pdf_{pdf.id}.pkl"

    # 🛡 Safety check
    if not os.path.exists(embedding_file):
        print(f"[INFO] Embeddings missing for PDF {pdf.id}. Generating now...")
        store_text_embeddings(pdf)

    # Now load embeddings safely
    with open(embedding_file, "rb") as f:
        data = pickle.load(f)

    with open(embedding_file, "rb") as f:
        data = pickle.load(f)

    vectors = np.array(data["vectors"])
    meta = data["meta"]

    # 4️⃣ Compute semantic similarity
    similarities = cosine_similarity(reference_vector, vectors)[0]

    # Fetch all extracted text once (performance-safe)
    all_texts = list(ExtractedText.objects.filter(pdf=pdf))

    # 5️⃣ Hybrid scoring
    scored = []
    for sim, meta_item in zip(similarities, meta):
        text_obj = next(t for t in all_texts if t.id == meta_item["id"])

        style_bonus = definition_style_score(text_obj.content, topic_name)
        heading_bonus = heading_proximity_bonus(text_obj, all_texts, topic_name)

        final_score = sim + style_bonus + heading_bonus
        scored.append((final_score, text_obj))

    # 6️⃣ Rank by final score
    scored.sort(key=lambda x: x[0], reverse=True)

    best_score, best_text = scored[0]
    confidence = round(best_score * 100, 2)

    # 7️⃣ Confidence threshold (quality control)
    if confidence < 65:
        return None

    # 8️⃣ Page clustering (definition section)
    definition_page = best_text.page_number
    allowed_pages = {definition_page, definition_page - 1, definition_page + 1}

    explanations = [
        t
        for _, t in scored[1:]
        if t.page_number in allowed_pages and t.id != best_text.id
    ][:3]

    # 9️⃣ Diagram relevance filtering
    diagrams = ExtractedDiagram.objects.filter(pdf=pdf, page_number__in=allowed_pages)

    # 🔍 Explainability message
    explanation_reason = (
        "Selected using semantic similarity with an AI-generated reference "
        "definition, definition-style linguistic patterns, heading proximity, "
        "and contextual page filtering."
    )

    return {
        "definition": best_text,
        "confidence": confidence,
        "reason": explanation_reason,
        "explanations": explanations,
        "diagrams": diagrams,
    }
