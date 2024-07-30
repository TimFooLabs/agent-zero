from langchain_core.embeddings import Embeddings
import chromadb
from . import files
import uuid
from typing import List, Dict, Any

class VectorDB:
    def __init__(self, embeddings_model: Embeddings, cache_dir: str = "./cache"):
        print("Initializing VectorDB...")
        self.embeddings_model = embeddings_model
        db_cache = files.get_abs_path(cache_dir, "database")
        self.client = chromadb.PersistentClient(path=db_cache)
        self.collection = self.client.get_or_create_collection("my_collection")

    def search(self, query: str, results: int = 2) -> List[Dict[str, Any]]:
        emb = self.embeddings_model.embed_query(query)
        res = self.collection.query(query_embeddings=[emb], n_results=results)
        return [{"id": id, "document": doc, "distance": dist} 
                for id, doc, dist in zip(res["ids"][0], res["documents"][0], res["distances"][0])]

    def delete_documents(self, query: str, score_limit: float = 0.5, batch_size: int = 10) -> int:
        total_deleted = 0
        while True:
            results = self.search(query, results=batch_size)
            ids_to_delete = [result["id"] for result in results if result["distance"] < score_limit]
            
            if not ids_to_delete:
                break
            
            self.collection.delete(ids=ids_to_delete)
            total_deleted += len(ids_to_delete)
            
            if len(ids_to_delete) < batch_size:
                break
        
        return total_deleted

    def insert(self, data: List[str]) -> List[str]:
        ids = [str(uuid.uuid4()) for _ in data]
        embeddings = self.embeddings_model.embed_documents(data)
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=data,
        )
        
        return ids

