#!/usr/bin/env python3
"""
Inspect and correlate dataset files for HackerRank Orchestrate: Ghost Data Still Exists.
Analyzes schemas, enums, temporal ranges, and correlates all 32 sample cases with
identities, audit logs, system activities, evidence files, and expected sample outputs.
"""

import csv
import json
import os
import sys
from pathlib import Path
from collections import Counter, defaultdict

def load_csv(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def inspect():
    repo_root = Path(__file__).resolve().parent.parent
    dataset_dir = repo_root / "dataset"

    print("=" * 80)
    print("GHOST DATA STILL EXISTS — DATASET FORENSICS & SAMPLE CORRELATION")
    print("=" * 80)

    # 1. Load CSVs
    del_reqs = load_csv(dataset_dir / "deletion_requests.csv")
    sample_reqs = load_csv(dataset_dir / "sample_deletion_requests.csv")
    sample_out = load_csv(dataset_dir / "sample_output.csv")
    identities = load_csv(dataset_dir / "user_identities.csv")
    audit_log = load_csv(dataset_dir / "user_audit_log.csv")
    activity = load_csv(dataset_dir / "system_activity.csv")
    rules = load_csv(dataset_dir / "deletion_rules.csv")
    evidence_files = load_csv(dataset_dir / "evidence_files.csv")

    print(f"\n[1] File Inventory & Row Counts:")
    print(f"  • deletion_requests.csv:        {len(del_reqs):>5} requests")
    print(f"  • sample_deletion_requests.csv: {len(sample_reqs):>5} sample requests")
    print(f"  • sample_output.csv:            {len(sample_out):>5} sample ground truth rows")
    print(f"  • user_identities.csv:          {len(identities):>5} current user identities")
    print(f"  • user_audit_log.csv:           {len(audit_log):>5} historical identity changes")
    print(f"  • system_activity.csv:          {len(activity):>5} operational events")
    print(f"  • deletion_rules.csv:           {len(rules):>5} policy rules")
    print(f"  • evidence_files.csv:           {len(evidence_files):>5} evidence files")

    # 2. Deletion Rules summary
    print(f"\n[2] Deletion Rules Summary ({len(rules)} rules):")
    for r in rules:
        print(f"  {r['rule_id']}: {r['data_category']:<24} [{r['condition']:<20}] -> {r['required_action']}")

    # 3. Evidence files manifest summary
    evidence_by_type = Counter()
    for ev in evidence_files:
        ext = ev["file_path"].split(".")[-1]
        evidence_by_type[ext] += 1
    print(f"\n[3] Evidence Files Manifest Breakdown ({len(evidence_files)} files):")
    for ext, count in sorted(evidence_by_type.items()):
        print(f"  • .{ext:<5}: {count:>2} files")

    # 4. Identity Graph lookup maps
    user_by_id = {u["user_id"]: u for u in identities}
    user_by_curr_email = {u["email"].lower(): u for u in identities}
    
    # Audit log historical email -> user_id
    user_by_hist_email = {}
    for entry in audit_log:
        if entry["field_name"] == "email":
            if entry["old_value"]:
                user_by_hist_email[entry["old_value"].lower()] = entry["user_id"]
            if entry["new_value"]:
                user_by_hist_email[entry["new_value"].lower()] = entry["user_id"]

    # Sample output indexed by case_id
    sample_out_map = {row["case_id"]: row for row in sample_out}

    # 5. Analyze the 32 sample cases
    print(f"\n[4] Sample Cases Forensics (32 Cases):")
    status_counts = Counter(row["deletion_status"] for row in sample_out)
    print(f"  Sample Output Status Distribution: {dict(status_counts)}")

    phase_counter = Counter()
    op_counter = Counter()
    evidence_type_counter = Counter()

    for req in sample_reqs:
        cid = req["case_id"]
        req_email = req["email"].lower()
        audit_at = req["audit_at"]
        gold = sample_out_map.get(cid, {})
        gold_status = gold.get("deletion_status", "UNKNOWN")
        steps = json.loads(gold.get("steps_json", "[]"))

        # Resolve user
        matched_user = user_by_curr_email.get(req_email)
        matched_via = "current_email"
        if not matched_user:
            uid = user_by_hist_email.get(req_email)
            if uid:
                matched_user = user_by_id.get(uid)
                matched_via = f"historical_audit_log({uid})"

        uid_str = matched_user["user_id"] if matched_user else "NOT_FOUND"

        # Tally steps
        phases = [s.get("phase") for s in steps]
        for p in phases:
            phase_counter[p] += 1
        for s in steps:
            op_counter[s.get("operation")] += 1
            ev_id = s.get("evidence_id", "")
            if ev_id.startswith("evidence_"):
                evidence_type_counter["file_id"] += 1
            elif ev_id.startswith("activity_"):
                evidence_type_counter["activity_id"] += 1
            elif ev_id.startswith("audit_"):
                evidence_type_counter["audit_id"] += 1
            elif ev_id == "":
                evidence_type_counter["empty (remediation/future)"] += 1
            else:
                evidence_type_counter["other"] += 1

        print(f"  Case: {cid:<8} | Status: {gold_status:<10} | Steps: {len(steps):>2} | User: {uid_str:<9} ({matched_via}) | Claim: {req['reported_status']}")

    print(f"\n[5] Sample Steps Breakdown:")
    print(f"  Phases:     {dict(phase_counter)}")
    print(f"  Operations: {dict(op_counter)}")
    print(f"  Evidence ID types cited in sample_output.csv: {dict(evidence_type_counter)}")

    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETED: ALL DATASET FILES INSPECTED AND CORRELATED SUCCESSFULLY.")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = inspect()
    sys.exit(0 if success else 1)
