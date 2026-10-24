#!/usr/bin/env python3
"""
Custom Adversarial Synthetic Evaluation Cases for Northstar Shop Deletion Audit.
All synthetic cases are defined as Python dataclasses/dictionaries (per hackathon constraints: zero .json/.csv test files).

Adversarial Scenarios:
1. SYNTH_01 - Replica Drift:
   Primary database confirms profile deletion, but a cross-region read replica still retains customer PII
   leading to an INCOMPLETE audit finding and mandatory remediation.
2. SYNTH_02 - Tombstone PII Exposure via Historical Alias:
   Account was deleted and a tombstone created, but unredacted phone number/historical email was left exposed
   in identity_service tombstone records, violating retention policy.
3. SYNTH_03 - Deceptive Non-Deletion Request (Subject Access Request):
   User requests a complete copy/export of their data under GDPR Art. 15 ("Right of Access") without expressing
   any intent to delete their account. Classifier must flag as NOT_APPLICABLE and output 0 steps.
4. SYNTH_04 - Concurrent Restore Risk & Active Integration Flow:
   Customer request reported as COMPLETE, but backup restore was left UNBLOCKED while an external integration
   flow remains ACTIVE, triggering multiple remediation operations.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import json
import sys

from code.intent_classifier import classifier
from code.policy_engine import policy_engine
from code.state_reconstructor import CaseReconstruction, ResourceState

@dataclass
class SyntheticCase:
    case_id: str
    scenario_name: str
    description: str
    request: Dict[str, str]
    expected_status: str
    expected_steps: List[Dict]

SYNTHETIC_CASES = [
    SyntheticCase(
        case_id="synth_case_01",
        scenario_name="Replica Drift (Secondary Read Replica Retains PII)",
        description=(
            "Primary account service reported deletion SUCCESS, but search service / replica index "
            "still contains customer profile document after the completion window. "
            "Must report FINDING on search_service, emit REMEDIATION to DELETE_RECORD, and verify absence."
        ),
        request={
            "case_id": "synth_case_01",
            "email": "replica.drift.test@example.com",
            "requested_at": "2026-09-01T10:00:00Z",
            "reported_status": "COMPLETE",
            "reported_at": "2026-09-03T10:00:00Z",
            "audit_at": "2026-09-15T12:00:00Z",
            "request_text": "Please delete my account and erase all my personal information completely from all systems.",
        },
        expected_status="INCOMPLETE",
        expected_steps=[
            {
                "step_no": 1,
                "phase": "FINDING",
                "system_id": "search_service",
                "resource_id": "search_replica_881",
                "operation": "REPORT_REMAINING_RECORD",
                "state": "PRESENT",
                "evidence_id": "evidence_synthetic_replica",
            },
            {
                "step_no": 2,
                "phase": "REMEDIATION",
                "system_id": "search_service",
                "resource_id": "search_replica_881",
                "operation": "DELETE_RECORD",
                "state": "ABSENT",
                "evidence_id": "",
            },
            {
                "step_no": 3,
                "phase": "VERIFICATION",
                "system_id": "account_service",
                "resource_id": "account_synth_01",
                "operation": "VERIFY_RECORD_ABSENT",
                "state": "ABSENT",
                "evidence_id": "",
            },
            {
                "step_no": 4,
                "phase": "VERIFICATION",
                "system_id": "search_service",
                "resource_id": "search_replica_881",
                "operation": "VERIFY_RECORD_ABSENT",
                "state": "ABSENT",
                "evidence_id": "",
            },
            {
                "step_no": 5,
                "phase": "VERIFICATION",
                "system_id": "security_service",
                "resource_id": "audit_record_synth_01",
                "operation": "VERIFY_RECORD_PRESENT",
                "state": "PRESENT",
                "evidence_id": "",
            },
        ],
    ),
    SyntheticCase(
        case_id="synth_case_02",
        scenario_name="Tombstone PII Exposure via Historical Alias",
        description=(
            "User had a historical phone alias tracked in user_audit_log.csv. Primary account was purged, "
            "but identity_service tombstone retains raw phone number instead of hash/redaction. "
            "Must flag REPORT_EXPOSED_PII on identity_service, emit REDACT_RECORD, and verify redaction."
        ),
        request={
            "case_id": "synth_case_02",
            "email": "tombstone.pii.test@example.com",
            "requested_at": "2026-09-02T14:00:00Z",
            "reported_status": "PARTIALLY_COMPLETE",
            "reported_at": "2026-09-04T14:00:00Z",
            "audit_at": "2026-09-18T09:00:00Z",
            "request_text": "I demand the immediate deletion of my user account and all personal data under privacy law.",
        },
        expected_status="INCOMPLETE",
        expected_steps=[
            {
                "step_no": 1,
                "phase": "FINDING",
                "system_id": "identity_service",
                "resource_id": "tombstone_synth_02",
                "operation": "REPORT_EXPOSED_PII",
                "state": "PRESENT",
                "evidence_id": "evidence_synthetic_tombstone",
            },
            {
                "step_no": 2,
                "phase": "REMEDIATION",
                "system_id": "identity_service",
                "resource_id": "tombstone_synth_02",
                "operation": "REDACT_RECORD",
                "state": "REDACTED",
                "evidence_id": "",
            },
            {
                "step_no": 3,
                "phase": "VERIFICATION",
                "system_id": "account_service",
                "resource_id": "account_synth_02",
                "operation": "VERIFY_RECORD_ABSENT",
                "state": "ABSENT",
                "evidence_id": "",
            },
            {
                "step_no": 4,
                "phase": "VERIFICATION",
                "system_id": "security_service",
                "resource_id": "audit_record_synth_02",
                "operation": "VERIFY_RECORD_PRESENT",
                "state": "PRESENT",
                "evidence_id": "",
            },
            {
                "step_no": 5,
                "phase": "VERIFICATION",
                "system_id": "identity_service",
                "resource_id": "tombstone_synth_02",
                "operation": "VERIFY_RECORD_REDACTED",
                "state": "REDACTED",
                "evidence_id": "",
            },
        ],
    ),
    SyntheticCase(
        case_id="synth_case_03",
        scenario_name="Deceptive Non-Deletion Request (Subject Access Request)",
        description=(
            "User submits a GDPR Article 15 Subject Access Request asking for an export of all their data, "
            "orders, and invoices. No deletion intent is expressed. "
            "Pipeline must classify as NOT_APPLICABLE and output exactly 0 steps."
        ),
        request={
            "case_id": "synth_case_03",
            "email": "data.access.request@example.com",
            "requested_at": "2026-09-05T08:00:00Z",
            "reported_status": "NOT_STARTED",
            "reported_at": "2026-09-07T08:00:00Z",
            "audit_at": "2026-09-20T12:00:00Z",
            "request_text": "Hello, pursuant to Article 15 GDPR, please send me a machine-readable copy of all personal data, purchases, and browsing history associated with my account. Do not close or delete my account as I intend to keep shopping.",
        },
        expected_status="NOT_APPLICABLE",
        expected_steps=[],
    ),
    SyntheticCase(
        case_id="synth_case_04",
        scenario_name="Concurrent Restore Risk & Active Integration Connector",
        description=(
            "User deletion request processed, but backup service archive remains eligible for restore "
            "and integration service connector is still actively streaming customer events. "
            "Must detect restore risk and active data flow, emit BLOCK_RESTORE and DISABLE_DATA_FLOW, "
            "and verify all systems post-remediation."
        ),
        request={
            "case_id": "synth_case_04",
            "email": "restore.risk.test@example.com",
            "requested_at": "2026-09-07T11:00:00Z",
            "reported_status": "COMPLETE",
            "reported_at": "2026-09-09T11:00:00Z",
            "audit_at": "2026-09-22T15:00:00Z",
            "request_text": "I am requesting permanent deletion of my account. Please remove all records.",
        },
        expected_status="INCOMPLETE",
        expected_steps=[
            {
                "step_no": 1,
                "phase": "FINDING",
                "system_id": "integration_service",
                "resource_id": "data_flow_synth_04",
                "operation": "REPORT_ACTIVE_DATA_FLOW",
                "state": "ACTIVE",
                "evidence_id": "evidence_synthetic_flow",
            },
            {
                "step_no": 2,
                "phase": "FINDING",
                "system_id": "backup_service",
                "resource_id": "backup_synth_04",
                "operation": "REPORT_RESTORE_RISK",
                "state": "ACTIVE",
                "evidence_id": "evidence_synthetic_backup",
            },
            {
                "step_no": 3,
                "phase": "REMEDIATION",
                "system_id": "integration_service",
                "resource_id": "data_flow_synth_04",
                "operation": "DISABLE_DATA_FLOW",
                "state": "DISABLED",
                "evidence_id": "",
            },
            {
                "step_no": 4,
                "phase": "REMEDIATION",
                "system_id": "backup_service",
                "resource_id": "backup_synth_04",
                "operation": "BLOCK_RESTORE",
                "state": "BLOCKED",
                "evidence_id": "",
            },
            {
                "step_no": 5,
                "phase": "VERIFICATION",
                "system_id": "account_service",
                "resource_id": "account_synth_04",
                "operation": "VERIFY_RECORD_ABSENT",
                "state": "ABSENT",
                "evidence_id": "",
            },
            {
                "step_no": 6,
                "phase": "VERIFICATION",
                "system_id": "security_service",
                "resource_id": "audit_record_synth_04",
                "operation": "VERIFY_RECORD_PRESENT",
                "state": "PRESENT",
                "evidence_id": "",
            },
            {
                "step_no": 7,
                "phase": "VERIFICATION",
                "system_id": "integration_service",
                "resource_id": "data_flow_synth_04",
                "operation": "VERIFY_DATA_FLOW_DISABLED",
                "state": "DISABLED",
                "evidence_id": "",
            },
            {
                "step_no": 8,
                "phase": "VERIFICATION",
                "system_id": "backup_service",
                "resource_id": "backup_synth_04",
                "operation": "VERIFY_RESTORE_BLOCKED",
                "state": "BLOCKED",
                "evidence_id": "",
            },
        ],
    ),
]

def run_synthetic_tests() -> bool:
    print("=" * 75)
    print("ADVERSARIAL SYNTHETIC EVALUATION HARNESS")
    print(f"Total Custom Synthetic Test Cases: {len(SYNTHETIC_CASES)}")
    print("=" * 75)

    all_passed = True
    for case in SYNTHETIC_CASES:
        print(f"\nEvaluating {case.case_id}: {case.scenario_name}...")
        
        # 1. Intent Classification Check
        intent = classifier.classify(case.request["request_text"])
        if case.expected_status == "NOT_APPLICABLE":
            if intent != "NOT_APPLICABLE":
                print(f"  [FAIL] Expected intent NOT_APPLICABLE, got {intent}")
                all_passed = False
                continue
            pred_status, pred_steps = "NOT_APPLICABLE", []
        else:
            if intent != "AUTHORIZED_DELETION":
                print(f"  [FAIL] Expected intent AUTHORIZED_DELETION, got {intent}")
                all_passed = False
                continue

            # Simulate Policy Evaluation for synthetic scenario
            # Build synthetic CaseReconstruction
            res_dict = {}
            findings = []

            if case.case_id == "synth_case_01":
                acct = ResourceState("account_service", "account_synth_01", "USER_PROFILE", "ABSENT", verification_op="VERIFY_RECORD_ABSENT")
                search = ResourceState("search_service", "search_replica_881", "SEARCH_INDEX_ENTRY", "PRESENT",
                                       evidence_id="evidence_synthetic_replica", is_violation=True,
                                       finding_op="REPORT_REMAINING_RECORD", remediation_op="DELETE_RECORD",
                                       verification_op="VERIFY_RECORD_ABSENT")
                audit = ResourceState("security_service", "audit_record_synth_01", "SECURITY_AUDIT_LOG", "PRESENT", verification_op="VERIFY_RECORD_PRESENT")
                res_dict = {"account_synth_01": acct, "search_replica_881": search, "audit_record_synth_01": audit}
                findings = [search]

            elif case.case_id == "synth_case_02":
                acct = ResourceState("account_service", "account_synth_02", "USER_PROFILE", "ABSENT", verification_op="VERIFY_RECORD_ABSENT")
                tomb = ResourceState("identity_service", "tombstone_synth_02", "ACCOUNT_TOMBSTONE", "PRESENT",
                                     evidence_id="evidence_synthetic_tombstone", is_violation=True,
                                     finding_op="REPORT_EXPOSED_PII", remediation_op="REDACT_RECORD",
                                     verification_op="VERIFY_RECORD_REDACTED")
                audit = ResourceState("security_service", "audit_record_synth_02", "SECURITY_AUDIT_LOG", "PRESENT", verification_op="VERIFY_RECORD_PRESENT")
                res_dict = {"account_synth_02": acct, "tombstone_synth_02": tomb, "audit_record_synth_02": audit}
                findings = [tomb]

            elif case.case_id == "synth_case_04":
                acct = ResourceState("account_service", "account_synth_04", "USER_PROFILE", "ABSENT", verification_op="VERIFY_RECORD_ABSENT")
                flow = ResourceState("integration_service", "data_flow_synth_04", "DATA_FLOW", "ACTIVE",
                                     evidence_id="evidence_synthetic_flow", is_violation=True,
                                     finding_op="REPORT_ACTIVE_DATA_FLOW", remediation_op="DISABLE_DATA_FLOW",
                                     verification_op="VERIFY_DATA_FLOW_DISABLED")
                backup = ResourceState("backup_service", "backup_synth_04", "BACKUP_ARCHIVE", "ACTIVE",
                                       evidence_id="evidence_synthetic_backup", is_violation=True,
                                       finding_op="REPORT_RESTORE_RISK", remediation_op="BLOCK_RESTORE",
                                       verification_op="VERIFY_RESTORE_BLOCKED")
                audit = ResourceState("security_service", "audit_record_synth_04", "SECURITY_AUDIT_LOG", "PRESENT", verification_op="VERIFY_RECORD_PRESENT")
                res_dict = {"account_synth_04": acct, "data_flow_synth_04": flow, "backup_synth_04": backup, "audit_record_synth_04": audit}
                findings = [flow, backup]

            recon = CaseReconstruction(
                case_id=case.case_id,
                intent=intent,
                profile=None,
                account_resource_id=None,
                audit_resource_id=None,
                resources=res_dict,
                findings=findings,
            )
            pred_status, pred_steps = policy_engine.evaluate(recon)

        # Validate Status Match
        if pred_status != case.expected_status:
            print(f"  [FAIL] Status mismatch: expected {case.expected_status}, got {pred_status}")
            all_passed = False
            continue

        # Validate Steps Exact Match
        if pred_steps != case.expected_steps:
            print(f"  [FAIL] Steps mismatch:")
            print(f"    Expected: {json.dumps(case.expected_steps)}")
            print(f"    Got:      {json.dumps(pred_steps)}")
            all_passed = False
            continue

        print(f"  [PASS] Status '{pred_status}' and all {len(pred_steps)} steps perfectly matched.")

    print("\n" + "=" * 75)
    if all_passed:
        print("RESULT: ALL SYNTHETIC ADVERSARIAL CASES PASSED (100.0%)")
    else:
        print("RESULT: SYNTHETIC ADVERSARIAL EVALUATION FAILED")
    print("=" * 75)
    return all_passed

if __name__ == "__main__":
    success = run_synthetic_tests()
    sys.exit(0 if success else 1)
