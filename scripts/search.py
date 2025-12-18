import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from sentence_transformers import SentenceTransformer

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
        effective_max_distance = self.get_effective_max_distance(
            query, max_distance
        )

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

        scored_results = []
        query_tokens = self.tokenize_query(query)
        lexical_weight = self.get_lexical_weight(len(query_tokens))

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
                "final_score": final_score,
                "tags": self.parse_tags_from_metadata(
                    metadata.get("semantic_tags", "[]")
                ),
            }
            lexical_score = self.compute_lexical_score(result, query_tokens)
            final_score = (1.0 - lexical_weight) * base_score + (
                lexical_weight * lexical_score
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


def main():
    script_dir = Path(__file__).parent.parent
    db_path = str(script_dir / "chroma_db")

    searcher = HybridSearcher(db_path=db_path)

    examples = [
        {
            "query": "красивый парк для прогулки и фото",
            "search_categories": ["парк"],
        },
        {
            "query": "исторический памятник с архитектурой",
            "search_categories": ["памятник"],
        },
        {
            "query": "вкусная выпечка с кофе",
        },
        {
            "query": "ыврпоыварпыдл",
        },
        {
            "query": "йух",
        },
        {
            "query": "запрещенка",
        }
    ]
    for i, example in enumerate(examples, 1):
        results = searcher.search(**example)
        searcher.print_results(results)

    while True:
        query = input("Введи запрос. ").strip()
        if not query or query.lower() == "exit":
            break

        categories_input = input("   Категории [enter пропустить]: ").strip()
        categories = (
            [c.strip() for c in categories_input.split(",")]
            if categories_input
            else None
        )

        price_input = input("   Цена [enter пропустить]: ").strip()
        prices = [p.strip() for p in price_input.split(",")] if price_input else None

        results = searcher.search(
            query=query,
            n_results=5,
            search_categories=categories,
            price_ranges=prices,
        )

        searcher.print_results(results)
        print()


if __name__ == "__main__":
    main()
