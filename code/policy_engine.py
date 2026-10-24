#!/usr/bin/env python3
"""
Policy Engine for HackerRank Orchestrate: Ghost Data Still Exists.
Applies deletion_rules.csv, generates findings, remediations, and verifications,
and formats strictly ordered steps_json complying with problem_statement.md.
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    from code.state_reconstructor import CaseReconstruction, ResourceState
except ImportError:
    from .state_reconstructor import CaseReconstruction, ResourceState

# Canonical Operation Rankings within each Phase (from problem_statement.md)
FINDING_ORDER = {
    "REPORT_REMAINING_RECORD": 1,
    "REPORT_EXPOSED_PII": 2,
    "REPORT_ACTIVE_DATA_FLOW": 3,
    "REPORT_RESTORE_RISK": 4,
}

REMEDIATION_ORDER = {
    "DISABLE_DATA_FLOW": 1,
    "BLOCK_RESTORE": 2,
    "DELETE_RECORD": 3,
    "REDACT_RECORD": 4,
    "ANONYMIZE_RECORD": 5,
}

VERIFICATION_ORDER = {
    "VERIFY_RECORD_ABSENT": 1,
    "VERIFY_RECORD_PRESENT": 2,
    "VERIFY_RECORD_REDACTED": 3,
    "VERIFY_RECORD_ANONYMIZED": 4,
    "VERIFY_DATA_FLOW_DISABLED": 5,
    "VERIFY_RESTORE_BLOCKED": 6,
}

PHASE_ORDER = {
    "FINDING": 1,
    "REMEDIATION": 2,
    "VERIFICATION": 3,
}

OPERATION_STATES = {
    "REPORT_REMAINING_RECORD": "PRESENT",
    "REPORT_EXPOSED_PII": "PRESENT",
    "REPORT_ACTIVE_DATA_FLOW": "ACTIVE",
    "REPORT_RESTORE_RISK": "ACTIVE",
    "DISABLE_DATA_FLOW": "DISABLED",
    "BLOCK_RESTORE": "BLOCKED",
    "DELETE_RECORD": "ABSENT",
    "REDACT_RECORD": "REDACTED",
    "ANONYMIZE_RECORD": "ANONYMIZED",
    "VERIFY_RECORD_ABSENT": "ABSENT",
    "VERIFY_RECORD_PRESENT": "PRESENT",
    "VERIFY_RECORD_REDACTED": "REDACTED",
    "VERIFY_RECORD_ANONYMIZED": "ANONYMIZED",
    "VERIFY_DATA_FLOW_DISABLED": "DISABLED",
    "VERIFY_RESTORE_BLOCKED": "BLOCKED",
}

class PolicyEngine:
    def evaluate(self, reconstruction: CaseReconstruction) -> Tuple[str, List[Dict]]:
        # Non-deletion request -> NOT_APPLICABLE
        if reconstruction.intent == "NOT_APPLICABLE":
            return "NOT_APPLICABLE", []

        raw_steps = []
        is_incomplete = len(reconstruction.findings) > 0

        if is_incomplete:
            status = "INCOMPLETE"
            # 1. FINDINGS Phase
            for res in reconstruction.findings:
                raw_steps.append({
                    "phase": "FINDING",
                    "system_id": res.system_id,
                    "resource_id": res.resource_id,
                    "operation": res.finding_op,
                    "state": OPERATION_STATES[res.finding_op],
                    "evidence_id": res.evidence_id,
                })

            # 2. REMEDIATION Phase
            for res in reconstruction.findings:
                raw_steps.append({
                    "phase": "REMEDIATION",
                    "system_id": res.system_id,
                    "resource_id": res.resource_id,
                    "operation": res.remediation_op,
                    "state": OPERATION_STATES[res.remediation_op],
                    "evidence_id": "",
                })

            # 3. VERIFICATION Phase (Post-remediation)
            # Must verify all resources associated with the case
            for res in reconstruction.resources.values():
                raw_steps.append({
                    "phase": "VERIFICATION",
                    "system_id": res.system_id,
                    "resource_id": res.resource_id,
                    "operation": res.verification_op,
                    "state": OPERATION_STATES[res.verification_op],
                    "evidence_id": "",
                })

        else:
            status = "COMPLETE"
            # Only VERIFICATION Phase
            for res in reconstruction.resources.values():
                raw_steps.append({
                    "phase": "VERIFICATION",
                    "system_id": res.system_id,
                    "resource_id": res.resource_id,
                    "operation": res.verification_op,
                    "state": OPERATION_STATES[res.verification_op],
                    "evidence_id": res.evidence_id,
                })

        # Canonical Sorting
        def sort_key(s):
            ph_rank = PHASE_ORDER[s["phase"]]
            if s["phase"] == "FINDING":
                op_rank = FINDING_ORDER.get(s["operation"], 99)
            elif s["phase"] == "REMEDIATION":
                op_rank = REMEDIATION_ORDER.get(s["operation"], 99)
            else:
                op_rank = VERIFICATION_ORDER.get(s["operation"], 99)
            return (ph_rank, op_rank, s["system_id"], s["resource_id"])

        sorted_steps = sorted(raw_steps, key=sort_key)

        # Number steps consecutively starting at 1
        final_steps = []
        for idx, s in enumerate(sorted_steps, 1):
            step_dict = {
                "step_no": idx,
                "phase": s["phase"],
                "system_id": s["system_id"],
                "resource_id": s["resource_id"],
                "operation": s["operation"],
                "state": s["state"],
                "evidence_id": s["evidence_id"],
            }
            final_steps.append(step_dict)

        return status, final_steps

policy_engine = PolicyEngine()
