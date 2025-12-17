import json
from pathlib import Path
import numpy as np
import traceback
import time
from typing import List, Dict
from sentence_transformers import SentenceTransformer


MODEL_NAME = "DiTy/bi-encoder-russian-msmarco"
BATCH_SIZE = 32

def load_places_data(data_file: str) -> List[Dict]:

    print(f"Загрузка {data_file}")
    
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Загружено {len(data)} мест")
        return data
    
    except FileNotFoundError:
        print(f"Ошибка: файл {data_file} не найден")
        exit(1)
    except json.JSONDecodeError:
        print(f"Ошибка: некорректный JSON в {data_file}")
        exit(1)

def prepare_embedding_text(place: Dict) -> str:
    text = place.get("search_text")
    
    if place.get("semantic_tags"):
        tags = ", ".join(place["semantic_tags"])
        text += f". Теги: {tags}"
        
    return text

def create_embeddings(places: List[Dict], model_name: str = MODEL_NAME) -> np.ndarray:
    print(f"\nЗагрузка {model_name}")
    
    try:
        model = SentenceTransformer(model_name)
    
    except Exception as e:
        print(f"Ошибка при загрузке модели: {e}")
        exit(1)
    
    texts = []
    for place in places:
        text = prepare_embedding_text(place)
        texts.append(text)  
    
    print(f"\n Мест: {len(texts)}")
    
    try:
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=True,
            batch_size=BATCH_SIZE,
        )
        return embeddings
    
    except Exception as e:
        print(f"Ошибка при создании эмбеддингов: {e}")
        exit(1)


def save_embeddings(embeddings: np.ndarray, output_file: str) -> None:
    try:
        np.save(output_file, embeddings)
    
    except Exception as e:
        print(f"Ошибка при сохранении: {e}")
        exit(1)

def main():
    
    script_dir = Path(__file__).parent.parent
     
    DATA_FILE = script_dir / 'data' / 'processed' / 'places_with_updated_search_text.json'
    EMBEDDINGS_FILE = script_dir / 'data' / 'embeddings' / 'place_embeddings.npy'

    places = load_places_data(str(DATA_FILE))
    embeddings = create_embeddings(places)
    
    save_embeddings(embeddings, str(EMBEDDINGS_FILE))
    
    print(f"\nЭмбеддинги созданы")
    print(f"Количество: {len(places)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nНеожиданная ошибка: {e}")
        traceback.print_exc()
        exit(1)
