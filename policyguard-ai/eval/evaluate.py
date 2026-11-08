"""Runs the real pipeline over the test set. Usage: python eval/evaluate.py dev|holdout|all

Compares PolicyGuard with a filename-only script. Responses are cached, so reruns cost nothing.
"""
import hashlib
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from backend.config import GEMINI_EMBED_MODEL, GEMINI_MODEL, RETRIEVAL_TOP_K
from backend.document_analyzer import rule_query
from backend.llm_client import GeminiClient
from backend.pipeline import run_audit
from backend.rulebook_store import RulebookStore, load_rules
from backend.structure_validator import validate_folder_structure

HERE = Path(__file__).parent
CACHE = Path.home() / ".cache" / "policyguard-ai" / "eval"
MIN_SECONDS_BETWEEN_CALLS = 4.5


class CachedLLM:
    def __init__(self, llm):
        self.llm, self.model, self.embed_model = llm, llm.model, llm.embed_model
        self.calls, self.seconds, self.last_call = 0, 0.0, 0.0
        CACHE.mkdir(parents=True, exist_ok=True)

    def _cached(self, parts, call):
        digest = hashlib.sha256(json.dumps([self.model, self.embed_model, *parts], sort_keys=True).encode()).hexdigest()
        path = CACHE / f"{digest}.json"
        if path.exists():
            return json.loads(path.read_text())
        wait = MIN_SECONDS_BETWEEN_CALLS - (time.time() - self.last_call)
        if wait > 0:
            time.sleep(wait)
        started = time.time()
        try:
            value = call()
        except Exception as error:
            if "PerDay" in str(error):  # never score a run the quota cut short
                raise SystemExit(f"Daily quota reached after {self.calls} live calls. Rerun tomorrow: cached calls are kept.")
            raise
        self.last_call = time.time()
        self.seconds += self.last_call - started
        self.calls += 1
        path.write_text(json.dumps(value))
        return value

    def analyse_file(self, file_bytes, filename, mime_type, prompt, schema):
        key = [hashlib.sha256(file_bytes).hexdigest(), prompt, schema.__name__]
        return self._cached(key, lambda: self.llm.analyse_file(file_bytes, filename, mime_type, prompt, schema))

    def generate_json(self, prompt, schema):
        return self._cached([prompt, schema.__name__], lambda: self.llm.generate_json(prompt, schema))

    def generate_text(self, prompt):
        return self._cached([prompt, "text"], lambda: self.llm.generate_text(prompt))

    def embed(self, texts):
        return self._cached(["embed", texts], lambda: self.llm.embed(texts))


def prf(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(precision, 3), "recall": round(recall, 3)}


def score(found_by_folder, truth):
    tp = fp = fn = 0
    per_rule = defaultdict(lambda: [0, 0, 0])
    for policy, entry in truth.items():
        expected, found = set(entry["expected_rules"]), found_by_folder[policy]
        for rule in expected & found:
            tp += 1; per_rule[rule][0] += 1
        for rule in found - expected:
            fp += 1; per_rule[rule][1] += 1
        for rule in expected - found:
            fn += 1; per_rule[rule][2] += 1
    return prf(tp, fp, fn), {rule: prf(*counts) for rule, counts in sorted(per_rule.items())}


def run(split):
    all_truth = json.loads((HERE / "ground_truth.json").read_text())
    truth = {p: e for p, e in all_truth["folders"].items() if split == "all" or e["split"] == split}
    as_of = date.fromisoformat(all_truth["as_of"])
    llm = CachedLLM(GeminiClient())
    store = RulebookStore(llm.embed, llm.embed_model)
    rules = load_rules()

    results, ai_found, baseline_found, seconds = {}, {}, {}, {}
    for policy, entry in truth.items():
        folder = HERE / "folders" / entry["split"] / policy
        files = [(p.name, p.read_bytes(), "application/pdf") for p in sorted(folder.glob("*.pdf"))]
        started = time.time()
        calls_before = llm.calls
        result = run_audit(policy, files, as_of, llm, store)
        if llm.calls > calls_before:
            seconds[policy] = round(time.time() - started, 1)
        results[policy] = result
        ai_found[policy] = {f["rule_id"] for f in result["findings"] if f["status"] == "fail"}
        baseline_found[policy] = {f["rule_id"] for f in validate_folder_structure(policy, [f[0] for f in files])}
        print(policy, result["audit"]["status"], sorted(ai_found[policy]), "expected", entry["expected_rules"], flush=True)

    ai_overall, ai_rules = score(ai_found, truth)
    base_overall, base_rules = score(baseline_found, truth)
    all_findings = [f for r in results.values() for f in r["findings"]]
    ai_findings = [f for f in all_findings if f["source"] != "rule"]
    clean = [p for p, e in truth.items() if not e["expected_rules"]]
    critical = {r["id"] for r in rules.values() if r["severity"] == "critical"}
    expected_llm = {t: {r["id"] for r in rules.values() if r["method"] == "llm" and t in r["applies_to"]}
                    for t in ("Application", "Risk_Assessment", "Inspection_Report", "Signed_Disclosure")}
    retrieval_hits = retrieval_total = 0
    for result in results.values():
        for filename, retrieved in result["retrieved_rules"].items():
            wanted = expected_llm.get(result["extractions"].get(filename, {}).get("document_type", {}).get("value"), set())
            retrieval_hits += len(wanted & set(retrieved))
            retrieval_total += len(wanted)
    report = {
        "split": split, "folders": len(truth), "model": GEMINI_MODEL, "embedding_model": GEMINI_EMBED_MODEL,
        "policyguard": ai_overall, "baseline_filename_only": base_overall,
        "per_rule_policyguard": ai_rules, "per_rule_baseline": base_rules,
        "renewal_match": round(sum(results[p]["renewal"]["recommendation"] == e["expected_renewal"] for p, e in truth.items()) / len(truth), 3),
        "renewal_mismatches": {p: results[p]["renewal"]["recommendation"] for p, e in truth.items() if results[p]["renewal"]["recommendation"] != e["expected_renewal"]},
        "missed_critical": {p: sorted((set(e["expected_rules"]) & critical) - ai_found[p]) for p, e in truth.items() if (set(e["expected_rules"]) & critical) - ai_found[p]},
        "clean_folders_flagged": [p for p in clean if ai_found[p]],
        "clean_folders": len(clean),
        "ai_evidence": dict(Counter(f["verification"] for f in ai_findings)),
        "confidence_bands": dict(Counter(f["confidence_band"] for f in all_findings)),
        "statuses": dict(Counter(r["audit"]["status"] for r in results.values())),
        "rejected_citations": sum(len(r["rejected_citations"]) for r in results.values()),
        "failed_documents": {p: r["failed_documents"] for p, r in results.items() if r["failed_documents"]},
        "rationale_sources": dict(Counter(r["renewal"]["rationale_source"] for r in results.values())),
        f"rulebook_recall_at_{RETRIEVAL_TOP_K}": round(retrieval_hits / retrieval_total, 3) if retrieval_total else None,
        "live_api_calls_this_run": llm.calls, "live_seconds_per_folder": seconds,
    }
    (HERE / f"results_{split}.json").write_text(json.dumps(report, indent=2))
    (HERE / f"raw_{split}.json").write_text(json.dumps(results, indent=2, default=str))
    print(json.dumps({k: v for k, v in report.items() if not k.startswith("per_rule")}, indent=2))


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "dev")
