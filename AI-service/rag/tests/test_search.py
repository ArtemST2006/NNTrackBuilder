import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from scripts.search import HybridSearcher

QUERIES = [
    "парки",
    "вкусно поесть",
    "история",
    "музей",
    "фоырдварфоывадол",
    "йух",
    "запрет",
    "Пушкин",
    "погулять с детьми",
    "фдыыдрва паррк"
]

DB_PATH = ROOT / "chroma_db"
N_RESULTS = 5


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
        results = searcher.search(query, n_results=N_RESULTS)
        if not results:
            print("  (ничего не найдено)")
            continue

        for i, r in enumerate(results, 1):
            name = r.get("name")
            score = r.get("final_score")
            distance = r.get("distance")
            print(f"{i}. {name} | score={score} | distance={distance}")


if __name__ == "__main__":
    main()
