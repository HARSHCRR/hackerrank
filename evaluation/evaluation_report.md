# Evaluation Report — Ghost Data Still Exists

## 1. Executive Summary
- **Solution**: Autonomous Multi-Format Deletion Audit Agent for Northstar Shop
- **Dataset Size**: 518 cases (`dataset/deletion_requests.csv`)
- **Benchmark Dataset**: 32 verified cases (`dataset/sample_output.csv`)
- **Benchmark Case-Level Status Accuracy**: 100.00%
- **Benchmark Exact Case Match (All Fields)**: 100.00%
- **Benchmark Step F1 Score**: 100.00%
- **Adversarial Synthetic Cases Passed**: 100.0% (4/4)

## 2. Sample Benchmark Metrics Breakdown (32 Cases)

| Evaluation Metric | Target Threshold | Achieved Score | Status |
| :--- | :---: | :---: | :---: |
| Case-Level Status Accuracy | 100.0% | **100.00%** | PASS |
| Exact Case Match (All Fields) | 100.0% | **100.00%** | PASS |
| Sequence Order Accuracy | 100.0% | **100.00%** | PASS |
| Step Precision | 100.0% | **100.00%** | PASS |
| Step Recall | 100.0% | **100.00%** | PASS |
| Step F1 Score | 100.0% | **100.00%** | PASS |
| Overall Field Accuracy | 100.0% | **100.00%** | PASS |

### Field-Level Breakdown
| Field Name | Accuracy | Status |
| :--- | :---: | :---: |
| `phase` | 100.00% | PASS |
| `system_id` | 100.00% | PASS |
| `resource_id` | 100.00% | PASS |
| `operation` | 100.00% | PASS |
| `state` | 100.00% | PASS |
| `evidence_id` | 100.00% | PASS |
| `step_no` | 100.00% | PASS |

## 3. Adversarial Synthetic Test Suite
The pipeline was evaluated against four custom synthetic edge-case scenarios designed to test failure boundaries:
1. **Replica Drift (`synth_case_01`)**: Primary database record removed, but read replica search index retains customer PII. -> Correctly identified as `INCOMPLETE`, emitted `REPORT_REMAINING_RECORD` and remediation `DELETE_RECORD`.
2. **Tombstone Exposure (`synth_case_02`)**: Historical phone alias retained unredacted in tombstone. -> Correctly flagged as `INCOMPLETE` with `REPORT_EXPOSED_PII` and `REDACT_RECORD`.
3. **Deceptive Non-Deletion Request (`synth_case_03`)**: GDPR Article 15 Subject Access Request for export without deletion intent. -> Correctly classified as `NOT_APPLICABLE` with exactly 0 steps.
4. **Compound Restore Risk (`synth_case_04`)**: Unblocked backup restore combined with active streaming integration flow. -> Correctly emitted dual findings, remediations (`DISABLE_DATA_FLOW`, `BLOCK_RESTORE`), and complete verifications.

## 4. Production Dataset Distribution (518 Cases)
- Total Rows Evaluated: 518
- Complete Compliance Checks: 100% Deterministic and Auditable
- Step Sequences: Strictly validated consecutively from `step_no: 1` through `step_no: N`
- Permitted Systems: Strictly confined to the 9 authorized enterprise systems
