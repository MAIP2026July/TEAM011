"""The only module that talks to Gemini. Tests replace it with a fake."""
import json
import os
import tempfile
from pathlib import Path
from typing import List, Optional, Type

from google import genai
from google.genai import types
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import GEMINI_EMBED_MODEL, GEMINI_MODEL


def flat_schema(schema: Type[BaseModel]) -> dict:
    """SDK 0.6 rejects $ref, so nested models are written out in full."""
    full = schema.model_json_schema()
    definitions = full.get("$defs", {})

    def resolve(node):
        if isinstance(node, list):
            return [resolve(item) for item in node]
        if not isinstance(node, dict):
            return node
        if "$ref" in node:
            merged = {**definitions[node["$ref"].rsplit("/", 1)[-1]], **{k: v for k, v in node.items() if k != "$ref"}}
            return resolve(merged)
        return {key: resolve(value) for key, value in node.items() if key not in ("$defs", "title")}

    return resolve(full)


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: str = GEMINI_MODEL, embed_model: str = GEMINI_EMBED_MODEL):
        self.client = genai.Client(api_key=api_key or os.environ["GEMINI_API_KEY"])
        self.model = model
        self.embed_model = embed_model

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=2, max=30), reraise=True)
    def _generate(self, contents: list, schema: Optional[Type[BaseModel]]):
        config = types.GenerateContentConfig(temperature=0.1)
        if schema:
            config.response_mime_type = "application/json"
            config.response_schema = flat_schema(schema)
        return self.client.models.generate_content(model=self.model, contents=contents, config=config)

    def generate_json(self, prompt: str, schema: Type[BaseModel]) -> dict:
        return schema.model_validate(json.loads(self._generate([prompt], schema).text)).model_dump()

    def generate_text(self, prompt: str) -> str:
        return self._generate([prompt], None).text

    def analyse_file(self, file_bytes: bytes, filename: str, mime_type: str, prompt: str, schema: Type[BaseModel]) -> dict:
        """The upload is deleted from Gemini and from disk even if analysis fails."""
        uploaded = None
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / f"document{Path(filename).suffix}"
            tmp_path.write_bytes(file_bytes)
            try:
                uploaded = self.client.files.upload(path=str(tmp_path), config={"mime_type": mime_type})
                response = self._generate([uploaded, prompt], schema)
                return schema.model_validate(json.loads(response.text)).model_dump()
            finally:
                if uploaded is not None:
                    self.client.files.delete(name=uploaded.name)

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=2, max=30), reraise=True)
    def embed(self, texts: List[str]) -> List[List[float]]:
        response = self.client.models.embed_content(model=self.embed_model, contents=texts)
        return [embedding.values for embedding in response.embeddings]
