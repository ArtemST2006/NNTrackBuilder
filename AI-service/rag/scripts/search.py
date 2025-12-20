import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import chromadb
from sentence_transformers import SentenceTransformer


class BM25Index:
    def __init__(self, documents: Dict[str, str], k1: float = 1.5, b: float = 0.75):
        self.documents = documents
        self.k1 = k1
        self.b = b
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length: float = 0.0
        self.postings: Dict[str, List[Tuple[str, int]]] = {}
        self.doc_freqs: Dict[str, int] = {}
        self.N = len(documents)
        self._build()

    def _build(self) -> None:
        if not self.documents:
            return

        total_length = 0
        postings: Dict[str, List[Tuple[str, int]]] = {}
        doc_freqs: Dict[str, int] = {}

        for doc_id, text in self.documents.items():
            tokens = re.findall(r"[\w-]+", text.lower(), flags=re.UNICODE)
            total_length += len(tokens)
            term_counts: Dict[str, int] = {}
            for tok in tokens:
                term_counts[tok] = term_counts.get(tok, 0) + 1

            self.doc_lengths[doc_id] = len(tokens)

            for term, tf in term_counts.items():
                postings.setdefault(term, []).append((doc_id, tf))
                doc_freqs[term] = doc_freqs.get(term, 0) + 1

        self.postings = postings
        self.doc_freqs = doc_freqs
        self.avg_doc_length = total_length / max(1, self.N)

    def search(
            self, query_tokens: List[str], top_k: int = 20
    ) -> List[Tuple[str, float]]:
        if not query_tokens or not self.postings:
            return []

        scores: Dict[str, float] = {}
        unique_terms = set(query_tokens)

        for term in unique_terms:
            posting = self.postings.get(term)
            if not posting:
                continue

            df = self.doc_freqs.get(term, 0)
            if df == 0:
                continue

            idf = (self.N - df + 0.5) / (df + 0.5)
            if idf <= 0:
                continue

            idf = max(idf, 1e-9)
            for doc_id, tf in posting:
                denom = tf + self.k1 * (
                        1 - self.b + self.b * self.doc_lengths[doc_id] / self.avg_doc_length
                )
                score = (tf * (self.k1 + 1) / denom) * idf
                scores[doc_id] = scores.get(doc_id, 0.0) + score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


MODEL_NAME = "DiTy/bi-encoder-russian-msmarco"
MIN_SCORE_SHORT_QUERY = 0.65
MIN_SCORE_MEDIUM_QUERY = 0.4
MIN_SCORE_LONG_QUERY = 0.45
MAX_DISTANCE_SHORT_QUERY = 0.9
MAX_DISTANCE_MEDIUM_QUERY = 0.95
MAX_DISTANCE_LONG_QUERY = 1.1
LEXICAL_WEIGHT_SHORT_QUERY = 0.6
LEXICAL_WEIGHT_MEDIUM_QUERY = 0.4
LEXICAL_WEIGHT_LONG_QUERY = 0.3
QUERY_STOPWORDS = {
    "и",
    "в",
    "во",
    "на",
    "с",
    "со",
    "для",
    "без",
    "по",
    "про",
    "или",
    "что",
    "это",
    "как",
    "где",
    "рядом",
    "около",
}


