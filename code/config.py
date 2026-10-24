"""
Configuration constants and environment settings for Ghost Data Still Exists.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

DATASET_DIR = REPO_ROOT / "dataset"
EVIDENCE_DIR = DATASET_DIR / "evidence"
EVALUATION_DIR = REPO_ROOT / "code" / "evaluation"
TOP_EVALUATION_DIR = REPO_ROOT / "evaluation"

OUTPUT_CSV = REPO_ROOT / "output.csv"
SAMPLE_OUTPUT_CSV = DATASET_DIR / "sample_output.csv"
SAMPLE_REQUESTS_CSV = DATASET_DIR / "sample_deletion_requests.csv"
DELETION_REQUESTS_CSV = DATASET_DIR / "deletion_requests.csv"

# Models and Pricing (Gemini 2.5 / 1.5 Flash reference pricing per 1M tokens)
DEFAULT_MODEL = "gemini-2.5-flash"
MODEL_PRICING = {
    "gemini-2.5-flash": {
        "input_per_million": 0.075,
        "output_per_million": 0.300,
    },
    "gemini-1.5-flash": {
        "input_per_million": 0.075,
        "output_per_million": 0.300,
    },
    "gemini-1.5-pro": {
        "input_per_million": 1.250,
        "output_per_million": 5.000,
    },
}

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
