#!/usr/bin/env python3
"""
Global Evidence Indexer for HackerRank Orchestrate: Ghost Data Still Exists.
Parses all SQL, JSON, log, text, PDF, and image evidence under dataset/evidence/
mapped to evidence_files.csv, plus operational events in system_activity.csv.
"""

import csv
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Set

try:
    from code.config import DATASET_DIR, EVIDENCE_DIR
    from code.cached_extractions import CACHED_MULTIMODAL_EXTRACTIONS
except ImportError:
    from .config import DATASET_DIR, EVIDENCE_DIR
    from .cached_extractions import CACHED_MULTIMODAL_EXTRACTIONS

class EvidenceIndexer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EvidenceIndexer, cls).__new__(cls)
            cls._instance.is_indexed = False
            cls._instance.records = []
            cls._instance.file_manifest = {}
            cls._instance.records_by_resource = defaultdict(list)
            cls._instance.records_by_user_id = defaultdict(list)
            cls._instance.records_by_email = defaultdict(list)
            cls._instance.records_by_correlation_key = defaultdict(list)
            cls._instance.system_activities = []
            cls._instance.activities_by_resource = defaultdict(list)
        return cls._instance

    def load_manifest(self):
        manifest_path = DATASET_DIR / "evidence_files.csv"
        with open(manifest_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.file_manifest[row["file_id"]] = {
                    "file_id": row["file_id"],
                    "file_path": row["file_path"],
                    "origin": row["origin"],
                    "captured_at": row["captured_at"],
                }

    def load_system_activity(self):
        act_path = DATASET_DIR / "system_activity.csv"
        with open(act_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self.system_activities = list(reader)
            for act in self.system_activities:
                rid = act.get("resource_id")
                if rid:
                    self.activities_by_resource[rid].append(act)

    def index_all(self, force=False):
        if self.is_indexed and not force:
            return self

        self.load_manifest()
        self.load_system_activity()
        self.records.clear()
        self.records_by_resource.clear()
        self.records_by_user_id.clear()
        self.records_by_email.clear()
        self.records_by_correlation_key.clear()

        for file_id, meta in self.file_manifest.items():
            rel_path = meta["file_path"]
            full_path = DATASET_DIR / rel_path
            captured_at = meta["captured_at"]
            origin = meta["origin"]

            ext = rel_path.split(".")[-1].lower()
            if ext == "sql":
                self._parse_sql(file_id, full_path, captured_at, origin)
            elif ext == "json":
                self._parse_json(file_id, full_path, captured_at, origin)
            elif ext == "log":
                self._parse_log(file_id, full_path, captured_at, origin)
            elif ext == "txt":
                self._parse_txt(file_id, full_path, captured_at, origin)
            elif ext in ["png", "pdf"]:
                self._parse_multimodal(file_id, full_path, captured_at, origin)

        self.is_indexed = True
        return self

    def _add_record(self, record):
        self.records.append(record)
        rid = record.get("resource_id")
        if rid:
            self.records_by_resource[rid].append(record)
        uid = record.get("user_id")
        if uid:
            self.records_by_user_id[uid.lower()].append(record)
        email = record.get("email")
        if email:
            self.records_by_email[email.lower()].append(record)
        ck = record.get("correlation_key")
        if ck:
            self.records_by_correlation_key[ck.lower()].append(record)

    def _parse_sql(self, file_id, full_path, captured_at, origin):
        with open(full_path, "r", encoding="utf-8") as f:
            sql_text = f.read()

        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(sql_text)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cursor.fetchall()]

            for tbl in tables:
                cursor.execute(f"PRAGMA table_info('{tbl}');")
                cols = [c[1] for c in cursor.fetchall()]
                cursor.execute(f"SELECT * FROM '{tbl}';")
                rows = cursor.fetchall()
                for r in rows:
                    row_dict = dict(zip(cols, r))
                    system_id = self._infer_system_from_table(tbl, row_dict)

                    # Extract record_json if present (e.g. replica tables)
                    rjson_str = row_dict.get("record_json")
                    if rjson_str:
                        try:
                            rjson = json.loads(rjson_str)
                            doc = rjson.get("document", {}) if isinstance(rjson, dict) else {}
                            uid = rjson.get("customer_reference") or rjson.get("user_id") or rjson.get("subject_reference") or doc.get("customer_reference") or doc.get("user_id") or doc.get("subject_reference")
                            em = rjson.get("email") or rjson.get("customer_email") or rjson.get("owner_email") or doc.get("email") or doc.get("customer_email") or doc.get("owner_email")
                            nm = rjson.get("full_name") or rjson.get("display_name") or doc.get("display_name") or doc.get("full_name")
                            ph = rjson.get("phone") or doc.get("phone")
                            
                            rec = {
                                "file_id": file_id,
                                "captured_at": captured_at,
                                "origin": origin,
                                "system_id": self._infer_system_from_resource(rjson.get("resource_id") or row_dict.get("resource_id")),
                                "table_name": tbl,
                                "resource_id": rjson.get("resource_id") or row_dict.get("resource_id"),
                                "user_id": uid,
                                "email": em,
                                "name": nm,
                                "phone": ph,
                                "status": rjson.get("account_status") or rjson.get("status") or ("PRESENT" if (em or uid) else "ANONYMIZED"),
                                "raw_data": rjson,
                            }
                            self._add_record(rec)
                            continue
                        except Exception:
                            pass

                    # Direct columns
                    user_id = row_dict.get("user_id") or row_dict.get("customer_reference") or row_dict.get("subject_reference")
                    email = row_dict.get("email") or row_dict.get("customer_email") or row_dict.get("owner_email") or row_dict.get("requester_email")
                    name = row_dict.get("full_name") or row_dict.get("display_name") or row_dict.get("requester_name")
                    phone = row_dict.get("phone") or row_dict.get("owner_phone") or row_dict.get("requester_phone")
                    
                    status = "PRESENT"
                    if "status_code" in row_dict and row_dict["status_code"] == 404:
                        status = "ABSENT"
                    elif "account_status" in row_dict:
                        status = row_dict["account_status"]
                    elif "enabled" in row_dict:
                        status = "ACTIVE" if row_dict["enabled"] in (1, "1", True) else "DISABLED"
                    elif "restore_allowed" in row_dict:
                        status = "ACTIVE" if row_dict["restore_allowed"] in (1, "1", True) else "BLOCKED"
                    elif "retention_until" in row_dict:
                        status = "RETAIN"

                    rec = {
                        "file_id": file_id,
                        "captured_at": captured_at,
                        "origin": origin,
                        "system_id": system_id,
                        "table_name": tbl,
                        "resource_id": row_dict.get("resource_id"),
                        "user_id": user_id,
                        "email": email,
                        "name": name,
                        "phone": phone,
                        "status": status,
                        "raw_data": row_dict,
                    }
                    self._add_record(rec)
        finally:
            conn.close()

    def _infer_system_from_table(self, tbl, row):
        if "profile" in tbl or "account" in tbl:
            return "account_service"
        if "search" in tbl:
            return "search_service"
        if "analytics" in tbl:
            return "analytics_platform"
        if "support" in tbl:
            return "support_platform"
        if "backup" in tbl:
            return "backup_service"
        if "connector" in tbl:
            return "integration_service"
        if "audit" in tbl or "security" in tbl:
            return "security_service"
        if "export" in tbl:
            return "export_service"
        return "account_service"

    def _infer_system_from_resource(self, rid):
        if not rid:
            return "account_service"
        if rid.startswith("account_"):
            return "account_service"
        if rid.startswith("search_"):
            return "search_service"
        if rid.startswith("analytics_"):
            return "analytics_platform"
        if rid.startswith("support_"):
            return "support_platform"
        if rid.startswith("backup_"):
            return "backup_service"
        if rid.startswith("data_flow_"):
            return "integration_service"
        if rid.startswith("audit_record_"):
            return "security_service"
        if rid.startswith("export_"):
            return "export_service"
        if rid.startswith("tombstone_"):
            return "identity_service"
        return "account_service"

    def _parse_json(self, file_id, full_path, captured_at, origin):
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. Service resource exports (e.g. evidence_92)
        if "service_exports" in data:
            for svc_name, svc_data in data["service_exports"].items():
                if isinstance(svc_data, dict):
                    for subk, items in svc_data.items():
                        if isinstance(items, list):
                            for it in items:
                                rid = it.get("resource_id")
                                obs_at = it.get("observed_at", captured_at)
                                prof = it.get("profile") if isinstance(it.get("profile"), dict) else {}
                                uid = it.get("customer_reference") or it.get("subject_reference") or it.get("user_id") or prof.get("customer_reference") or prof.get("user_id")
                                email = it.get("email") or it.get("customer_email") or it.get("owner_email") or it.get("requester_email") or it.get("query") or prof.get("email")
                                name = it.get("requester_name") or it.get("full_name") or it.get("display_name") or prof.get("full_name")
                                phone = it.get("requester_phone") or it.get("phone") or it.get("owner_phone") or prof.get("phone")
                                
                                status = "PRESENT"
                                if it.get("status_code") == 404:
                                    status = "ABSENT"
                                elif "enabled" in it:
                                    status = "ACTIVE" if it.get("enabled") else "DISABLED"
                                elif "restore_allowed" in it:
                                    status = "ACTIVE" if it.get("restore_allowed") else "BLOCKED"
                                elif "retention_until" in it:
                                    status = "RETAIN"
                                elif svc_name == "analytics_platform":
                                    status = "ANONYMIZED" if not (email or phone or it.get("email_hash") or uid) else "PRESENT"
                                elif svc_name == "support_platform":
                                    status = "REDACTED" if not (email or name or phone) else "PRESENT"
                                elif svc_name == "search_service":
                                    hits = it.get("hits", {})
                                    status = "PRESENT" if hits.get("total", 0) > 0 else "ABSENT"

                                rec = {
                                    "file_id": file_id,
                                    "captured_at": obs_at,
                                    "origin": origin,
                                    "system_id": svc_name,
                                    "resource_id": rid,
                                    "user_id": uid,
                                    "email": email,
                                    "name": name,
                                    "phone": phone,
                                    "status": status,
                                    "raw_data": it,
                                }
                                self._add_record(rec)

        # 2. Snapshot bundles
        elif "snapshots" in data:
            for snap in data["snapshots"]:
                data_store = snap.get("data_store", "account_service")
                snap_time = snap.get("captured_at", captured_at)
                for item in snap.get("records", []):
                    doc = item.get("document", {})
                    uid = item.get("subject_reference") or item.get("customer_reference") or item.get("user_id") or doc.get("subject_reference") or doc.get("customer_reference") or doc.get("user_id")
                    em = item.get("email") or doc.get("email")
                    stat = item.get("account_status") or "PRESENT"
                    if data_store == "identity_service":
                        stat = "IDENTIFIABLE" if (item.get("email") or item.get("phone") or item.get("name") or item.get("email_hash")) else "REDACTED"
                    elif data_store == "security_service":
                        stat = "PRESENT"

                    rec = {
                        "file_id": file_id,
                        "captured_at": snap_time,
                        "origin": origin,
                        "system_id": data_store,
                        "resource_id": item.get("resource_id"),
                        "user_id": uid,
                        "email": em,
                        "name": item.get("full_name") or doc.get("display_name"),
                        "phone": item.get("phone"),
                        "status": stat,
                        "raw_data": item,
                    }
                    self._add_record(rec)

        # 3. Direct records array
        elif "records" in data and isinstance(data["records"], list):
            for item in data["records"]:
                sys_id = item.get("system") or self._infer_system_from_resource(item.get("resource_id"))
                sub_ref = item.get("subject_reference") or item.get("user_id") or item.get("customer_reference")
                email = item.get("email") or item.get("owner_email") or (sub_ref if sub_ref and "@" in sub_ref else None)
                uid = item.get("user_id") or (sub_ref if sub_ref and sub_ref.startswith("user_") else None)
                status = "PRESENT"
                if item.get("result") == "NOT_FOUND":
                    status = "ABSENT"
                elif item.get("result") == "FOUND":
                    status = "PRESENT"
                elif sys_id == "analytics_platform":
                    status = "ANONYMIZED" if not (email or item.get("phone") or item.get("email_hash") or uid) else "PRESENT"

                rec = {
                    "file_id": file_id,
                    "captured_at": item.get("recorded_at") or data.get("captured_at") or data.get("exported_at", captured_at),
                    "origin": origin,
                    "system_id": sys_id,
                    "resource_id": item.get("resource_id"),
                    "user_id": uid,
                    "email": email,
                    "name": None,
                    "phone": item.get("phone"),
                    "status": status,
                    "raw_data": item,
                }
                self._add_record(rec)

    def _parse_log(self, file_id, full_path, captured_at, origin):
        traces = defaultdict(dict)
        with open(full_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                ts_match = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", line)
                ev_time = ts_match.group(1) if ts_match else captured_at

                # Check if line contains a JSON payload
                json_idx = line.find("{")
                json_data = None
                if json_idx != -1 and line.endswith("}"):
                    try:
                        json_data = json.loads(line[json_idx:])
                    except Exception:
                        json_data = None

                if json_data:
                    system_id = json_data.get("service") or json_data.get("logger")
                    resource_id = json_data.get("resource_id")
                    user_id = json_data.get("subject_ref") or json_data.get("customer_reference") or json_data.get("user_id")
                    email = json_data.get("email") or json_data.get("customer_email") or json_data.get("requester_email")
                    lk = json_data.get("lookup_key")
                    if lk:
                        if "@" in lk:
                            email = lk
                        elif lk.startswith("user_"):
                            user_id = lk
                    correlation_key = json_data.get("correlation_key")
                    event_name = json_data.get("event", "log_event")
                    trace_id = json_data.get("trace_id") or json_data.get("requestId")

                    status = None
                    rows = json_data.get("rows")
                    hstat = json_data.get("http_status") or json_data.get("status_code")
                    if rows in (0, "0") or hstat in (404, "404"):
                        status = "ABSENT"
                    elif rows in (1, "1") or hstat in (200, "200"):
                        status = "PRESENT"
                    elif json_data.get("restore_allowed") is False or json_data.get("deletion_block") is True:
                        status = "BLOCKED"
                    elif json_data.get("restore_allowed") is True or json_data.get("deletion_block") is False:
                        status = "ACTIVE"
                    elif json_data.get("enabled") is False:
                        status = "DISABLED"
                    elif json_data.get("enabled") is True:
                        status = "ACTIVE"
                    elif json_data.get("retention_until") or json_data.get("event_code") == "IDENTITY_CHANGE_RECORDED":
                        status = "RETAIN"
                    elif event_name == "audit_record_read_completed":
                        status = "RETAIN"
                else:
                    svc_match = re.search(r"service=([a-zA-Z0-9_]+)", line)
                    system_id = svc_match.group(1) if svc_match else None

                    res_match = re.search(r"resource_id=([a-zA-Z0-9_]+)", line)
                    resource_id = res_match.group(1) if res_match else None

                    email_match = re.search(r'[\"\']?([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)[\"\']?', line)
                    email = email_match.group(1) if email_match else None

                    user_match = re.search(r'\b(user_\d+)\b', line)
                    user_id = user_match.group(1) if user_match else None

                    ck_match = re.search(r'correlation_key=[\"\']([^\"\']+)[\"\']', line)
                    correlation_key = ck_match.group(1) if ck_match else None

                    lk_match = re.search(r'lookup_key=[\"\']?([a-zA-Z0-9_.+@-]+)[\"\']?', line)
                    if lk_match:
                        lk = lk_match.group(1)
                        if "@" in lk:
                            email = lk
                        elif lk.startswith("user_"):
                            user_id = lk

                    event_match = re.search(r"event=([a-zA-Z0-9_]+)", line)
                    event_name = event_match.group(1) if event_match else "log_event"

                    status = None
                    if "http_status=404" in line or "rows=0" in line:
                        status = "ABSENT"
                    elif "enabled=false" in line or "last_delivery_status=stopped" in line:
                        status = "DISABLED"
                    elif "enabled=true" in line:
                        status = "ACTIVE"
                    elif "deletion_block=false" in line or "restore_allowed=true" in line:
                        status = "ACTIVE"
                    elif "deletion_block=true" in line or "restore_allowed=false" in line:
                        status = "BLOCKED"
                    elif "retention_until" in line or "event_code=IDENTITY_CHANGE_RECORDED" in line or "audit_record_read_completed" in line:
                        status = "RETAIN"
                    elif "analytics_profile_read_completed" in line:
                        status = "ANONYMIZED" if "email=null" in line and "phone=null" in line else "PRESENT"
                    elif "support_ticket_read_completed" in line:
                        status = "REDACTED" if "requester_email=null" in line and "requester_phone=null" in line else "PRESENT"
                    elif "http_status=200" in line or "rows=1" in line or "result=hit" in line:
                        status = "PRESENT"

                    trace_match = re.search(r'(?:trace_id|requestId)=[\"\']?([a-zA-Z0-9_\-]+)[\"\']?', line)
                    trace_id = trace_match.group(1) if trace_match else None

                if trace_id:
                    t = traces[trace_id]
                    t["captured_at"] = max(t.get("captured_at", ""), ev_time)
                    if system_id:
                        t["system_id"] = system_id
                    if resource_id:
                        t["resource_id"] = resource_id
                    if email:
                        t["email"] = email
                    if user_id:
                        t["user_id"] = user_id
                    if correlation_key:
                        t["correlation_key"] = correlation_key
                    if status:
                        t["status"] = status
                    t["event_name"] = event_name
                    t["raw_line"] = line
                else:
                    if resource_id or email or user_id or correlation_key:
                        rec = {
                            "file_id": file_id,
                            "captured_at": ev_time,
                            "origin": origin,
                            "system_id": (system_id if system_id and system_id != "readback_collector" else self._infer_system_from_resource(resource_id)),
                            "resource_id": resource_id,
                            "user_id": user_id,
                            "email": email,
                            "correlation_key": correlation_key,
                            "name": None,
                            "phone": None,
                            "status": status or "PRESENT",
                            "event_name": event_name,
                            "raw_line": line,
                        }
                        self._add_record(rec)

        for trace_id, t in traces.items():
            rid = t.get("resource_id")
            uid = t.get("user_id")
            em = t.get("email")
            ck = t.get("correlation_key")
            sys_id = t.get("system_id") or self._infer_system_from_resource(rid)
            if sys_id == "readback_collector":
                sys_id = self._infer_system_from_resource(rid)

            if rid or uid or em or ck:
                rec = {
                    "file_id": file_id,
                    "captured_at": t.get("captured_at", captured_at),
                    "origin": origin,
                    "system_id": sys_id,
                    "resource_id": rid,
                    "user_id": uid,
                    "email": em,
                    "correlation_key": ck,
                    "name": None,
                    "phone": None,
                    "status": t.get("status", "PRESENT"),
                    "event_name": t.get("event_name", "log_event"),
                    "raw_line": t.get("raw_line", ""),
                }
                self._add_record(rec)

    def _parse_txt(self, file_id, full_path, captured_at, origin):
        with open(full_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("- "):
                    parts = [p.strip() for p in line[2:].split("|")]
                    if len(parts) >= 6:
                        ts, sys_id, res_id, cat, status, ident = parts[:6]
                        rec = {
                            "file_id": file_id,
                            "captured_at": ts,
                            "origin": origin,
                            "system_id": sys_id,
                            "resource_id": res_id,
                            "user_id": ident if ident.startswith("user_") else None,
                            "email": ident if "@" in ident else None,
                            "name": None,
                            "phone": None,
                            "status": "ABSENT" if status == "NOT_FOUND" else status,
                            "category": cat,
                            "raw_line": line,
                        }
                        self._add_record(rec)

    def _parse_multimodal(self, file_id, full_path, captured_at, origin):
        cached = CACHED_MULTIMODAL_EXTRACTIONS.get(file_id)
        if not cached:
            return
        system_id = cached.get("system_id", "platform_service")
        for r in cached.get("records", []):
            rec = {
                "file_id": file_id,
                "captured_at": cached.get("captured_at", captured_at),
                "origin": origin,
                "system_id": system_id,
                "resource_id": r.get("resource_id"),
                "user_id": r.get("user_id"),
                "email": r.get("email"),
                "name": r.get("name"),
                "phone": r.get("phone"),
                "status": r.get("status", "PRESENT"),
                "category": r.get("category"),
                "associated_resources": r.get("associated_resources", []),
            }
            self._add_record(rec)

    def query_evidence(self, user_id=None, emails=None, resource_ids=None, hashes=None, max_time=None):
        results = []
        target_emails = set(e.lower() for e in (emails or []) if e)
        target_uid = user_id.lower() if user_id else None
        target_rids = set(resource_ids or [])
        target_hashes = set(h.lower() for h in (hashes or []) if h)

        for rec in self.records:
            if max_time and rec.get("captured_at", "") > max_time:
                continue

            r_uid = (rec.get("user_id") or "").lower()
            r_email = (rec.get("email") or "").lower()
            r_id = rec.get("resource_id")
            r_ck = (rec.get("correlation_key") or "").lower()

            if (target_uid and r_uid == target_uid) or \
               (r_email and r_email in target_emails) or \
               (r_id and r_id in target_rids) or \
               (r_ck and (r_ck in target_hashes or r_ck == target_uid or r_ck in target_emails)):
                results.append(rec)

        return results

    def query_activities(self, max_time=None, resource_ids=None):
        results = []
        target_rids = set(resource_ids or []) if resource_ids else None
        for act in self.system_activities:
            if max_time and act["event_time"] > max_time:
                continue
            if target_rids and act["resource_id"] not in target_rids:
                continue
            results.append(act)
        return results

indexer = EvidenceIndexer()

def verify():
    idx = EvidenceIndexer().index_all(force=True)
    print("=" * 70)
    print("GLOBAL EVIDENCE INDEXER ENHANCED VERIFICATION")
    print("=" * 70)
    print(f"Total Evidence Files in Manifest: {len(idx.file_manifest)}")
    print(f"Total Unified Evidence Records:   {len(idx.records):,}")
    print(f"Unique Resources Indexed:         {len(idx.records_by_resource):,}")
    print(f"Unique Users Indexed:             {len(idx.records_by_user_id):,}")
    print(f"Unique Emails Indexed:            {len(idx.records_by_email):,}")
    print(f"Total System Activity Events:     {len(idx.system_activities):,}")
    print("=" * 70)
    assert len(idx.file_manifest) == 94
    assert len(idx.records) > 2000
    print("ENHANCED INDEXER VERIFIED.")
    return True

if __name__ == "__main__":
    success = verify()
    sys.exit(0 if success else 1)
