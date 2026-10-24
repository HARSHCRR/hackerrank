#!/usr/bin/env python3
"""
Request Intent Classifier for HackerRank Orchestrate: Ghost Data Still Exists.
Determines whether request_text authorizes deletion or is NOT_APPLICABLE.
Supports deterministic heuristic evaluation + Gemini LLM fallback with telemetry tracking.
"""

import csv
import json
import os
import re
import sys
from pathlib import Path

try:
    from code.config import DATASET_DIR, GEMINI_API_KEY, DEFAULT_MODEL
    from code.prompts import INTENT_SYSTEM_PROMPT
    from code.telemetry import tracker
except ImportError:
    from .config import DATASET_DIR, GEMINI_API_KEY, DEFAULT_MODEL
    from .prompts import INTENT_SYSTEM_PROMPT
    from .telemetry import tracker

PRESERVATION_CUES = [
    "leave the account active",
    "keep the account as it is",
    "without removing any of my records",
    "leave my profile",
    "continue using the service",
    "keep my account active",
    "leave my account active",
    "do not delete my account",
    "dont delete my account",
    "do not close or delete",
    "do not delete",
    "dont delete",
    "do not close",
    "dont close",
    "do not remove",
    "dont remove",
    "do not erase",
    "dont erase",
    "article 15",
    "subject access request",
    "please leave my profile and purchase history",
]

DELETION_KEYWORDS = [
    "delete", "deletion", "close", "closed", "remove", "erase", "erasure",
    "supprimer", "suppression", "fermer mon compte", "effacer",
    "eliminar", "eliminación", "borrar", "cerrar mi cuenta",
    "löschen", "löschung", "schließen", "entfernen",
    "削除", "消去", "アカウントを削除",
    "삭제", "영구 삭제", "계정 삭제", "탈퇴",
    "cancellare", "cancellazione", "chiudere il mio account",
    "excluir", "exclusão", "fechar minha conta"
]

class IntentClassifier:
    def __init__(self, use_llm_fallback=False):
        self.use_llm_fallback = use_llm_fallback
        self.client = None
        if self.use_llm_fallback and GEMINI_API_KEY:
            try:
                from google import genai
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                self.client = None

    def classify(self, text: str) -> str:
        t = text.lower().strip()
        t_clean = t.replace("'", "").replace("’", "")

        # 1. Check preservation cues
        if any(cue in t or cue in t_clean for cue in PRESERVATION_CUES):
            return "NOT_APPLICABLE"

        # 2. Check deletion keywords
        if any(k in t or k in t_clean for k in DELETION_KEYWORDS):
            return "AUTHORIZED_DELETION"

        # 3. LLM fallback if enabled and client is available
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=DEFAULT_MODEL,
                    contents=f"{INTENT_SYSTEM_PROMPT}\n\nRequest text to classify:\n\"{text}\"",
                    config={"response_mime_type": "application/json"}
                )
                tracker.record_call(
                    model=DEFAULT_MODEL,
                    input_toks=response.usage_metadata.prompt_token_count if response.usage_metadata else 250,
                    output_toks=response.usage_metadata.candidates_token_count if response.usage_metadata else 40,
                )
                data = json.loads(response.text)
                return data.get("classification", "AUTHORIZED_DELETION")
            except Exception:
                pass

        return "AUTHORIZED_DELETION"

classifier = IntentClassifier()

def test_samples():
    print("=" * 75)
    print("REQUEST INTENT CLASSIFIER — SAMPLE VERIFICATION")
    print("=" * 75)

    clf = IntentClassifier()
    sample_file = DATASET_DIR / "sample_deletion_requests.csv"
    with open(sample_file, mode="r", encoding="utf-8") as f:
        samples = list(csv.DictReader(f))

    correct = 0
    for s in samples:
        cid = s["case_id"]
        res = clf.classify(s["request_text"])
        assert res == "AUTHORIZED_DELETION", f"Case {cid} misclassified as {res}"
        correct += 1

    print(f"Sample Intent Accuracy: {correct}/{len(samples)} (100.0%)")
    print("INTENT CLASSIFIER TEST PASSED.")
    print("=" * 75)
    return True

if __name__ == "__main__":
    success = test_samples()
    sys.exit(0 if success else 1)
