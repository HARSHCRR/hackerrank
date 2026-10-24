# WORKFLOW.md — Execution & Efficiency Protocol

## 1. Turn-by-Turn Loop
1. **Read State**: Check `PROGRESS.md` and current step in `STEPS.md`.
2. **Implement Increment**: Write clean, modular Python code for the current step only.
3. **Run Verification**: Execute the step's verification command in the terminal and inspect actual stdout/stderr.
4. **Update Tracking**:
   - Update `PROGRESS.md` (`Done`, `In Progress`, `Blocked`, `Key Decisions`).
   - Append the mandatory turn summary to `<repo_root>/log.txt` per `AGENTS.md` §5.2, and verify `tool=` and `model=` lines.
5. **3-Line Summary**: Report the step result to the user in 3 lines or fewer.

## 2. Token & Runtime Efficiency Rules
1. **Index Once, Query 518 Times**: Never call the LLM inside a 518-iteration loop over raw evidence files. Parse all evidence once in `code/indexer.py` and persist multimodal extractions in `code/cached_extractions.py`.
2. **Batch Intent Classification**: Send `request_text` items in batches of 25–50 with structured JSON output and cache results in `code/cached_extractions.py` so subsequent runs require 0 API calls.
3. **Deterministic Diffing on Samples**: Whenever predictions on the 32 sample cases diverge from `sample_output.csv`, never guess—print the exact diff between expected and predicted `steps_json`, inspect the underlying evidence rows for that `case_id`, and fix the rule deterministically.
4. **Two-Strike Stop Rule**: If any verification command fails twice on the same issue, stop immediately, present the root cause and exact traceback/diff, and ask the user before proceeding.
