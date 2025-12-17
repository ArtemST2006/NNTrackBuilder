import json
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from sentence_transformers import SentenceTransformer

MODEL_NAME = "DiTy/bi-encoder-russian-msmarco"


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
        boost_tags: Optional[List[str]] = None,
        price_ranges: Optional[List[str]] = None,
        seasons: Optional[List[str]] = None,
        city: Optional[str] = None,
    ) -> List[Dict]:

        print(f"Поиск: '{query}'")
        if search_categories:
            print(f"   Категории: {', '.join(search_categories)}")
        if boost_tags:
            print(f"   Буст тегов: {', '.join(boost_tags)}")
        if price_ranges:
            print(f"   Цена: {', '.join(price_ranges)}")
        print()

        query_embedding = self.model.encode(query, convert_to_numpy=True).tolist()

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
            print("Результатов не найдено\n")
            return []

        ids = raw_results["ids"][0]
        docs = raw_results["documents"][0]
        metas = raw_results["metadatas"][0]
        dists = raw_results["distances"][0]

        scored_results = []

        for doc_id, doc_text, metadata, distance in zip(ids, docs, metas, dists):
            base_score = 1.0 / (1.0 + distance)
            final_score = base_score

            if boost_tags:
                tags_str = metadata.get("semantic_tags", "[]")
                place_tags = self.parse_tags_from_metadata(tags_str)

                for tag in boost_tags:
                    if tag in place_tags:
                        final_score *= 1.5

            if city and metadata.get("city", "").lower() != city.lower():
                continue

            scored_results.append(
                {
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
            )

        scored_results.sort(key=lambda x: x["final_score"], reverse=True)

        return scored_results[:n_results]

    def print_results(self, results: List[Dict], show_details: bool = True):
        if not results:
            print("Результатов не найдено\n")
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
            "boost_tags": ["природа", "фотосессии", "прогулки"],
        },
        {
            "query": "исторический памятник с архитектурой",
            "search_categories": ["памятник"],
            "boost_tags": ["история", "архитектура"],
        },
        {
            "query": "вкусная выпечка и кофе",
            "search_categories": ["кондитерская"],
            "boost_tags": ["десерты"],
            "price_ranges": ["budget", "moderate"],
        },
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

        boost_input = input("   Буст теги [enter пропустить]: ").strip()
        boost_tags = (
            [t.strip() for t in boost_input.split(",")] if boost_input else None
        )

        price_input = input("   Цена [enter пропустить]: ").strip()
        prices = [p.strip() for p in price_input.split(",")] if price_input else None

        results = searcher.search(
            query=query,
            n_results=5,
            search_categories=categories,
            boost_tags=boost_tags,
            price_ranges=prices,
        )

        searcher.print_results(results)
        print()


if __name__ == "__main__":
    main()
