#!/usr/bin/env python3
"""
Strict Submission Validator for HackerRank Orchestrate: Ghost Data Still Exists.
Validates output.csv, step schemas, ordering, evidence citations, evaluation reports,
and secret hygiene.
"""

import csv
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ALLOWED_SYSTEMS = {
    "account_service",
    "search_service",
    "support_platform",
    "analytics_platform",
    "security_service",
    "integration_service",
    "backup_service",
    "export_service",
    "identity_service",
}

ALLOWED_FINDING_OPERATIONS = {
    "REPORT_REMAINING_RECORD": "PRESENT",
    "REPORT_EXPOSED_PII": "PRESENT",
    "REPORT_ACTIVE_DATA_FLOW": "ACTIVE",
    "REPORT_RESTORE_RISK": "ACTIVE",
}

ALLOWED_REMEDIATION_OPERATIONS = {
    "DISABLE_DATA_FLOW": "DISABLED",
    "BLOCK_RESTORE": "BLOCKED",
    "DELETE_RECORD": "ABSENT",
    "REDACT_RECORD": "REDACTED",
    "ANONYMIZE_RECORD": "ANONYMIZED",
}

ALLOWED_VERIFICATION_OPERATIONS = {
    "VERIFY_RECORD_ABSENT": "ABSENT",
    "VERIFY_RECORD_PRESENT": "PRESENT",
    "VERIFY_RECORD_REDACTED": "REDACTED",
    "VERIFY_RECORD_ANONYMIZED": "ANONYMIZED",
    "VERIFY_DATA_FLOW_DISABLED": "DISABLED",
    "VERIFY_RESTORE_BLOCKED": "BLOCKED",
}

PHASE_RANK = {"FINDING": 1, "REMEDIATION": 2, "VERIFICATION": 3}

