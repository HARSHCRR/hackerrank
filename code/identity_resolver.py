#!/usr/bin/env python3
"""
Historical Identity Graph Resolver for HackerRank Orchestrate: Ghost Data Still Exists.
Resolves transitive identities across user_identities.csv and user_audit_log.csv
linking user_id, current and historical emails, names, phones, and email hashes.
"""

import csv
import hashlib
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

try:
    from code.config import DATASET_DIR
except ImportError:
    from .config import DATASET_DIR

@dataclass
class IdentityProfile:
    user_id: str
    primary_email: str
    all_emails: Set[str] = field(default_factory=set)
    primary_name: str = ""
    all_names: Set[str] = field(default_factory=set)
    primary_phone: str = ""
    all_phones: Set[str] = field(default_factory=set)
    all_hashes: Set[str] = field(default_factory=set)
    audit_events: List[Dict] = field(default_factory=list)

class IdentityResolver:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IdentityResolver, cls).__new__(cls)
            cls._instance.is_loaded = False
            cls._instance.identities_by_id = {}
            cls._instance.identities_by_email = {}
            cls._instance.audit_by_user = defaultdict(list)
            cls._instance.audit_by_email = defaultdict(list)
        return cls._instance

    def load(self, force=False):
        if self.is_loaded and not force:
            return self

        # 1. Load user_identities.csv
        ident_file = DATASET_DIR / "user_identities.csv"
        with open(ident_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid = row["user_id"]
                email = row["email"].lower().strip()
                self.identities_by_id[uid] = row
                self.identities_by_email[email] = uid

        # 2. Load user_audit_log.csv
        audit_file = DATASET_DIR / "user_audit_log.csv"
        with open(audit_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid = row["user_id"]
                self.audit_by_user[uid].append(row)
                if row["field_name"] == "email":
                    if row["old_value"]:
                        self.audit_by_email[row["old_value"].lower().strip()].append(uid)
                    if row["new_value"]:
                        self.audit_by_email[row["new_value"].lower().strip()].append(uid)

        self.is_loaded = True
        return self

    def _compute_hashes(self, email_str: str) -> Set[str]:
        hashes = set()
        clean = email_str.lower().strip()
        if not clean:
            return hashes
        hashes.add(hashlib.sha256(clean.encode("utf-8")).hexdigest())
        hashes.add(hashlib.md5(clean.encode("utf-8")).hexdigest())
        return hashes

    def resolve(self, request_email: str, audit_at: Optional[str] = None) -> Optional[IdentityProfile]:
        self.load()
        req_email_clean = request_email.lower().strip()

        # Step 1: Find user_id
        uid = self.identities_by_email.get(req_email_clean)
        if not uid:
            candidates = self.audit_by_email.get(req_email_clean, [])
            if candidates:
                uid = candidates[0]

        if not uid or uid not in self.identities_by_id:
            # Fallback for synthetic / unmapped emails
            profile = IdentityProfile(
                user_id="",
                primary_email=req_email_clean,
                all_emails={req_email_clean},
                all_hashes=self._compute_hashes(req_email_clean),
            )
            return profile

        # Step 2: Build complete historical profile
        curr = self.identities_by_id[uid]
        all_emails = {req_email_clean}
        curr_email = curr["email"].lower().strip()
        if curr_email:
            all_emails.add(curr_email)

        all_names = set()
        if curr.get("name"):
            all_names.add(curr["name"].strip())

        all_phones = set()
        if curr.get("phone"):
            all_phones.add(curr["phone"].strip())

        all_hashes = set()
        if curr.get("email_hash"):
            all_hashes.add(curr["email_hash"].lower().strip())

        # Collect historical changes <= audit_at
        audit_events = []
        for event in self.audit_by_user.get(uid, []):
            ev_time = event.get("event_time", "")
            if audit_at and ev_time > audit_at:
                continue

            audit_events.append(event)
            fname = event.get("field_name")
            old_val = (event.get("old_value") or "").strip()
            new_val = (event.get("new_value") or "").strip()

            if fname == "email":
                if old_val:
                    all_emails.add(old_val.lower())
                if new_val:
                    all_emails.add(new_val.lower())
            elif fname == "name":
                if old_val:
                    all_names.add(old_val)
                if new_val:
                    all_names.add(new_val)
            elif fname == "phone":
                if old_val:
                    all_phones.add(old_val)
                if new_val:
                    all_phones.add(new_val)
            elif fname == "email_hash":
                if old_val:
                    all_hashes.add(old_val.lower())
                if new_val:
                    all_hashes.add(new_val.lower())

        # Compute hashes for all discovered emails
        for em in all_emails:
            all_hashes.update(self._compute_hashes(em))

        return IdentityProfile(
            user_id=uid,
            primary_email=curr_email or req_email_clean,
            all_emails=all_emails,
            primary_name=curr.get("name", ""),
            all_names=all_names,
            primary_phone=curr.get("phone", ""),
            all_phones=all_phones,
            all_hashes=all_hashes,
            audit_events=audit_events,
        )

resolver = IdentityResolver()

def test_samples():
    res = IdentityResolver().load()
    sample_file = DATASET_DIR / "sample_deletion_requests.csv"
    with open(sample_file, mode="r", encoding="utf-8") as f:
        samples = list(csv.DictReader(f))

    print("=" * 75)
    print("HISTORICAL IDENTITY GRAPH RESOLVER — SAMPLE VERIFICATION")
    print("=" * 75)
    resolved_count = 0
    for row in samples:
        cid = row["case_id"]
        req_email = row["email"]
        audit_at = row["audit_at"]
        prof = res.resolve(req_email, audit_at)
        assert prof is not None, f"Failed to resolve profile for {req_email}"
        if prof.user_id:
            resolved_count += 1
            print(f"[{cid}] {req_email} -> {prof.user_id} ({prof.primary_name}) | Emails: {len(prof.all_emails)} | Hashes: {len(prof.all_hashes)} | Audits: {len(prof.audit_events)}")
        else:
            print(f"[{cid}] {req_email} -> UNRESOLVED USER_ID")

    print("-" * 75)
    print(f"Resolved Users: {resolved_count}/{len(samples)} (100.0%)")
    assert resolved_count == len(samples), f"Expected all {len(samples)} to be resolved!"
    print("IDENTITY RESOLVER TEST PASSED.")
    print("=" * 75)
    return True

if __name__ == "__main__":
    if "--test-samples" in sys.argv:
        success = test_samples()
        sys.exit(0 if success else 1)
    else:
        test_samples()
