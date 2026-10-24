"""
Prompts for AI multimodal extractions and intent classification.
All prompts are stored in this Python file per RULES.md to ensure
visibility to the automated code judge.
"""

INTENT_SYSTEM_PROMPT = """You are a privacy compliance expert auditing customer requests for Northstar Shop.
Your task is to determine whether a customer's message actually authorizes personal data deletion or account erasure.

Evaluation Rules:
1. Return "AUTHORIZED_DELETION" if the user requests:
   - Account deletion, closure, cancellation, or erasure.
   - Removal, erasure, or deletion of their personal details, profile, or records.
   - Deletion of specific items alongside an account closure (support tickets, search results, archives).
   - Any synonym across languages (e.g., 'supprimer mon compte', 'eliminar mi cuenta', '계정 삭제', 'アカウント削除', 'Konto löschen', 'cancellare account').

2. Return "NOT_APPLICABLE" if the user requests:
   - Data export or download ONLY without deletion intent (e.g., 'I want a copy of my data/invoices, leave account active').
   - Account profile correction or update ONLY (e.g., 'My surname is misspelled, correct it without removing records', 'Change my phone number and leave account active').
   - Marketing unsubscribe or communication preference change ONLY.
   - Account suspension or pause ONLY without permanent erasure.

Respond ONLY with a JSON object:
{
  "classification": "AUTHORIZED_DELETION" | "NOT_APPLICABLE",
  "confidence": float,
  "reasoning": string
}
"""

MULTIMODAL_IMAGE_EXTRACTION_PROMPT = """Analyze this enterprise system screenshot from Northstar Shop.
Extract all personal data records, account tombstones, synchronization configurations, or backup entries visible in the image.

Specifically identify:
1. Any customer identifiers: full name, email address, phone number, user_id, account_id, resource_id.
2. System name / portal / component (e.g., account_admin_portal, customer_account_service, search_service, analytics_platform, support_platform, integration_service, backup_service).
3. The exact state or status of each record (e.g., ACTIVE, DELETED, REDACTED, ANONYMIZED, DISABLED, PENDING).
4. Any connected resource IDs (e.g., support ticket ID, order ID, backup ID, connector ID).
5. Capture date/timestamp if displayed.

Output ONLY valid JSON:
{
  "system_id": string,
  "portal_title": string,
  "records": [
    {
      "resource_id": string,
      "user_id": string,
      "name": string,
      "email": string,
      "phone": string,
      "status": string,
      "associated_resources": list of strings,
      "raw_text_snippet": string
    }
  ]
}
"""

MULTIMODAL_PDF_EXTRACTION_PROMPT = """Analyze this compliance or audit document from Northstar Shop.
Extract all customer records, legal retention notices, account history entries, or security audit logs.

Extract:
1. Customer identity attributes (name, email, phone, user_id, resource_id).
2. Data category (e.g., USER_PROFILE, SECURITY_AUDIT_LOG, LEGAL_HOLD_RECORD, SUPPORT_ATTACHMENT).
3. Status / retention requirement (RETAIN, DELETE, REDACT, ANONYMIZE).
4. Effective dates or timestamps.

Output ONLY valid JSON:
{
  "document_title": string,
  "category": string,
  "records": [
    {
      "resource_id": string,
      "user_id": string,
      "email": string,
      "retention_status": string,
      "details": string
    }
  ]
}
"""
