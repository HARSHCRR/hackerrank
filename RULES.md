# RULES.md — Non-Negotiable Engineering & Grader Rules

## 1. AGENTS.md & Logging Compliance
1. **Shared Root Log (`log.txt`)**: Append a `SESSION START` block at session start and a per-turn summary block after every user turn in `<repo_root>/log.txt` following `AGENTS.md` §5.1–5.2.
2. **Authoritative Tool & Model Fields**: Every `log.txt` entry MUST include non-empty, exact `tool=` and `model=` fields. Never use `unknown` or placeholders. Before finishing any turn, re-read the tail of `log.txt` to verify.
3. **Zero Secrets**: Never hardcode, print, commit, zip, or log API keys, tokens, credentials, or `.env` values. Load keys exclusively via `os.environ` / `.env` (which must be in `.gitignore`).
4. **Participant-Only Data**: Only read from `dataset/`. Never fabricate or hardcode answers for the 518 test cases in `deletion_requests.csv`.

## 2. Automated Code Judge Visibility Constraints
1. **Ignored Data Extensions**: The HackerRank automated code judge ignores `.csv`, `.tsv`, `.json`, `.jsonl`, `.sql`, and `.log` files when inspecting your code submission.
2. **Code & Markdown Storage Rule**:
   - Store all LLM/Vision prompts inside `code/prompts.py` (never in external `.json` files).
   - Cache extracted multimodal evidence (from PDFs/images) as a Python dictionary inside `code/cached_extractions.py` so the code judge can inspect it and re-runs are 100% deterministic.
   - Define the 3+ custom evaluation cases inside `code/evaluation/synthetic_cases.py` AND write their full schemas, inputs, expected outputs, and analysis directly inside `code/evaluation/evaluation_report.md`.
   - Mirror `evaluation_report.md` and `usage_report.md` in both `code/evaluation/` and `<repo_root>/evaluation/`.

## 3. Domain & Policy Correctness Rules
1. **Intent First (`NOT_APPLICABLE`)**: Evaluate `request_text` before anything else. Requests for data export, access, correction, subscription pause, or marketing opt-out without account/personal-data deletion intent MUST return `deletion_status = "NOT_APPLICABLE"` and `steps_json = []`, regardless of `reported_status`.
2. **Never Trust Claims**: `reported_status` in `deletion_requests.csv` and operation result statuses in `system_activity.csv` are unverified claims. Establish ground truth at `audit_at` from evidence snapshots and activity timelines.
3. **Strict Temporal Horizon (`<= audit_at`)**: Ignore any evidence snapshot (`capture_time`), audit event (`changed_at`), or system activity (`activity_at`) that occurred strictly after the case's `audit_at` timestamp.
4. **Transitive Identity Resolution**: Resolve the user across both `user_identities.csv` and `user_audit_log.csv` (matching current and historical `email`, `name`, `phone`, `email_hash`, and computed MD5/SHA-256 hashes of historical emails).
5. **Tombstones & Retained Records**:
   - Records required to be retained by `deletion_rules.csv` must remain `PRESENT` (`VERIFY_RECORD_PRESENT`).
   - Account tombstones may keep the internal `user_id` reference, but if any direct PII (`name`, `email`, `phone`, `email_hash`) remains present at `audit_at`, emit `REPORT_EXPOSED_PII` -> `REDACT_RECORD` -> `VERIFY_RECORD_REDACTED`.

## 4. Serialization & Canonical Step Ordering
1. **Output Format**: `<repo_root>/output.csv` must have exact header `case_id,deletion_status,steps_json` and 518 rows sorted ascending by `case_id`.
2. **Phase & Operation Order**:
   - Phases: `FINDING` (1) -> `REMEDIATION` (2) -> `VERIFICATION` (3).
   - Operations within `FINDING`: `REPORT_REMAINING_RECORD` (1), `REPORT_EXPOSED_PII` (2), `REPORT_ACTIVE_DATA_FLOW` (3), `REPORT_RESTORE_RISK` (4).
   - Operations within `REMEDIATION`: `DISABLE_DATA_FLOW` (1), `BLOCK_RESTORE` (2), `DELETE_RECORD` (3), `REDACT_RECORD` (4), `ANONYMIZE_RECORD` (5).
   - Operations within `VERIFICATION`: `VERIFY_RECORD_ABSENT` (1), `VERIFY_RECORD_PRESENT` (2), `VERIFY_RECORD_REDACTED` (3), `VERIFY_RECORD_ANONYMIZED` (4), `VERIFY_DATA_FLOW_DISABLED` (5), `VERIFY_RESTORE_BLOCKED` (6).
   - Tie-breakers within same `(phase, operation)`: dependency order (if required by `AGENTS.md` §6.5 and verified on `sample_output.csv`), then `system_id` ascending, then `resource_id` ascending.
3. **Step Numbering & Evidence Citations**:
   - `step_no` starts at `1` and increments consecutively (`1..N`).
   - `COMPLETE`: Only `VERIFICATION` steps; every step MUST cite a non-empty `evidence_id` (`file_id`, `activity_id`, or `audit_id`).
   - `INCOMPLETE`: `FINDING` steps MUST cite a non-empty `evidence_id`. Proposed `REMEDIATION` and future `VERIFICATION` steps MUST use `"evidence_id": ""`.
