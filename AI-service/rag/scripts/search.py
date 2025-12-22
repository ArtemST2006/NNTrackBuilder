from typing import Dict, List, Optional, Tuple
import json
import re
import chromadb
import os
from pathlib import Path
import math



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


MODELS_CACHE = str(Path(__file__).parent / ".model_cache")
MODEL_DIR = str(Path(MODELS_CACHE) / "models--DiTy--bi-encoder-russian-msmarco")


os.environ['TRANSFORMERS_CACHE'] = MODELS_CACHE
os.environ['HF_HOME'] = MODELS_CACHE
os.environ['HF_HUB_OFFLINE'] = '1'  # Отключить скачивание с интернета

from sentence_transformers import SentenceTransformer

MODEL_NAME = "DiTy/bi-encoder-russian-msmarco"

MIN_SCORE_SHORT_QUERY = 0.6
MIN_SCORE_MEDIUM_QUERY = 0.35
MIN_SCORE_LONG_QUERY = 0.4
MAX_DISTANCE_SHORT_QUERY = 0.95
MAX_DISTANCE_MEDIUM_QUERY = 1.0
MAX_DISTANCE_LONG_QUERY = 1.15
LEXICAL_WEIGHT_SHORT_QUERY = 0.6
LEXICAL_WEIGHT_MEDIUM_QUERY = 0.4
LEXICAL_WEIGHT_LONG_QUERY = 0.3
GEO_DISTANCE_WEIGHT = 0.1
GEO_DISTANCE_SCALE_KM = 20.0

SERVICE_CENTER_LAT = 56.320409
SERVICE_CENTER_LON = 44.001358

