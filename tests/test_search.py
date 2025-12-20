import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from scripts.search import HybridSearcher

QUERIES = [
    "парк",
    "вкусно поесть",
    "история",
    "музей",
    "фоырдварфоывадол",
    "йух",
    "запрет",
    "Пушкин",
    "погулять с детьми",
    "фдыыдрва паррк",
    "все",
]

DB_PATH = ROOT / "chroma_db"
N_RESULTS = 5
USER_LAT = 56.321272
USER_LON = 44.001221


def main() -> None:
    if not DB_PATH.exists():
        print(f"chroma_db не найден по пути: {DB_PATH}")
        return

    try:
        searcher = HybridSearcher(db_path=str(DB_PATH))
    except Exception as e:
        print(f"Ошибка инициализации поиска: {e}")
        return

    for query in QUERIES:
        print(f"\n==== {query} ====")
        results = searcher.search(
            query,
            n_results=N_RESULTS,
            user_lat=USER_LAT,
            user_lon=USER_LON,
        )
        if not results:
            print("  (ничего не найдено)")
            continue

        for i, r in enumerate(results, 1):
            name = r.get("name")
            score = r.get("final_score")
            meta = r.get("metadata") or {}
            lat = r.get("lat", meta.get("lat", "N/A"))
            lon = r.get("lon", meta.get("lon", "N/A"))
            distance = r.get("distance")
            geo_km = r.get("geo_distance_km", "N/A")
            geo_score = r.get("geo_score", "N/A")
            print(
                f"{i}. {name} | score={score} | distance={distance} | "
                f"geo_km={geo_km} | geo_score={geo_score} | lat/lon={lat},{lon}"
            )


if __name__ == "__main__":
    main()
