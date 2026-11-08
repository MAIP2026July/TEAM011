"""RAG layer: the compliance rulebook, embedded and searched through ChromaDB."""
import json
from typing import Callable, Dict, List, Optional

import chromadb

from .config import CHROMA_DIR, RETRIEVAL_TOP_K, RULEBOOK_PATH

EmbedFn = Callable[[List[str]], List[List[float]]]


def load_rules() -> Dict[str, dict]:
    with open(RULEBOOK_PATH, encoding="utf-8") as handle:
        return {rule["id"]: rule for rule in json.load(handle)["rules"]}


def rulebook_version() -> str:
    with open(RULEBOOK_PATH, encoding="utf-8") as handle:
        return json.load(handle)["version"]


class RulebookStore:
    def __init__(self, embed_fn: EmbedFn, index_name: str, path: Optional[str] = None):
        self.embed_fn = embed_fn
        self.rules = load_rules()
        client = chromadb.PersistentClient(path=str(path or CHROMA_DIR))
        name = f"rules-{rulebook_version()}-{index_name}".replace(".", "-")
        self.collection = client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
        if self.collection.count() != len(self.rules):
            self._build()

    def _build(self) -> None:
        ids = list(self.rules)
        documents = [self.rules[i]["text"] for i in ids]
        metadatas = [{"category": self.rules[i]["category"], "severity": self.rules[i]["severity"]} for i in ids]
        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=self.embed_fn(documents))

    def retrieve(self, query: str, top_k: int = RETRIEVAL_TOP_K) -> List[dict]:
        """Returns the top_k rules for a query, closest first, with their distance."""
        result = self.collection.query(query_embeddings=self.embed_fn([query]), n_results=top_k)
        return [
            {**self.rules[rule_id], "distance": round(distance, 4)}
            for rule_id, distance in zip(result["ids"][0], result["distances"][0])
        ]
