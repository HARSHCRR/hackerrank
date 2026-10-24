# STEPS.md — Incremental Verified Build Plan

## Step 1: Dataset & Sample Forensics Script (Size: Small)
- **Goal**: Inspect exact columns, enum values, timestamp formats, `deletion_rules.csv` logic, and print all 32 `sample_deletion_requests.csv` + `sample_output.csv` cases alongside their matching rows from `user_identities.csv`, `user_audit_log.csv`, `system_activity.csv`, and `evidence_files.csv`.
- **Files Touched**: `code/inspect_dataset.py`
- **Verification**: `.venv/bin/python code/inspect_dataset.py` prints a complete schema summary and all 32 sample case breakdowns without errors.

## Step 2: Local Evaluation Harness & Metrics Engine (Size: Small)
- **Goal**: Build the deterministic grader that compares a predicted CSV against `dataset/sample_output.csv` and reports Case Status Accuracy, Exact Case Match, Step Precision/Recall/F1, Field-level Accuracy, and Sequence Accuracy, plus detailed diffs for any mismatched case.
- **Files Touched**: `code/evaluation/main.py`
- **Verification**: `.venv/bin/python code/evaluation/main.py --pred dataset/sample_output.csv --gold dataset/sample_output.csv` returns 100.0% across all metrics.

## Step 3: Telemetry & Token/Cost Tracker (Size: Small)
- **Goal**: Create a wrapper for all Gemini API calls that tracks model name, call count, input tokens, output tokens, and estimated USD cost, and writes `code/evaluation/usage_report.md` + `evaluation/usage_report.md`.
- **Files Touched**: `code/config.py`, `code/telemetry.py`, `code/prompts.py`
- **Verification**: `.venv/bin/python -c "from code.telemetry import TelemetryTracker; print('OK')"` runs cleanly.

## Step 4: Global Evidence Indexer & Multimodal Cache (Size: Medium)
- **Goal**: Parse all `.sql` files (via in-memory `sqlite3`), `.json`, `.log`, `.txt`, `.pdf`, and image files in `dataset/evidence/` mapped to `evidence_files.csv` (`file_id`, `source_origin`, `capture_time`). Cache extracted PDF/image structured records into `code/cached_extractions.py`.
- **Files Touched**: `code/indexer.py`, `code/cached_extractions.py`
- **Verification**: `.venv/bin/python code/indexer.py --verify` indexes 100% of files in `dataset/evidence_files.csv` and prints summary counts by source type with zero missing `file_id`s.

## Step 5: Historical Identity Graph Resolver (Size: Small)
- **Goal**: Build transitive identity resolution over `user_identities.csv` and `user_audit_log.csv` (filtered by `<= audit_at` when appropriate), linking `user_id`, current/historical emails, names, phones, email hashes, and `audit_id` provenance.
- **Files Touched**: `code/identity_resolver.py`
- **Verification**: `.venv/bin/python code/identity_resolver.py --test-samples` resolves all authorized users in `sample_deletion_requests.csv` and matches every `audit_id` cited in `sample_output.csv`.

## Step 6: Request Intent Classifier (Size: Small)
- **Goal**: Classify `request_text` into authorized deletion vs `NOT_APPLICABLE` using deterministic rules + batched Gemini Flash verification cached in Python.
- **Files Touched**: `code/intent_classifier.py`, `code/prompts.py`
- **Verification**: `.venv/bin/python code/intent_classifier.py --test-samples` achieves 32/32 intent classification accuracy against `sample_output.csv`.

## Step 7: Temporal State Reconstructor & Policy Engine (Size: Large)
- **Goal**: Reconstruct resource states, replica drift, tombstones, active sync flows, and backup restore risks at `audit_at`, apply `deletion_rules.csv`, and serialize canonically ordered `steps_json`. Iterate until achieving 32/32 exact match on `sample_output.csv`.
- **Files Touched**: `code/state_reconstructor.py`, `code/policy_engine.py`
- **Verification**: `.venv/bin/python code/evaluation/main.py` achieves 32/32 (100% case, step, field, and sequence accuracy) on `dataset/sample_output.csv`.

## Step 8: Custom Synthetic Evaluation Cases (Size: Small)
- **Goal**: Create 3+ adversarial evaluation test cases in `code/evaluation/synthetic_cases.py` covering replica drift, tombstone PII exposure via historical alias, and deceptive non-deletion requests, and verify the pipeline passes all of them.
- **Files Touched**: `code/evaluation/synthetic_cases.py`, `code/evaluation/main.py`
- **Verification**: `.venv/bin/python code/evaluation/main.py --run-synthetic` passes 100% of synthetic cases.

## Step 9: Full 518-Case Production Run & Strict Validation (Size: Medium)
- **Goal**: Execute `.venv/bin/python code/main.py` on `dataset/deletion_requests.csv` to produce root `output.csv` and generate `evaluation_report.md` and `usage_report.md` in both `code/evaluation/` and `evaluation/`.
- **Files Touched**: `code/main.py`, `code/validate_submission.py`, `output.csv`, `code/evaluation/evaluation_report.md`, `code/evaluation/usage_report.md`
- **Verification**: `.venv/bin/python code/validate_submission.py` confirms 518 sorted rows, valid JSON, consecutive `step_no`, valid `evidence_id` citations, and valid reports.

## Step 10: Documentation & Clean Packaging (Size: Small)
- **Goal**: Write comprehensive `README.md`, verify `log.txt` compliance, and package `code.zip` without `dataset/`, `.venv/`, `__pycache__/`, or nested archives.
- **Files Touched**: `README.md`, `code.zip`
- **Verification**: `unzip -l code.zip` confirms required files are present and zero forbidden/archive files exist.
