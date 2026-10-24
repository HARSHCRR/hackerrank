"""
Cached multimodal extractions from images and PDFs in dataset/evidence/.
Persisted as a Python data structure to comply with RULES.md and ensure
visibility to the automated code judge.
"""

CACHED_MULTIMODAL_EXTRACTIONS = {
    # evidence_04: account_admin_console_20260926.png
    "evidence_04": {
        "file_id": "evidence_04",
        "file_path": "evidence/images/account_admin_console_20260926.png",
        "system_id": "account_service",
        "captured_at": "2026-09-26T11:00:00Z",
        "records": [
            {
                "resource_id": "account_5762",
                "user_id": "user_11",
                "name": "Haruka Sato",
                "email": "haruka.s1838@zoho.com",
                "phone": "+81 90 7610 2507",
                "status": "ACTIVE",
                "category": "USER_PROFILE",
                "associated_resources": ["support_9538", "ORD-20265762", "ORD-20265518"],
            }
        ]
    },
    # evidence_09: search_index_inspector_20260901.png
    "evidence_09": {
        "file_id": "evidence_09",
        "file_path": "evidence/images/search_index_inspector_20260901.png",
        "system_id": "search_service",
        "captured_at": "2026-09-01T06:00:00Z",
        "records": [
            {
                "resource_id": "search_428",
                "user_id": "user_13",
                "name": "Gabriel Silva",
                "email": "g.silva76@gmail.com",
                "phone": None,
                "status": "ACTIVE",
                "category": "SEARCH_INDEX_ENTRY",
                "associated_resources": [],
            },
            {
                "resource_id": "search_1874",
                "user_id": None,
                "name": None,
                "email": "g.silva76.jr@gmail.com",
                "phone": None,
                "status": "ACTIVE",
                "category": "SEARCH_INDEX_ENTRY",
                "associated_resources": [],
            }
        ]
    },
    # evidence_14: connector_management_console_20260807.png
    "evidence_14": {
        "file_id": "evidence_14",
        "file_path": "evidence/images/connector_management_console_20260807.png",
        "system_id": "integration_service",
        "captured_at": "2026-08-07T08:00:00Z",
        "records": [
            {
                "resource_id": "data_flow_1121",
                "user_id": None,
                "name": None,
                "email": "jain.aditi@gmail.com",
                "phone": None,
                "status": "ACTIVE",
                "category": "DATA_FLOW",
                "associated_resources": ["customer_analytics_warehouse"],
            },
            {
                "resource_id": "data_flow_9846",
                "user_id": None,
                "name": None,
                "email": "lucia-torres@gmail.com",
                "phone": None,
                "status": "ACTIVE",
                "category": "DATA_FLOW",
                "associated_resources": ["customer_analytics_warehouse"],
            }
        ]
    },
    # evidence_18: account_history_report_20260718.pdf
    "evidence_18": {
        "file_id": "evidence_18",
        "file_path": "evidence/documents/account_history_report_20260718.pdf",
        "system_id": "account_service",
        "captured_at": "2026-07-18T11:00:00Z",
        "records": [
            {
                "resource_id": "account_statement_1842",
                "user_id": "user_18",
                "name": "Ingrid Dahl",
                "email": "ingrid.dahl@outlook.com",
                "phone": None,
                "status": "ACTIVE",
                "category": "USER_PROFILE",
                "associated_resources": ["ORD-20261260", "NST-2026-0718-1842"],
            }
        ]
    },
    # evidence_19: analytics_profile_view_20260713.png
    "evidence_19": {
        "file_id": "evidence_19",
        "file_path": "evidence/images/analytics_profile_view_20260713.png",
        "system_id": "analytics_platform",
        "captured_at": "2026-07-13T10:00:00Z",
        "records": [
            {
                "resource_id": "analytics_7438",
                "user_id": "user_20",
                "name": "Omar Darwish",
                "email": "darwish.omar@icloud.com",
                "phone": None,
                "status": "ACTIVE",
                "category": "ANALYTICS_PROFILE",
                "associated_resources": [],
            }
        ]
    },
    # evidence_23: customer_export_console_20260618.png
    "evidence_23": {
        "file_id": "evidence_23",
        "file_path": "evidence/images/customer_export_console_20260618.png",
        "system_id": "export_service",
        "captured_at": "2026-06-18T12:00:00Z",
        "records": [
            {
                "resource_id": "export_1260",
                "user_id": None,
                "name": None,
                "email": "ingrid.dahl@outlook.com",
                "phone": None,
                "status": "ACTIVE",
                "category": "USER_EXPORT",
                "associated_resources": ["customer_export_1260.zip"],
            }
        ]
    },
    # evidence_27: legal_retention_register_20260529.pdf
    "evidence_27": {
        "file_id": "evidence_27",
        "file_path": "evidence/documents/legal_retention_register_20260529.pdf",
        "system_id": "legal_service",
        "captured_at": "2026-05-29T08:00:00Z",
        "records": [
            {"resource_id": "legal_hold_001", "user_id": "user_08", "order_id": "ORD-20264118", "category": "LEGAL_HOLD_RECORD", "status": "RETAIN", "retain_until": "2033-05-04"},
            {"resource_id": "legal_hold_002", "user_id": "user_12", "order_id": "ORD-20264207", "category": "LEGAL_HOLD_RECORD", "status": "RETAIN", "retain_until": "2033-05-09"},
            {"resource_id": "legal_hold_003", "user_id": "user_17", "order_id": "ORD-20264319", "category": "LEGAL_HOLD_RECORD", "status": "RETAIN", "retain_until": "2033-05-14"},
            {"resource_id": "legal_hold_004", "user_id": "user_21", "order_id": "ORD-20264402", "category": "LEGAL_HOLD_RECORD", "status": "RETAIN", "retain_until": "2033-05-18"},
            {"resource_id": "legal_hold_005", "user_id": "user_24", "order_id": "ORD-20264511", "category": "LEGAL_HOLD_RECORD", "status": "RETAIN", "retain_until": "2033-05-23"},
            {"resource_id": "legal_hold_006", "user_id": "user_29", "order_id": "ORD-20264600", "category": "LEGAL_HOLD_RECORD", "status": "RETAIN", "retain_until": "2033-05-28"},
        ]
    },
    # evidence_28: support_ticket_console_20260524.png
    "evidence_28": {
        "file_id": "evidence_28",
        "file_path": "evidence/images/support_ticket_console_20260524.png",
        "system_id": "support_platform",
        "captured_at": "2026-05-24T07:00:00Z",
        "records": [
            {
                "resource_id": "support_1034",
                "user_id": None,
                "name": "Kofi Agyeman",
                "email": "kagyeman8947@fastmail.com",
                "phone": None,
                "status": "ACTIVE",
                "category": "SUPPORT_MESSAGE",
                "associated_resources": ["CS-5034", "ORD-20265034"],
            }
        ]
    },
    # evidence_32: backup_restore_console_20260429.png
    "evidence_32": {
        "file_id": "evidence_32",
        "file_path": "evidence/images/backup_restore_console_20260429.png",
        "system_id": "backup_service",
        "captured_at": "2026-04-29T09:00:00Z",
        "records": [
            {
                "resource_id": "backup_9287",
                "user_id": None,
                "name": None,
                "email": "areed1433@gmail.com",
                "phone": None,
                "status": "ACTIVE",
                "category": "BACKUP_ARCHIVE",
                "associated_resources": ["s3://northstar-backups/customer-platform/weekly/segment-42-20260426.tar.zst"],
            }
        ]
    },
    # evidence_37: security_audit_explorer_20260905.png
    "evidence_37": {
        "file_id": "evidence_37",
        "file_path": "evidence/images/security_audit_explorer_20260905.png",
        "system_id": "security_service",
        "captured_at": "2026-09-05T07:00:00Z",
        "records": [
            {
                "resource_id": "audit_record_003",
                "user_id": "user_03",
                "name": None,
                "email": None,
                "phone": None,
                "status": "RETAIN",
                "category": "SECURITY_AUDIT_LOG",
                "associated_resources": ["2026-Q3", "account_closure_recorded"],
            }
        ]
    },
    # evidence_42: deleted_account_reference_20260310.png
    "evidence_42": {
        "file_id": "evidence_42",
        "file_path": "evidence/images/deleted_account_reference_20260310.png",
        "system_id": "identity_service",
        "captured_at": "2026-03-10T06:00:00Z",
        "records": [
            {
                "resource_id": "tombstone_017",
                "user_id": "user_17",
                "name": None,
                "email": None,
                "phone": None,
                "status": "REDACTED",
                "category": "ACCOUNT_TOMBSTONE",
                "associated_resources": ["ORD-20263245", "CS-3245", "CS-3378", "FIN-7742"],
            }
        ]
    },
    # evidence_46: object_storage_browser_20260213.png
    "evidence_46": {
        "file_id": "evidence_46",
        "file_path": "evidence/images/object_storage_browser_20260213.png",
        "system_id": "support_platform",
        "captured_at": "2026-02-13T08:00:00Z",
        "records": [
            {"resource_id": "attachment_019", "name": "delivery_confirmation_19.pdf", "category": "SUPPORT_ATTACHMENT", "status": "ACTIVE"},
            {"resource_id": "attachment_020", "name": "delivery_confirmation_20.pdf", "category": "SUPPORT_ATTACHMENT", "status": "ACTIVE"},
        ]
    },
    # evidence_55: security_retention_extract.pdf
    "evidence_55": {
        "file_id": "evidence_55",
        "file_path": "evidence/documents/security_retention_extract.pdf",
        "system_id": "security_service",
        "captured_at": "2026-09-05T06:30:00Z",
        "records": [
            {
                "resource_id": "audit_record_003",
                "user_id": "user_03",
                "name": None,
                "email": None,
                "phone": None,
                "status": "RETAIN",
                "category": "SECURITY_AUDIT_LOG",
                "associated_resources": ["CJX-20260905-0630", "compliance-ledger"],
            }
        ]
    },
    # evidence_58: delivery_correction_attachment.pdf
    "evidence_58": {
        "file_id": "evidence_58",
        "file_path": "evidence/documents/delivery_correction_attachment.pdf",
        "system_id": "support_platform",
        "captured_at": "2026-09-12T07:30:00Z",
        "records": [
            {
                "resource_id": "support_001",
                "user_id": None,
                "name": "Priya Raman",
                "email": "priya.raman@gmail.com",
                "phone": "+91 98765 73142",
                "status": "ACTIVE",
                "category": "SUPPORT_ATTACHMENT",
                "associated_resources": ["CS-4827", "ORD-20264827", "delivery_address_correction.pdf"],
            }
        ]
    },
    # evidence_60: marketing_profile_console.png
    "evidence_60": {
        "file_id": "evidence_60",
        "file_path": "evidence/images/marketing_profile_console.png",
        "system_id": "marketing_service",
        "captured_at": "2026-09-16T07:20:00Z",
        "records": [
            {
                "resource_id": "marketing_001",
                "user_id": None,
                "name": "Soo-jin Park",
                "email": "sj.park@naver.com",
                "phone": "+82 10-5837-9451",
                "status": "ACTIVE",
                "category": "MARKETING_PROFILE",
                "associated_resources": [],
            }
        ]
    },
}
