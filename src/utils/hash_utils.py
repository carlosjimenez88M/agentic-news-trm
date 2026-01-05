"""Hashing utilities for content deduplication."""

import hashlib
from typing import List
from difflib import SequenceMatcher


def hash_content(content: str) -> str:
    """Generate SHA256 hash of content.

    Args:
        content: Content to hash

    Returns:
        Hex digest of hash
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, strip whitespace).

    Args:
        text: Text to normalize

    Returns:
        Normalized text
    """
    return text.lower().strip()


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts using SequenceMatcher.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity ratio between 0.0 and 1.0
    """
    normalized1 = normalize_text(text1)
    normalized2 = normalize_text(text2)
    return SequenceMatcher(None, normalized1, normalized2).ratio()


def is_duplicate(
    text: str,
    existing_texts: List[str],
    threshold: float = 0.9
) -> tuple[bool, float]:
    """Check if text is a duplicate of any existing texts.

    Args:
        text: Text to check
        existing_texts: List of existing texts to compare against
        threshold: Similarity threshold (0.0-1.0) to consider duplicate

    Returns:
        Tuple of (is_duplicate, max_similarity)
    """
    max_similarity = 0.0

    for existing_text in existing_texts:
        similarity = calculate_similarity(text, existing_text)
        max_similarity = max(max_similarity, similarity)

        if similarity >= threshold:
            return True, similarity

    return False, max_similarity


def remove_stopwords(text: str, stopwords: set) -> str:
    """Remove stopwords from text.

    Args:
        text: Text to process
        stopwords: Set of stopwords to remove

    Returns:
        Text without stopwords
    """
    words = text.lower().split()
    filtered_words = [word for word in words if word not in stopwords]
    return ' '.join(filtered_words)
