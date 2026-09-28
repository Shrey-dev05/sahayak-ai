"""
Builds an ActionPlan ONLY from fields already present on the retrieved,
approved Document/Chunk rows - never invented. If a document has no
`plan_steps`/`plan_documents` metadata, no action plan is generated for it
(the answer still comes back, just without a checklist).
"""
from typing import List, Optional
from sqlalchemy.orm import Session as DBSession
from app import models

# Demo metadata: which seeded documents carry a step-by-step plan, keyed by
# document title so it stays close to the seed data in app/seed.py.
PLAN_LIBRARY = {
    "Crop insurance - general guidance": {
        "steps": [
            "Confirm this season's active crop-insurance scheme name at your bank or CSC",
            "Collect your land record, sowing certificate and bank passbook",
            "Apply before the official cut-off date for your crop and district",
        ],
        "documents_required": ["Land record", "Sowing certificate", "Bank passbook"],
        "warnings": ["Deadlines and premium rates change every season - confirm with an official source before applying."],
    },
    "Pradhan Mantri Fasal Bima Yojana - rules and claims": {
        "steps": [
            "Intimate crop damage within the 72-hour mandatory deadline via 14447 helpline or Crop Insurance App",
            "Gather Khasra/Khatoni land records and Patwari sowing certificate (Girdawari)",
            "Submit joint survey intimation form with bank passbook copy to local agriculture officer",
        ],
        "documents_required": ["Khasra/Khatoni Land Record", "Sowing Certificate / Girdawari", "Bank Passbook Copy", "Photographs of Crop Damage"],
        "warnings": ["Failure to report crop loss within 72 hours of localized calamity can lead to claim rejection."],
    },
    "PACS - primary agricultural credit society": {
        "steps": [
            "Visit your local village PACS secretary or administrative office",
            "Submit membership application with land revenue record (RoR/Khatoni)",
            "Deposit nominal admission fee and purchase required minimum share capital",
        ],
        "documents_required": ["Aadhaar Card", "Land Record (Khasra/Khatoni)", "Passport size photographs", "Bank Account Details"],
        "warnings": ["Only residents within the cooperative society's operational area are eligible for membership."],
    },
    "PACS membership and governance": {
        "steps": [
            "Complete the formal PACS membership application form",
            "Attach landholding certificate and resident proof",
            "Obtain committee resolution approving your member share issuance",
        ],
        "documents_required": ["Identity Proof (Aadhaar/Voter ID)", "Landholding / Cultivator proof", "Nominee details"],
        "warnings": ["Each member holds exactly one vote regardless of the number of shares owned."],
    },
    "Filing a grievance - general process": {
        "steps": [
            "Describe the problem in one or two clear sentences with exact dates and names",
            "Gather transaction receipt, acknowledgement slip, or sanction letter as proof",
            "Submit grievance online at pmfby.gov.in or in writing to District Registrar / Collector",
        ],
        "documents_required": ["Proof of payment or transaction", "Written correspondence / rejection notice", "Identity proof"],
        "warnings": ["Keep a physical or digital copy of your complaint acknowledgement number for follow-up."],
    },
    "Government scheme discovery - general guidance": {
        "steps": [
            "Check scheme eligibility criteria (landholding size, category, and state)",
            "Ensure bank account is Aadhaar-seeded with completed e-KYC",
            "Apply online through the official government portal or visit your nearest CSC",
        ],
        "documents_required": ["Aadhaar Card", "Land records", "Active bank passbook", "Income / caste certificate (if applicable)"],
        "warnings": ["Never pay unauthorized brokers; official scheme application assistance is available at CSCs."],
    },
}


def build_action_plan(db: DBSession, session_id: str, chunks: List[models.Chunk]) -> Optional[models.ActionPlan]:
    for c in chunks:
        doc = db.get(models.Document, c.document_id)
        if doc and doc.title in PLAN_LIBRARY:
            meta = PLAN_LIBRARY[doc.title]
            plan = models.ActionPlan(
                session_id=session_id,
                title=doc.title,
                steps=meta["steps"],
                documents_required=meta["documents_required"],
                warnings=meta["warnings"],
            )
            db.add(plan)
            db.commit()
            db.refresh(plan)
            return plan
    return None
