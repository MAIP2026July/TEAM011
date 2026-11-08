"""Smoke test: one real extraction and one embedding. Needs GEMINI_API_KEY in .env."""
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from backend.document_analyzer import extract_document
from backend.llm_client import GeminiClient

path = Path(sys.argv[1]) if len(sys.argv) > 1 else next(Path("eval/folders/dev").glob("*/*Application*.pdf"))
llm = GeminiClient()
print("Models:", llm.model, llm.embed_model)
print("Embedding size:", len(llm.embed(["signature on the application"])[0]))
print(json.dumps(extract_document(llm, path.read_bytes(), path.name, "application/pdf"), indent=2))
