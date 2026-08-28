import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class KBSearchIndex:
    """In-memory singleton index for knowledge-base documentation chunks and TF-IDF search."""

    _instance: Optional["KBSearchIndex"] = None

    def __init__(self, kb_dir: Optional[Path] = None):
        if kb_dir is None:
            # Default to <repo_root>/knowledge-base
            self.kb_dir = Path(__file__).resolve().parent.parent.parent / "knowledge-base"
        else:
            self.kb_dir = kb_dir

        self.chunks: List[Dict[str, str]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix: Optional[Any] = None
        self._load_and_index()

    @classmethod
    def get_instance(cls) -> "KBSearchIndex":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_and_index(self) -> None:
        """Loads all .md files, chunks them by '---' boundaries, and fits TF-IDF matrix."""
        chunks: List[Dict[str, str]] = []
        if not self.kb_dir.exists():
            self.chunks = []
            return

        for md_file in sorted(self.kb_dir.rglob("*.md")):
            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue

            rel_path = str(md_file.relative_to(self.kb_dir.parent))
            raw_sections = re.split(r"(?m)^---+\s*$", content)

            current_h1 = ""
            current_h2 = ""
            current_h3 = ""

            for section in raw_sections:
                lines = section.strip().split("\n")
                for line in lines:
                    line_str = line.strip()
                    if line_str.startswith("# "):
                        current_h1 = line_str[2:].strip()
                        current_h2 = ""
                        current_h3 = ""
                    elif line_str.startswith("## "):
                        current_h2 = line_str[3:].strip()
                        current_h3 = ""
                    elif line_str.startswith("### "):
                        current_h3 = line_str[4:].strip()

                heading_parts = [h for h in [current_h1, current_h2, current_h3] if h]
                heading = " > ".join(heading_parts) if heading_parts else md_file.stem
                clean_text = section.strip()

                if clean_text:
                    chunks.append(
                        {
                            "doc_path": rel_path,
                            "heading": heading,
                            "text": clean_text,
                        }
                    )

        self.chunks = chunks
        if chunks:
            corpus = [f"{c['heading']}\n{c['text']}" for c in chunks]
            self.vectorizer = TfidfVectorizer(stop_words="english")
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search knowledge base chunks matching the query string."""
        if not self.chunks or self.vectorizer is None or self.tfidf_matrix is None:
            return []

        clean_query = query.strip()
        if not clean_query:
            return self.chunks[:top_k]

        query_vec = self.vectorizer.transform([clean_query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        top_indices = similarities.argsort()[::-1][:top_k]
        results: List[Dict[str, Any]] = []
        for idx in top_indices:
            score = float(similarities[idx])
            chunk = self.chunks[idx].copy()
            chunk["score"] = score
            results.append(chunk)

        return results


def search_kb(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Retrieve top_k knowledge base chunks relevant to query."""
    index = KBSearchIndex.get_instance()
    return index.search(query=query, top_k=top_k)