class HybridSearcher:

    def __init__(self, db_path: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        try:
            self.collection = self.client.get_collection(name="places")
        except ValueError as e:
            print("Ошибка: ", e)
            exit(1)

        self.model = SentenceTransformer(MODEL_NAME)
        self.doc_store: Dict[str, str] = {}
        self.metadata_store: Dict[str, Dict] = {}
        self._load_corpus()
        self.bm25_index = BM25Index(self.doc_store) if self.doc_store else None

        self.tag_map = {
            "scenic": "живописное",
            "adventure": "приключение",
            "photography": "фотография",
            "outdoor": "на открытом воздухе",
            "relaxation": "отдых",
            "paid_entry": "платный вход",
            "nature": "природа",
            "history": "историческое",
            "family": "для семей",
            "kids": "для детей",
        }

    def parse_tags_from_metadata(self, semantic_tags_str: str) -> List[str]:
        try:
            if isinstance(semantic_tags_str, list):
                return semantic_tags_str
            return json.loads(semantic_tags_str)
        except:
            return []

    def tokenize_query(self, query: str) -> List[str]:
        tokens = re.findall(r"[\w-]+", query.lower(), flags=re.UNICODE)
        return [t for t in tokens if len(t) >= 2 and t not in QUERY_STOPWORDS]

    def _load_corpus(self, batch_size: int = 500) -> None:
        total = self.collection.count()
        offset = 0
        while offset < total:
            batch = self.collection.get(
                include=["documents", "metadatas"],
                limit=batch_size,
                offset=offset,
            )
            ids = batch.get("ids") or []
            docs = batch.get("documents") or []
            metas = batch.get("metadatas") or []
            for doc_id, doc_text, meta in zip(ids, docs, metas):
                self.doc_store[str(doc_id)] = doc_text or ""
                self.metadata_store[str(doc_id)] = meta or {}
            offset += len(ids)
            if len(ids) < batch_size:
                break

    def get_lexical_weight(self, token_count: int) -> float:
        if token_count <= 2:
            return LEXICAL_WEIGHT_SHORT_QUERY
        if token_count <= 4:
            return LEXICAL_WEIGHT_MEDIUM_QUERY
        return LEXICAL_WEIGHT_LONG_QUERY

    def compute_lexical_score(self, result: Dict, tokens: List[str]) -> float:
        if not tokens:
            return 0.0
        meta = result.get("metadata", {})
        fields = [
            result.get("full_text", ""),
            meta.get("name", ""),
            meta.get("search_category", ""),
            meta.get("category", ""),
            meta.get("subcategory", ""),
        ]
        tags = self.parse_tags_from_metadata(meta.get("semantic_tags", "[]"))
        fields.extend(tags)
        haystack = " ".join(str(f).lower() for f in fields if f)
        unique_tokens = set(tokens)
        words = set(re.findall(r"[\w-]+", haystack, flags=re.UNICODE))
        matches = 0
        for token in unique_tokens:
            if token in haystack:
                matches += 1
                continue
            if len(token) >= 5:
                stem = token[:5]
                if any(word.startswith(stem) for word in words):
                    matches += 1
        return matches / len(unique_tokens)

    def get_effective_min_score(self, query: str, min_score: Optional[float]) -> float:
        if min_score is not None:
            return min_score
        tokens = re.findall(r"[\w-]+", query.lower(), flags=re.UNICODE)
        token_count = len(tokens)
        if token_count <= 2:
            return MIN_SCORE_SHORT_QUERY
        if token_count <= 4:
            return MIN_SCORE_MEDIUM_QUERY
        return MIN_SCORE_LONG_QUERY

    def get_effective_max_distance(
            self, query: str, max_distance: Optional[float]
    ) -> float:
        if max_distance is not None:
            return max_distance
        tokens = re.findall(r"[\w-]+", query.lower(), flags=re.UNICODE)
        token_count = len(tokens)
        if token_count <= 2:
            return MAX_DISTANCE_SHORT_QUERY
        if token_count <= 4:
            return MAX_DISTANCE_MEDIUM_QUERY
        return MAX_DISTANCE_LONG_QUERY

    def build_where_filter(
            self,
            search_categories: Optional[List[str]] = None,
            price_ranges: Optional[List[str]] = None,
            seasons: Optional[List[str]] = None,
    ) -> Optional[Dict]:

        filters = []

        def add_in_filter(field: str, values: Optional[List[str]]) -> None:
            if not values:
                return
            cleaned = [v for v in values if v]
            if cleaned:
                filters.append({field: {"$in": cleaned}})

        add_in_filter("search_category", search_categories)
        add_in_filter("price_range", price_ranges)
        add_in_filter("season", seasons)

        if not filters:
            return None

        if len(filters) == 1:
            return filters[0]

        return {"$and": filters}

    def search(
            self,
            query: str,
            n_results: int = 5,
            search_categories: Optional[List[str]] = None,
            price_ranges: Optional[List[str]] = None,
            seasons: Optional[List[str]] = None,
            city: Optional[str] = None,
            min_score: Optional[float] = None,
            max_distance: Optional[float] = None,
    ) -> List[Dict]:

        print(f"Поиск: '{query}'")
        if search_categories:
            print(f"   Категории: {', '.join(search_categories)}")
        if price_ranges:
            print(f"   Цена: {', '.join(price_ranges)}")
        print()

        query_embedding = self.model.encode(query, convert_to_numpy=True).tolist()
        effective_min_score = self.get_effective_min_score(query, min_score)
        effective_max_distance = self.get_effective_max_distance(query, max_distance)
        query_tokens = self.tokenize_query(query)
        lexical_weight = self.get_lexical_weight(len(query_tokens))

        where_filter = self.build_where_filter(
            search_categories=search_categories,
            price_ranges=price_ranges,
            seasons=seasons,
        )

        try:
            raw_results = self.collection.query(
                query_embeddings=[query_embedding],
                where=where_filter,
                n_results=n_results * 3,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            print(f"Ошибка при поиске: {e}")
            return []

        if not raw_results or not raw_results.get("ids"):
            return []

        ids = raw_results["ids"][0]
        docs = raw_results["documents"][0]
        metas = raw_results["metadatas"][0]
        dists = raw_results["distances"][0]

        candidate_map: Dict[str, Dict] = {}

        for doc_id, doc_text, metadata, distance in zip(ids, docs, metas, dists):
            if distance is None or distance > effective_max_distance:
                continue
            base_score = 1.0 / (1.0 + distance)
            final_score = base_score

            if city and metadata.get("city", "").lower() != city.lower():
                continue

            result = {
                "id": doc_id,
                "name": metadata.get("name", "N/A"),
                "text": doc_text[:80],
                "full_text": doc_text,
                "metadata": metadata,
                "distance": distance,
                "base_score": base_score,
                "tags": self.parse_tags_from_metadata(
                    metadata.get("semantic_tags", "[]")
                ),
            }
            candidate_map[str(doc_id)] = result

        bm25_results: List[Tuple[str, float]] = []
        if self.bm25_index:
            bm25_results = self.bm25_index.search(
                query_tokens, top_k=max(n_results * 5, n_results)
            )
            max_bm25 = bm25_results[0][1] if bm25_results else 0.0
            for doc_id, bm25_score in bm25_results:
                norm_bm25 = bm25_score / max_bm25 if max_bm25 > 0 else 0.0
                if doc_id in candidate_map:
                    candidate_map[doc_id]["bm25_score"] = norm_bm25
                else:
                    meta = self.metadata_store.get(doc_id, {})
                    doc_text = self.doc_store.get(doc_id, "")
                    candidate_map[doc_id] = {
                        "id": doc_id,
                        "name": meta.get("name", "N/A"),
                        "text": doc_text[:80],
                        "full_text": doc_text,
                        "metadata": meta,
                        "distance": None,
                        "base_score": 0.0,
                        "bm25_score": norm_bm25,
                        "tags": self.parse_tags_from_metadata(
                            meta.get("semantic_tags", "[]")
                        ),
                    }

        scored_results = []
        for doc_id, result in candidate_map.items():
            base_score = result.get("base_score", 0.0)
            bm25_score = result.get("bm25_score", 0.0)
            lexical_score = self.compute_lexical_score(result, query_tokens)
            final_score = (1.0 - lexical_weight) * base_score + lexical_weight * max(
                bm25_score, lexical_score
            )
            result["final_score"] = final_score
            scored_results.append(result)

        scored_results.sort(key=lambda x: x["final_score"], reverse=True)

        if not scored_results or scored_results[0]["final_score"] < effective_min_score:
            return []

        return scored_results[:n_results]

    def print_results(self, results: List[Dict], show_details: bool = True):
        if not results:
            print("Данных по вашему запросу не найдено.\n")
            return

        print(f"Найдено {len(results)} результатов:\n")

        for i, result in enumerate(results, 1):
            print(f"{i}. !!! {result['name']}")
            print(f"   {result['full_text'][:100]}...")

            if show_details:
                print(
                    f"   Score: {result['final_score']:.3f} | Distance: {result['distance']:.3f}"
                )

                meta = result["metadata"]

                if meta.get("search_category"):
                    print(f"   Category: {meta['search_category']}")

                if result["tags"]:
                    tags_text = ", ".join(
                        [self.tag_map.get(tag, tag) for tag in result["tags"]]
                    )
                    print(f"   Tags: {tags_text}")

                if meta.get("price_range"):
                    print(f"   Price: {meta['price_range']}")

                if meta.get("rating"):
                    print(f"   Rating: {meta['rating']}")

            print()