def validate_submission() -> bool:
    print("=" * 75)
    print("STRICT SUBMISSION VALIDATOR — NORTHSTAR SHOP DELETION AUDIT")
    print("=" * 75)

    errors = []
    warnings = []

    # 1. Validate output.csv exists
    out_csv = REPO_ROOT / "output.csv"
    if not out_csv.exists():
        errors.append(f"output.csv missing at expected path: {out_csv}")
        print("\n".join(f"[ERROR] {e}" for e in errors))
        return False

    # Read raw lines for header check
    with open(out_csv, mode="r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    if not raw_lines:
        errors.append("output.csv is completely empty.")
        return False

    header = raw_lines[0].strip()
    if header != "case_id,deletion_status,steps_json":
        errors.append(f"Invalid header line in output.csv: expected 'case_id,deletion_status,steps_json', got '{header}'")

    # Read evidence manifest to validate citations
    manifest_ids = set()
    manifest_csv = REPO_ROOT / "dataset" / "evidence_files.csv"
    if manifest_csv.exists():
        with open(manifest_csv, mode="r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                manifest_ids.add(r["file_id"])

    # Parse rows
    with open(out_csv, mode="r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    total_rows = len(reader)
    print(f"Total rows in output.csv: {total_rows}")
    if total_rows != 518:
        errors.append(f"Expected exactly 518 data rows in output.csv, found {total_rows}")

    case_ids_seen = set()
    prev_cid_num = 0

    for idx, row in enumerate(reader, start=1):
        cid = row.get("case_id", "")
        status = row.get("deletion_status", "")
        steps_raw = row.get("steps_json", "")

        if not cid:
            errors.append(f"Row {idx}: missing case_id")
            continue

        if cid in case_ids_seen:
            errors.append(f"Row {idx}: duplicate case_id '{cid}'")
        case_ids_seen.add(cid)

        # Check ordering
        parts = cid.split("_")
        if len(parts) >= 2 and parts[-1].isdigit():
            cnum = int(parts[-1])
            if cnum < prev_cid_num:
                errors.append(f"Row {idx}: case_id '{cid}' out of ascending order (prev was case_{prev_cid_num})")
            prev_cid_num = cnum

        if status not in ("COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"):
            errors.append(f"Row {idx} ({cid}): invalid deletion_status '{status}'")

        try:
            steps = json.loads(steps_raw)
        except Exception as e:
            errors.append(f"Row {idx} ({cid}): invalid JSON in steps_json: {e}")
            continue

        if not isinstance(steps, list):
            errors.append(f"Row {idx} ({cid}): steps_json is not a JSON list")
            continue

        if status == "NOT_APPLICABLE":
            if len(steps) != 0:
                errors.append(f"Row {idx} ({cid}): NOT_APPLICABLE case must have empty steps_json, got {len(steps)} steps")
            continue

        # For COMPLETE and INCOMPLETE
        prev_phase_rank = 0
        finding_count = 0
        remediation_count = 0
        verification_count = 0

        for s_idx, step in enumerate(steps, start=1):
            s_no = step.get("step_no")
            phase = step.get("phase")
            sys_id = step.get("system_id")
            rid = step.get("resource_id")
            op = step.get("operation")
            st = step.get("state")
            ev_id = step.get("evidence_id")

            # Consecutive step numbering
            if s_no != s_idx:
                errors.append(f"Row {idx} ({cid}) step {s_idx}: step_no must be {s_idx}, got {s_no}")

            # Permitted system check
            if sys_id not in ALLOWED_SYSTEMS:
                errors.append(f"Row {idx} ({cid}) step {s_idx}: forbidden system_id '{sys_id}'")

            # Phase progression check
            prank = PHASE_RANK.get(phase, 99)
            if prank < prev_phase_rank:
                errors.append(f"Row {idx} ({cid}) step {s_idx}: phase '{phase}' out of canonical order")
            prev_phase_rank = prank

            # Operation & State validity
            if phase == "FINDING":
                finding_count += 1
                if op not in ALLOWED_FINDING_OPERATIONS:
                    errors.append(f"Row {idx} ({cid}) step {s_idx}: invalid finding operation '{op}'")
                elif st != ALLOWED_FINDING_OPERATIONS[op]:
                    errors.append(f"Row {idx} ({cid}) step {s_idx}: state '{st}' does not match operation '{op}'")
                if not ev_id or (manifest_ids and ev_id not in manifest_ids):
                    errors.append(f"Row {idx} ({cid}) step {s_idx}: finding must cite valid evidence_id, got '{ev_id}'")

            elif phase == "REMEDIATION":
                remediation_count += 1
                if op not in ALLOWED_REMEDIATION_OPERATIONS:
                    errors.append(f"Row {idx} ({cid}) step {s_idx}: invalid remediation operation '{op}'")
                elif st != ALLOWED_REMEDIATION_OPERATIONS[op]:
                    errors.append(f"Row {idx} ({cid}) step {s_idx}: state '{st}' does not match operation '{op}'")
                if ev_id != "":
                    errors.append(f"Row {idx} ({cid}) step {s_idx}: remediation evidence_id must be empty string, got '{ev_id}'")

            elif phase == "VERIFICATION":
                verification_count += 1
                if op not in ALLOWED_VERIFICATION_OPERATIONS:
                    errors.append(f"Row {idx} ({cid}) step {s_idx}: invalid verification operation '{op}'")
                elif st != ALLOWED_VERIFICATION_OPERATIONS[op]:
                    errors.append(f"Row {idx} ({cid}) step {s_idx}: state '{st}' does not match operation '{op}'")

                if status == "COMPLETE":
                    if not ev_id or (manifest_ids and ev_id not in manifest_ids):
                        errors.append(f"Row {idx} ({cid}) step {s_idx}: COMPLETE verification must cite valid evidence_id, got '{ev_id}'")
                elif status == "INCOMPLETE":
                    if ev_id != "":
                        errors.append(f"Row {idx} ({cid}) step {s_idx}: INCOMPLETE post-remediation verification evidence_id must be empty string, got '{ev_id}'")

        if status == "COMPLETE":
            if finding_count > 0 or remediation_count > 0:
                errors.append(f"Row {idx} ({cid}): COMPLETE status cannot have findings or remediations")
            if verification_count == 0:
                errors.append(f"Row {idx} ({cid}): COMPLETE status must have at least 1 verification step")

        elif status == "INCOMPLETE":
            if finding_count == 0:
                errors.append(f"Row {idx} ({cid}): INCOMPLETE status must have at least 1 finding step")
            if remediation_count == 0:
                errors.append(f"Row {idx} ({cid}): INCOMPLETE status must have at least 1 remediation step")
            if verification_count == 0:
                errors.append(f"Row {idx} ({cid}): INCOMPLETE status must have at least 1 verification step")

    # 2. Validate documentation files
    doc_paths = [
        REPO_ROOT / "code" / "evaluation" / "evaluation_report.md",
        REPO_ROOT / "evaluation" / "evaluation_report.md",
        REPO_ROOT / "code" / "evaluation" / "usage_report.md",
        REPO_ROOT / "evaluation" / "usage_report.md",
    ]
    for dp in doc_paths:
        if not dp.exists():
            errors.append(f"Missing required documentation: {dp.relative_to(REPO_ROOT)}")
        elif dp.stat().st_size < 100:
            errors.append(f"Documentation file too small/empty: {dp.relative_to(REPO_ROOT)}")
        else:
            print(f"Verified documentation file: {dp.relative_to(REPO_ROOT)} ({dp.stat().st_size:,} bytes)")

    # 3. Secret hygiene check
    suspicious_patterns = [
        re.compile(r'AIza[0-9A-Za-z-_]{35}'),
        re.compile(r'GEMINI_API_KEY\s*=\s*["\'][A-Za-z0-9_-]{20,}["\']'),
        re.compile(r'sk-[a-zA-Z0-9]{20,}'),
    ]
    check_files = [out_csv] + doc_paths
    for cf in check_files:
        if cf.exists():
            txt = cf.read_text(encoding="utf-8", errors="ignore")
            for pat in suspicious_patterns:
                if pat.search(txt):
                    errors.append(f"POTENTIAL SECRET LEAK detected in {cf.relative_to(REPO_ROOT)}!")

    print("\n" + "=" * 75)
    if errors:
        print(f"VALIDATION FAILED WITH {len(errors)} ERRORS:")
        for err in errors[:25]:
            print(f"  [ERROR] {err}")
        if len(errors) > 25:
            print(f"  ... and {len(errors) - 25} more errors.")
        print("=" * 75)
        return False

    print("ALL VALIDATION CHECKS PASSED PERFECTLY (100.0% COMPLIANT).")
    print("=" * 75)
    return True

if __name__ == "__main__":
    success = validate_submission()
    sys.exit(0 if success else 1)
