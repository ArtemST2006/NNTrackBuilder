import json
import traceback
from pathlib import Path
from typing import Dict, List

import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "DiTy/bi-encoder-russian-msmarco"


def load_places_data(data_file: str) -> List[Dict]:
    print(f"Загрузка данных из {data_file}")

    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Загружено {len(data)} мест\n")
        return data

    except FileNotFoundError:
        print(f"Ошибка: файл {data_file} не найден")
        exit(1)
    except json.JSONDecodeError:
        print(f"Ошибка: некорректный JSON в {data_file}")
        exit(1)


def load_embeddings(embeddings_file: str) -> np.ndarray:
    print(f"Загрузка эмбеддингов из {embeddings_file}")

    try:
        embeddings = np.load(embeddings_file)
        print(f"Загружено {len(embeddings)} эмбеддингов")
        print(f"Размерность вектора: {embeddings.shape}\n")
        return embeddings

    except FileNotFoundError:
        print(f"Ошибка: файл {embeddings_file} не найден")
        exit(1)
    except Exception as e:
        print(f"Ошибка при загрузке эмбеддингов: {e}")
        exit(1)


def create_vectordb(places: List[Dict], embeddings: np.ndarray, db_path: str) -> None:
    db_dir = Path(db_path)
    db_dir.mkdir(parents=True, exist_ok=True)

    try:
        client = chromadb.PersistentClient(path=str(db_path))

        try:
            client.delete_collection(name="places")
        except:
            pass

        collection = client.create_collection(
            name="places", metadata={"hnsw:space": "cosine"}
        )

        ids = []
        metadatas = []
        documents = []
        vectors = []

        for idx, place in enumerate(places):
            place_id = str(idx)
            ids.append(place_id)

            metadata = {
                "name": place.get("name", ""),
                "search_category": place.get("search_category", ""),
                "category": place.get("category", ""),
                "subcategory": place.get("subcategory", ""),
                "lat": str(place.get("lat", "")),
                "lon": str(place.get("lon", "")),
                "semantic_tags": json.dumps(place.get("semantic_tags", [])),
                "price_range": place.get("metadata", {}).get("price_range", ""),
                "rating_category": place.get("metadata", {}).get("rating_category", ""),
                "season": place.get("metadata", {}).get("season", ""),
                "accessibility": place.get("metadata", {}).get("accessibility", ""),
                "rating": str(place.get("rating", "")),
                "city": place.get("city", ""),
            }
            metadatas.append(metadata)

            document = place.get("search_text", "")
            documents.append(document)

            vector = embeddings[idx].tolist()
            vectors.append(vector)

            if (idx + 1) % 500 == 0:
                print(f"  Подготовлено {idx + 1}/{len(places)} мест")

        collection.upsert(
            ids=ids, metadatas=metadatas, documents=documents, embeddings=vectors
        )

        print(f"Данные загружены\n")
    except Exception as e:
        print(f"Ошибка при создании БД: {e}")
        exit(1)


def main():
    script_dir = Path(__file__).parent.parent

    DATA_FILE = (
        script_dir / "data" / "processed" / "places_with_updated_search_text.json"
    )
    EMBEDDINGS_FILE = script_dir / "data" / "embeddings" / "place_embeddings.npy"
    DB_PATH = script_dir / "chroma_db"

    if not DATA_FILE.exists():
        print(f"Ошибка: файл не найден: {DATA_FILE}")
        exit(1)

    if not EMBEDDINGS_FILE.exists():
        print(f"Ошибка: файл не найден: {EMBEDDINGS_FILE}")
        exit(1)

    places = load_places_data(str(DATA_FILE))
    embeddings = load_embeddings(str(EMBEDDINGS_FILE))

    if len(places) != len(embeddings):
        print(
            f"Ошибка: количество мест ({len(places)}) != количество эмбеддингов ({len(embeddings)})"
        )
        exit(1)

    print(f"Данные совпадают: {len(places)} мест = {len(embeddings)} эмбеддингов\n")

    create_vectordb(places, embeddings, str(DB_PATH))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nНеожиданная ошибка: {e}")
        traceback.print_exc()
        exit(1)
