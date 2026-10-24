#!/usr/bin/env python3
"""
Evaluation Harness & Metrics Engine for HackerRank Orchestrate: Ghost Data Still Exists.
Evaluates predictions against gold answers with comprehensive metrics:
- Case-Level Status Accuracy
- Exact Case Match
- Step Precision, Recall, F1
- Field-Level Accuracy (phase, system_id, resource_id, operation, state, evidence_id)
- Sequence Order Accuracy
"""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate Ghost Data Still Exists predictions")
    parser.add_argument("--pred", type=str, default="dataset/sample_output.csv", help="Path to predictions CSV")
    parser.add_argument("--gold", type=str, default="dataset/sample_output.csv", help="Path to gold standard CSV")
    parser.add_argument("--verbose", action="store_true", help="Print detailed diffs for mismatched cases")
    parser.add_argument("--run-synthetic", action="store_true", help="Run evaluation against synthetic test cases")
    return parser.parse_args()

def load_submission_csv(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    cases = {}
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["case_id"]
            status = row["deletion_status"]
            steps_raw = row["steps_json"]
            try:
                steps = json.loads(steps_raw)
            except Exception as e:
                steps = []
                print(f"[ERROR] Invalid JSON in case {cid}: {e}", file=sys.stderr)
            cases[cid] = {
                "case_id": cid,
                "deletion_status": status,
                "steps": steps,
            }
    return cases

def step_key(s):
    """Canonical key for a step (excluding step_no to evaluate unordered set match)."""
    return (
        s.get("phase", ""),
        s.get("system_id", ""),
        s.get("resource_id", ""),
        s.get("operation", ""),
        s.get("state", ""),
        s.get("evidence_id", ""),
    )

def evaluate(pred_cases, gold_cases, verbose=False):
    total_gold_cases = len(gold_cases)
    if total_gold_cases == 0:
        print("No gold cases to evaluate.")
        return {}

    correct_status_count = 0
    exact_case_match_count = 0
    sequence_match_count = 0

    total_pred_steps = 0
    total_gold_steps = 0
    true_positive_steps = 0

    field_correct = defaultdict(int)
    field_total = defaultdict(int)
    fields = ["phase", "system_id", "resource_id", "operation", "state", "evidence_id", "step_no"]

    mismatches = []

    for cid, gold in gold_cases.items():
        pred = pred_cases.get(cid)
        if not pred:
            mismatches.append((cid, "MISSING_IN_PREDICTIONS", gold, None))
            continue

        gold_status = gold["deletion_status"]
        pred_status = pred["deletion_status"]
        gold_steps = gold["steps"]
        pred_steps = pred["steps"]

        status_matches = (pred_status == gold_status)
        if status_matches:
            correct_status_count += 1

        total_gold_steps += len(gold_steps)
        total_pred_steps += len(pred_steps)

        gold_keys = [step_key(s) for s in gold_steps]
        pred_keys = [step_key(s) for s in pred_steps]

        # Calculate step overlap
        gold_key_counts = defaultdict(int)
        for k in gold_keys:
            gold_key_counts[k] += 1

        for k in pred_keys:
            if gold_key_counts[k] > 0:
                true_positive_steps += 1
                gold_key_counts[k] -= 1

        # Check sequence order
        is_sequence_match = (pred_keys == gold_keys)
        if is_sequence_match:
            sequence_match_count += 1

        # Field-level accuracy for steps aligned by index (up to min length)
        min_len = min(len(pred_steps), len(gold_steps))
        max_len = max(len(pred_steps), len(gold_steps))
        for i in range(min_len):
            p_step = pred_steps[i]
            g_step = gold_steps[i]
            for f in fields:
                field_total[f] += 1
                if p_step.get(f) == g_step.get(f):
                    field_correct[f] += 1

        # Excess / missing steps penalize field totals
        for i in range(min_len, max_len):
            for f in fields:
                field_total[f] += 1

        exact_match = status_matches and is_sequence_match and (len(pred_steps) == len(gold_steps))
        if exact_match:
            exact_case_match_count += 1
        else:
            mismatches.append((cid, "MISMATCH", gold, pred))

    case_status_acc = (correct_status_count / total_gold_cases) * 100.0
    exact_case_acc = (exact_case_match_count / total_gold_cases) * 100.0
    sequence_acc = (sequence_match_count / total_gold_cases) * 100.0

    step_precision = (true_positive_steps / total_pred_steps * 100.0) if total_pred_steps > 0 else 0.0
    step_recall = (true_positive_steps / total_gold_steps * 100.0) if total_gold_steps > 0 else 0.0
    step_f1 = (2 * step_precision * step_recall / (step_precision + step_recall)) if (step_precision + step_recall) > 0 else 0.0

    field_accuracies = {}
    for f in fields:
        field_accuracies[f] = (field_correct[f] / field_total[f] * 100.0) if field_total[f] > 0 else 0.0

    overall_field_acc = (sum(field_correct.values()) / sum(field_total.values()) * 100.0) if sum(field_total.values()) > 0 else 0.0

    # Summary Report
    print("=" * 75)
    print("EVALUATION HARNESS REPORT")
    print("=" * 75)
    print(f"Total Evaluated Cases:         {total_gold_cases}")
    print(f"Case-Level Status Accuracy:    {case_status_acc:>6.2f}% ({correct_status_count}/{total_gold_cases})")
    print(f"Exact Case Match (All Fields): {exact_case_acc:>6.2f}% ({exact_case_match_count}/{total_gold_cases})")
    print(f"Sequence Order Accuracy:       {sequence_acc:>6.2f}% ({sequence_match_count}/{total_gold_cases})")
    print("-" * 75)
    print(f"Step Precision:                {step_precision:>6.2f}% ({true_positive_steps}/{total_pred_steps})")
    print(f"Step Recall:                   {step_recall:>6.2f}% ({true_positive_steps}/{total_gold_steps})")
    print(f"Step F1 Score:                 {step_f1:>6.2f}%")
    print("-" * 75)
    print(f"Overall Field-Level Accuracy:  {overall_field_acc:>6.2f}%")
    for f, acc in field_accuracies.items():
        print(f"  • {f:<15}:          {acc:>6.2f}% ({field_correct[f]}/{field_total[f]})")
    print("=" * 75)

    if mismatches and verbose:
        print(f"\n[MISMATCH DETAILS — {len(mismatches)} Cases]:")
        for cid, reason, gold, pred in mismatches[:10]:
            print(f"\n--- {cid} ({reason}) ---")
            print(f"Expected Status: {gold.get('deletion_status')} | Predicted Status: {pred.get('deletion_status') if pred else 'None'}")
            print(f"Expected Steps ({len(gold.get('steps', []))}):")
            print(json.dumps(gold.get("steps", []), indent=2))
            print(f"Predicted Steps ({len(pred.get('steps', [])) if pred else 0}):")
            print(json.dumps(pred.get("steps", []) if pred else [], indent=2))

    return {
        "case_status_acc": case_status_acc,
        "exact_case_acc": exact_case_acc,
        "sequence_acc": sequence_acc,
        "step_precision": step_precision,
        "step_recall": step_recall,
        "step_f1": step_f1,
        "overall_field_acc": overall_field_acc,
        "field_accuracies": field_accuracies,
        "mismatches": mismatches,
    }

def main():
    args = parse_args()
    if args.run_synthetic:
        from code.evaluation.synthetic_cases import run_synthetic_tests
        success = run_synthetic_tests()
        sys.exit(0 if success else 1)

    repo_root = Path(__file__).resolve().parent.parent.parent
    pred_path = repo_root / args.pred if not os.path.isabs(args.pred) else Path(args.pred)
    gold_path = repo_root / args.gold if not os.path.isabs(args.gold) else Path(args.gold)

    pred_cases = load_submission_csv(pred_path)
    gold_cases = load_submission_csv(gold_path)

    results = evaluate(pred_cases, gold_cases, verbose=args.verbose)
    is_perfect = (results.get("exact_case_acc") == 100.0)
    sys.exit(0 if is_perfect else 1)

if __name__ == "__main__":
    main()