SERVICE_RADIUS_KM = 50.0
RU_SUFFIXES = (
    "иями",
    "ями",
    "ами",
    "ях",
    "ах",
    "ов",
    "ев",
    "ей",
    "ам",
    "ям",
    "ом",
    "ем",
    "ою",
    "ею",
    "ую",
    "юю",
    "ая",
    "яя",
    "ое",
    "ее",
    "ый",
    "ий",
    "ой",
    "ые",
    "ие",
    "ых",
    "их",
    "ым",
    "им",
    "а",
    "я",
    "ы",
    "и",
    "о",
    "е",
    "у",
    "ю",
    "ь",
)
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

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / "chroma_db")
        db_path_value = Path(db_path)
        print(
            f"HybridSearcher: db_path={db_path_value} exists={db_path_value.exists()}"
        )
        self.client = chromadb.PersistentClient(path=db_path)
        try:
            collections = self.client.list_collections()
            collection_names = [c.name for c in collections]
            print(f"HybridSearcher: collections={collection_names}")
        except Exception as e:
            print(f"HybridSearcher: failed to list collections: {e}")
        try:
            self.collection = self.client.get_collection(name="places")
        except ValueError as e:
            try:
                collections = self.client.list_collections()
                collection_names = [c.name for c in collections]
                print(
                    f"HybridSearcher: missing collection 'places'; available={collection_names}"
                )
            except Exception as e2:
                print(f"HybridSearcher: failed to list collections after error: {e2}")
            print("Ошибка!: ", e)
            exit(1)
        try:
            print(f"Loading transformer model: {MODEL_NAME}")
            self.model = SentenceTransformer(MODEL_DIR)
            print("Transformer model loaded.")
        except Exception as e:
            print(f"Failed to load transformer model: {e}")
            raise
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

    def _normalize_token(self, token: str) -> str:
        normalized = token.lower().replace("ё", "е")
        if len(normalized) <= 3:
            return normalized
        for suffix in RU_SUFFIXES:
            if normalized.endswith(suffix):
                stem = normalized[: -len(suffix)]
                if len(stem) >= 3:
                    return stem
        return normalized

    def _parse_coordinate(self, value: Optional[object]) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None
            try:
                return float(cleaned.replace(",", "."))
            except ValueError:
                return None
        return None

    def _get_place_coords(self, metadata: Dict) -> Optional[Tuple[float, float]]:
        lat = self._parse_coordinate(metadata.get("lat"))
        if lat is None:
            lat = self._parse_coordinate(metadata.get("latitude"))

        lon = self._parse_coordinate(metadata.get("lon"))
        if lon is None:
            lon = self._parse_coordinate(metadata.get("lng"))
        if lon is None:
            lon = self._parse_coordinate(metadata.get("longitude"))

        if lat is None or lon is None:
            return None
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return None
        return lat, lon

    def _haversine_km(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        r = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lon2 - lon1)
        a = (
            math.sin(d_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
        )
        return 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

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
        normalized_words = {self._normalize_token(word) for word in words if word}
        prefixes_4 = {word[:4] for word in words if len(word) >= 4}
        prefixes_5 = {word[:5] for word in words if len(word) >= 5}
        normalized_prefixes_4 = {
            word[:4] for word in normalized_words if len(word) >= 4
        }
        normalized_prefixes_5 = {
            word[:5] for word in normalized_words if len(word) >= 5
        }
        matches = 0
        for token in unique_tokens:
            normalized_token = self._normalize_token(token)
            if token in words or normalized_token in normalized_words:
                matches += 1
                continue
            if len(normalized_token) >= 5:
                stem = normalized_token[:5]
                if stem in prefixes_5 or stem in normalized_prefixes_5:
                    matches += 1
                    continue
            if len(normalized_token) >= 4:
                stem = normalized_token[:4]
                if stem in prefixes_4 or stem in normalized_prefixes_4:
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
            user_lat: Optional[float] = None,
            user_lon: Optional[float] = None,
            min_score: Optional[float] = None,
            max_distance: Optional[float] = None,
    ) -> List[Dict]:

        # print(f"Поиск: '{query}'")
        # if search_categories:
        #     print(f"   Категории: {', '.join(search_categories)}")
        # if price_ranges:
        #     print(f"   Цена: {', '.join(price_ranges)}")
        # print()

        query_embedding = self.model.encode(query, convert_to_numpy=True).tolist()
        effective_min_score = self.get_effective_min_score(query, min_score)
        effective_max_distance = self.get_effective_max_distance(query, max_distance)
        query_tokens = self.tokenize_query(query)
        lexical_weight = self.get_lexical_weight(len(query_tokens))
        user_lat_value = self._parse_coordinate(user_lat)
        user_lon_value = self._parse_coordinate(user_lon)
        if (
            user_lat_value is None
            or user_lon_value is None
            or not (-90.0 <= user_lat_value <= 90.0)
            or not (-180.0 <= user_lon_value <= 180.0)
        ):
            user_lat_value = SERVICE_CENTER_LAT
            user_lon_value = SERVICE_CENTER_LON
        user_has_coords = True
        service_distance_km = self._haversine_km(
            user_lat_value, user_lon_value, SERVICE_CENTER_LAT, SERVICE_CENTER_LON
        )
        if service_distance_km > SERVICE_RADIUS_KM:
            return []

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
            main_score = (1.0 - lexical_weight) * base_score + lexical_weight * max(
                bm25_score, lexical_score
            )
            geo_distance_km = None
            geo_score = None
            if user_has_coords:
                coords = self._get_place_coords(result.get("metadata", {}))
                if coords:
                    geo_distance_km = self._haversine_km(
                        user_lat_value, user_lon_value, coords[0], coords[1]
                    )
                    geo_score = 1.0 / (1.0 + geo_distance_km / GEO_DISTANCE_SCALE_KM)

            if geo_score is not None:
                final_score = (1.0 - GEO_DISTANCE_WEIGHT) * main_score + (
                    GEO_DISTANCE_WEIGHT * geo_score
                )
            else:
                final_score = main_score

            result["geo_distance_km"] = geo_distance_km
            result["geo_score"] = geo_score
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
