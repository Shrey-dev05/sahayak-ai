import datetime
from typing import List, Tuple

CHECKLIST_EN = [
    "Proof of payment or transaction, if any",
    "Any written communication about the issue (SMS, letter, receipt)",
    "Your membership / account / policy number",
]
CHECKLIST_HI = [
    "भुगतान या लेनदेन का प्रमाण, यदि कोई हो",
    "इस मुद्दे से जुड़ा कोई भी लिखित संचार (SMS, पत्र, रसीद)",
    "आपकी सदस्यता / खाता / पॉलिसी संख्या",
]


def draft_grievance(category: str, description: str, language: str = "en") -> Tuple[str, List[str]]:
    date = datetime.date.today().isoformat()
    if language == "hi":
        draft = (
            f"शिकायत\nश्रेणी: {category}\nतारीख: {date}\n"
            f"विवरण: {description or '(विवरण जोड़ें)'}\n\n"
            "सुझाव: इसे अपने नज़दीकी सहकारी/PACS कार्यालय या जिला शिकायत पोर्टल पर सबूत सहित जमा करें।"
        )
        return draft, CHECKLIST_HI
    draft = (
        f"Complaint\nCategory: {category}\nDate: {date}\n"
        f"Description: {description or '(add a description)'}\n\n"
        "Suggested next step: submit this at your nearest cooperative/PACS office "
        "or your district grievance portal, along with the supporting documents below."
    )
    return draft, CHECKLIST_EN
