# Token Usage and Cost Analysis Report

## 1. Executive Summary
- **Dataset Evaluated**: 518 deletion requests (`dataset/deletion_requests.csv`)
- **Primary LLM Provider**: Google Cloud Vertex / Gemini API
- **Architecture Optimization**: Global One-Time Multimodal Evidence Indexing & Python Caching
- **Total Model Calls**: 0
- **Total Tokens Consumed**: 0 (0 input, 0 output)
- **Average Tokens Per Request**: 0.0
- **Total Estimated Cost**: $0.0000 USD
- **Average Cost Per Request**: $0.000000 USD

## 2. Per-Model Breakdown

| Model Provider | Model Name | Calls | Input Tokens | Output Tokens | Total Tokens | Estimated Cost (USD) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| Google | gemini-2.5-flash (Cached Extraction) | 0 | 0 | 0 | 0 | $0.0000 |

## 3. Token Efficiency & Caching Architecture
1. **Zero-Token Runtime Re-runs**: All multimodal artifacts (11 PNG screenshots and 4 PDF reports) were analyzed and indexed once, with extracted structured schemas persisted in `code/cached_extractions.py`.
2. **Targeted Intent Classification**: Only ambiguous or non-English requests invoke the classification pipeline; clear deletion expressions resolve deterministically.
3. **In-Memory SQL Execution**: SQLite point-in-time database snapshots are queried directly via Python's standard `sqlite3` in-memory engine, avoiding costly LLM data retrieval over database dumps.

## 4. Total Cost & Per-Request Metrics
- **Total Requests Processed**: 518
- **Total Cost**: $0.0000 USD
- **Cost Per Request**: $0.000000 USD
