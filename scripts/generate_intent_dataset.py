"""
Generates data/intents/intent_dataset.jsonl.

Important distinction from the RAG knowledge base: this dataset teaches the
model to recognize HOW users ask things (phrasing, language-mixing, slang),
not WHAT the facts are. So it is safe to generate programmatically - there
is no government fact, deadline or eligibility rule being invented here,
only realistic ways of asking a question whose real answer will always
come from the verified knowledge base, never from this dataset.

Run: python3 scripts/generate_intent_dataset.py
"""
import json
import random
from pathlib import Path

random.seed(7)
OUT = Path(__file__).resolve().parent.parent / "data" / "intents" / "intent_dataset.jsonl"

CROPS = ["dhaan", "gehu", "cotton", "sugarcane", "makka", "rice", "wheat", "soybean", "groundnut", "bajra"]
CROPS_EN = ["rice", "wheat", "cotton", "sugarcane", "maize", "soybean", "groundnut", "millet"]
SEASONS = ["kharif", "rabi", "zaid"]
LOAN_TYPES = ["crop loan", "gold loan", "kisan credit card", "home loan", "personal loan"]
DOC_TYPES = ["notice", "letter", "receipt", "form", "certificate", "loan statement"]
GOV_TOPICS = ["election", "audit", "by-laws", "membership rules", "annual meeting", "board voting"]

rows = []


def add(text, intent, language, entities=None):
    rows.append({"text": text.strip(), "intent": intent, "language": language, "entities": entities or {}})


# ---------- PACS_INFO ----------
for t in [
    ("PACS kya hota hai?", "hinglish"),
    ("PACS kya hai?", "hinglish"),
    ("What is PACS?", "en"),
    ("Can you explain what a PACS is?", "en"),
    ("PACS ka matlab kya hota hai?", "hinglish"),
    ("प्राइमरी एग्रीकल्चर क्रेडिट सोसाइटी क्या होती है?", "hi"),
    ("PACS ke baare mein bataiye", "hinglish"),
    ("Village level cooperative society kya hoti hai?", "hinglish"),
    ("PACS society ka function kya hota hai?", "hinglish"),
    ("mujhe PACS samjhao", "hinglish"),
    ("PACS aur cooperative bank mein kya fark hai?", "hinglish"),
    ("What services does a PACS provide?", "en"),
    ("PACS se kya kya fayda hota hai?", "hinglish"),
    ("गांव की सहकारी समिति क्या होती है", "hi"),
    ("What is the role of a Primary Agricultural Credit Society?", "en"),
]:
    add(t[0], "PACS_INFO", t[1])

# ---------- PACS_MEMBERSHIP ----------
for t in [
    ("PACS ka member kaise bane?", "hinglish"),
    ("PACS membership kaise milegi?", "hinglish"),
    ("PACS me member banne ke liye kya chahiye?", "hinglish"),
    ("PACS mein judne ka process kya hai?", "hinglish"),
    ("How can I become a PACS member?", "en"),
    ("PACS me naam kaise add karwaye?", "hinglish"),
    ("PACS ka member banane ke liye documents kya lagenge?", "hinglish"),
    ("What documents do I need for PACS membership?", "en"),
    ("Kya koi bhi kisan PACS ka member ban sakta hai?", "hinglish"),
    ("PACS सदस्यता कैसे लें?", "hi"),
    ("PACS membership fee kitni hai?", "hinglish"),
    ("Main PACS join karna chahta hoon, kaise karu?", "hinglish"),
    ("Is there an age limit to join a PACS?", "en"),
    ("PACS ki सदस्यता के लिए क्या पात्रता है?", "hi"),
]:
    add(t[0], "PACS_MEMBERSHIP", t[1])

# ---------- COOP_REGISTRATION ----------
for t in [
    ("Cooperative society ka registration kaise kare?", "hinglish"),
    ("How do I register a new cooperative society?", "en"),
    ("Naye cooperative society banane ke liye kya karna hoga?", "hinglish"),
    ("सहकारी समिति का पंजीकरण कैसे करें?", "hi"),
    ("Cooperative society register karne ke liye minimum kitne members chahiye?", "hinglish"),
    ("What is the process to form a cooperative society?", "en"),
    ("Society registration ke liye kaunse documents chahiye?", "hinglish"),
    ("Cooperative society ka registration certificate kaise milta hai?", "hinglish"),
    ("How long does cooperative registration usually take?", "en"),
    ("सोसाइटी रजिस्ट्रेशन की फीस कितनी है?", "hi"),
]:
    add(t[0], "COOP_REGISTRATION", t[1])

# ---------- COOP_GOVERNANCE ----------
for topic in GOV_TOPICS:
    add(f"Cooperative society mein {topic} kaise hota hai?", "COOP_GOVERNANCE", "hinglish", {"topic": topic})
    add(f"How does {topic} work in a cooperative society?", "COOP_GOVERNANCE", "en", {"topic": topic})
add("Cooperative society ke board election ka process kya hai?", "COOP_GOVERNANCE", "hinglish")
add("सहकारी समिति की वार्षिक बैठक कब होती है?", "COOP_GOVERNANCE", "hi")
add("Who can vote in a cooperative society's board election?", "COOP_GOVERNANCE", "en")
add("Society ka audit kaun karta hai?", "COOP_GOVERNANCE", "hinglish")

# ---------- COOP_LAW ----------
for topic in ["member rights", "dispute resolution", "liquidation", "amendment of by-laws", "record keeping"]:
    add(f"Cooperative societies act mein {topic} ke baare mein kya likha hai?", "COOP_LAW", "hinglish", {"topic": topic})
    add(f"What does the Cooperative Societies Act say about {topic}?", "COOP_LAW", "en", {"topic": topic})
add("Agar society ke rules follow nahi ho rahe to kya kare?", "COOP_LAW", "hinglish")
add("Is this cooperative by-law legally valid?", "COOP_LAW", "en")
add("सहकारी अधिनियम के तहत सदस्यों के अधिकार क्या हैं?", "COOP_LAW", "hi")

# ---------- GOVT_SCHEME ----------
for t in [
    ("Mere liye konsi sarkari yojana available hai?", "hinglish"),
    ("What government schemes am I eligible for?", "en"),
    ("Farmers ke liye koi naya scheme aaya hai kya?", "hinglish"),
    ("किसानों के लिए कौन सी सरकारी योजनाएं हैं?", "hi"),
    ("Is there a subsidy scheme for dairy farmers?", "en"),
    ("Cooperative members ke liye koi special scheme hai?", "hinglish"),
    ("Mujhe scheme ki eligibility check karni hai", "hinglish"),
    ("Scheme apply karne ka last date kya hai?", "hinglish"),
    ("What is the application process for this scheme?", "en"),
    ("Yojana ke liye kaunse documents chahiye?", "hinglish"),
]:
    add(t[0], "GOVT_SCHEME", t[1])

# ---------- CROP_INSURANCE ----------
for crop in CROPS:
    for season in SEASONS:
        add(f"{crop} ka insurance {season} season ke liye kaise milega?", "CROP_INSURANCE", "hinglish",
            {"crop": crop, "season": season})
for t in [
    ("Fasal ka insurance kaise milega?", "hinglish"),
    ("How do I get crop insurance?", "en"),
    ("Crop insurance ke liye premium kitna lagta hai?", "hinglish"),
    ("फसल बीमा कैसे कराएं?", "hi"),
    ("What documents are needed for crop insurance enrollment?", "en"),
    ("PMFBY ke liye apply kaise kare?", "hinglish"),
    ("Fasal bima yojana ka last date kya hai?", "hinglish"),
    ("Insurance premium sarkar deti hai ya kisan?", "hinglish"),
]:
    add(t[0], "CROP_INSURANCE", t[1])

# ---------- CROP_DAMAGE ----------
damage_templates_hi_mix = [
    "{crop} barbad ho gyi",
    "{crop} kharab ho gayi",
    "meri {crop} crop damage ho gayi",
    "baarish me {crop} chali gayi",
    "paani me {crop} doob gyi",
    "sukhe se {crop} ki fasal kharab ho gayi",
    "keeton ne meri {crop} ki fasal barbad kar di",
    "ओलावृष्टि से {crop} की फसल खराब हो गई",
    "meri {crop} ki fasal beema claim ke layak hai kya?",
    "{crop} nuksan ho gaya, ab kya karu?",
]
for crop in CROPS:
    for tmpl in random.sample(damage_templates_hi_mix, 4):
        text = tmpl.format(crop=crop)
        lang = "hi" if any(ord(c) > 2304 for c in text) else "hinglish"
        add(text, "CROP_DAMAGE", lang, {"crop": crop})
add("My rice crop was destroyed by flooding, what should I do?", "CROP_DAMAGE", "en", {"crop": "rice"})
add("Hailstorm damaged my wheat field", "CROP_DAMAGE", "en", {"crop": "wheat"})

# ---------- AGRICULTURAL_SUPPORT ----------
for t in [
    ("Irrigation ke liye koi subsidy hai kya?", "hinglish"),
    ("Is there a subsidy for drip irrigation?", "en"),
    ("Tractor kharidne ke liye loan kaise milega?", "hinglish"),
    ("Beej aur khaad par sarkari sahayata milti hai kya?", "hinglish"),
    ("How do FPOs (Farmer Producer Organizations) help farmers?", "en"),
    ("Fasal ki storage ke liye godam kaise milega?", "hinglish"),
    ("मंडी में उपज कैसे बेचें?", "hi"),
    ("What machinery subsidies are available for small farmers?", "en"),
]:
    add(t[0], "AGRICULTURAL_SUPPORT", t[1])

# ---------- FINANCIAL_LITERACY ----------
for t in [
    ("Loan par interest kaise calculate hota hai?", "hinglish"),
    ("How is EMI calculated?", "en"),
    ("Credit score kya hota hai aur kaise sudharein?", "hinglish"),
    ("Savings account aur fixed deposit mein kya fark hai?", "hinglish"),
    ("ब्याज दर कैसे तय होती है?", "hi"),
    ("What is KYC and why is it required?", "en"),
    ("Digital payment fraud se kaise bache?", "hinglish"),
    ("Karz chukane mein deri ho jaye to kya hota hai?", "hinglish"),
    ("What's the difference between simple and compound interest?", "en"),
    ("Cooperative bank mein account kaise khole?", "hinglish"),
]:
    add(t[0], "FINANCIAL_LITERACY", t[1])

# ---------- BANKING ----------
for t in [
    ("Bank account kholne ke liye kya documents chahiye?", "hinglish"),
    ("How do I open a savings account at a cooperative bank?", "en"),
    ("Passbook update kaise karwaye?", "hinglish"),
    ("ATM card kho gaya, kya karu?", "hinglish"),
    ("What is a minimum balance requirement?", "en"),
]:
    add(t[0], "BANKING", t[1])

# ---------- LOAN ----------
for loan in LOAN_TYPES:
    add(f"{loan} ke liye eligibility kya hai?", "LOAN", "hinglish", {"loan_type": loan})
    add(f"How do I apply for a {loan}?", "LOAN", "en", {"loan_type": loan})
add("Kisan credit card kaise banwaye?", "LOAN", "hinglish")
add("Loan repay karne ka schedule kaise dekhein?", "LOAN", "hinglish")

# ---------- GRIEVANCE ----------
for t in [
    ("Mera claim reject ho gaya.", "hinglish", "INSURANCE"),
    ("My crop insurance claim was rejected. Where do I complain?", "en", "INSURANCE"),
    ("Complaint kaha kare?", "hinglish", None),
    ("PACS staff ne mera kaam nahi kiya, complaint kaise kare?", "hinglish", "STAFF"),
    ("Mujhe scheme ka paisa nahi mila, shikayat kaise darj kare?", "hinglish", "PAYMENT"),
    ("How do I escalate an unresolved grievance?", "en", None),
    ("बैंक अधिकारी ने गलत जानकारी दी, शिकायत कैसे करूं?", "hi", "STAFF"),
    ("Society election mein gadbadi hui, kaha report kare?", "hinglish", "GOVERNANCE"),
    ("Mera application 3 mahine se pending hai, ab kya karu?", "hinglish", "DELAY"),
    ("I was overcharged for a service, how do I file a complaint?", "en", "PAYMENT"),
]:
    add(t[0], "GRIEVANCE", t[1], {"category": t[2]} if t[2] else {})

# ---------- DOCUMENT_EXPLANATION ----------
for doc in DOC_TYPES:
    add(f"Is {doc} ko samjhao", "DOCUMENT_EXPLANATION", "hinglish", {"document_type": doc})
    add(f"Can you explain this {doc}?", "DOCUMENT_EXPLANATION", "en", {"document_type": doc})
add("Mujhe ye sarkari notice samajh nahi aaya", "DOCUMENT_EXPLANATION", "hinglish")
add("What does this letter from the cooperative office mean?", "DOCUMENT_EXPLANATION", "en")
add("इस दस्तावेज़ में क्या लिखा है?", "DOCUMENT_EXPLANATION", "hi")

# ---------- FORM_ASSISTANCE ----------
for t in [
    ("Ye form kaise bhare?", "hinglish"),
    ("Can you help me fill this application form?", "en"),
    ("Scheme application form mein kya likhna hai?", "hinglish"),
    ("फॉर्म भरने में मदद चाहिए", "hi"),
    ("I don't understand this field on the form", "en"),
]:
    add(t[0], "FORM_ASSISTANCE", t[1])

# ---------- UNKNOWN (out-of-domain negatives) ----------
for t in [
    ("What's the weather like today?", "en"),
    ("Aaj cricket match kisne jeeta?", "hinglish"),
    ("Tell me a joke", "en"),
    ("Mujhe gaana sunao", "hinglish"),
    ("What's the capital of France?", "en"),
    ("Movie recommend karo", "hinglish"),
    ("आज का पंचांग बताओ", "hi"),
    ("How do I cook biryani?", "en"),
    ("Phone ka naya model kaunsa aaya hai?", "hinglish"),
    ("What time is it?", "en"),
]:
    add(t[0], "UNKNOWN", t[1])

# ---------- extra volume for thin classes (target ~25+ each) ----------
BANK_SERVICES = ["a savings account", "a fixed deposit", "a recurring deposit", "a locker", "a cheque book"]
for svc in BANK_SERVICES:
    add(f"How do I open {svc} at my PACS bank?", "BANKING", "en", {"service": svc})
    add(f"{svc} khulwane ke liye kya karna hoga?", "BANKING", "hinglish", {"service": svc})
add("Net banking activate kaise kare?", "BANKING", "hinglish")
add("Mera account freeze ho gaya hai, kya karu?", "BANKING", "hinglish")
add("What is the interest rate on a cooperative bank savings account?", "BANKING", "en")
add("बैंक खाता आधार से लिंक कैसे करें?", "BANKING", "hi")

FORMS = ["scheme application", "loan application", "membership form", "insurance claim form", "grievance form"]
for f_ in FORMS:
    add(f"Ye {f_} kaise bhare?", "FORM_ASSISTANCE", "hinglish", {"form": f_})
    add(f"Can you walk me through this {f_}?", "FORM_ASSISTANCE", "en", {"form": f_})
add("Form mein signature kaha karna hai?", "FORM_ASSISTANCE", "hinglish")
add("I'm stuck on the eligibility section of this form", "FORM_ASSISTANCE", "en")
add("फॉर्म में कौन सी जानकारी भरनी है?", "FORM_ASSISTANCE", "hi")

AG_TOPICS = ["seeds", "fertilizer", "pesticide", "tractor purchase", "cold storage", "warehouse", "market linkage"]
for topic in AG_TOPICS:
    add(f"{topic} ke liye koi sarkari sahayata hai kya?", "AGRICULTURAL_SUPPORT", "hinglish", {"topic": topic})
    add(f"Is there government support for {topic}?", "AGRICULTURAL_SUPPORT", "en", {"topic": topic})

GRIEV_EXTRA = [
    ("Mera refund abhi tak nahi aaya", "hinglish", "PAYMENT"),
    ("The cooperative office is not responding to my application", "en", "DELAY"),
    ("Mujhe galat jankari di gayi thi, ab kya kare?", "hinglish", "STAFF"),
    ("How do I check the status of my complaint?", "en", None),
    ("शिकायत दर्ज करने के बाद कितने दिन में जवाब मिलता है?", "hi", None),
    ("Society ne meri application reject kar di bina reason bataye", "hinglish", "DELAY"),
    ("Where is my district's grievance redressal office?", "en", None),
    ("Complaint number kho gaya, kaise track kare?", "hinglish", None),
]
for text, lang, cat in GRIEV_EXTRA:
    add(text, "GRIEVANCE", lang, {"category": cat} if cat else {})

SCHEME_EXTRA = [
    ("Dairy farmers ke liye koi scheme hai?", "hinglish"),
    ("Is there a scheme for women in agriculture?", "en"),
    ("Small and marginal farmers ke liye kya benefits milte hain?", "hinglish"),
    ("युवा किसानों के लिए कोई योजना है?", "hi"),
    ("What subsidy schemes exist for solar water pumps?", "en"),
    ("Scheme ka beneficiary list kaise check kare?", "hinglish"),
]
for t, l in SCHEME_EXTRA:
    add(t, "GOVT_SCHEME", l)

FIN_EXTRA = [
    ("Mutual fund aur FD mein kya better hai?", "hinglish"),
    ("What is a good credit score range?", "en"),
    ("Overdraft facility kya hoti hai?", "hinglish"),
    ("How does compound interest work over years?", "en"),
    ("UPI se payment safe hai kya?", "hinglish"),
    ("बचत खाते पर ब्याज कैसे मिलता है?", "hi"),
]
for t, l in FIN_EXTRA:
    add(t, "FINANCIAL_LITERACY", l)

REG_EXTRA = [
    ("Society ke bye-laws kaise banaye?", "hinglish"),
    ("What's the minimum share capital to register a cooperative?", "en"),
    ("Cooperative registration ke baad kya karna padta hai?", "hinglish"),
    ("सहकारी समिति पंजीकरण प्रमाणपत्र कहां से मिलेगा?", "hi"),
]
for t, l in REG_EXTRA:
    add(t, "COOP_REGISTRATION", l)

PACS_MEM_EXTRA = [
    ("Kya women bhi PACS ki member ban sakti hain?", "hinglish"),
    ("Can a person from another village join our PACS?", "en"),
    ("PACS membership cancel kaise kare?", "hinglish"),
    ("PACS सदस्यता नवीनीकरण कैसे करें?", "hi"),
]
for t, l in PACS_MEM_EXTRA:
    add(t, "PACS_MEMBERSHIP", l)

COOP_LAW_EXTRA = [
    ("Can a cooperative society expel a member?", "en"),
    ("Society ke fund ka misuse ho to kanooni kya vikalp hai?", "hinglish"),
    ("सहकारी समिति भंग कैसे होती है?", "hi"),
]
for t, l in COOP_LAW_EXTRA:
    add(t, "COOP_LAW", l)

PACS_INFO_EXTRA = [
    ("PACS kis ministry ke under aata hai?", "hinglish"),
    ("How many PACS typically operate in one district?", "en"),
    ("PACS और सहकारी बैंक में क्या संबंध है?", "hi"),
]
for t, l in PACS_INFO_EXTRA:
    add(t, "PACS_INFO", l)

DOC_EXTRA = [
    ("This insurance policy document has terms I don't understand", "en"),
    ("Bank statement mein ye charges kya hain?", "hinglish"),
    ("यह प्रमाणपत्र असली है या नकली कैसे जानें?", "hi"),
]
for t, l in DOC_EXTRA:
    add(t, "DOCUMENT_EXPLANATION", l)

UNKNOWN_EXTRA = [
    ("Best restaurant nearby kaunsa hai?", "hinglish"),
    ("Can you recommend a good smartphone under 15000?", "en"),
    ("Aaj ka rashifal kya hai?", "hinglish"),
    ("Play some music", "en"),
    ("Bus timing bata do", "hinglish"),
    ("What's trending on social media?", "en"),
    ("Cricket score kya hai abhi?", "hinglish"),
    ("मुझे एक कहानी सुनाओ", "hi"),
]
UNKNOWN_EXTRA = [
    ("Best restaurant nearby kaunsa hai?", "hinglish"),
    ("Can you recommend a good smartphone under 15000?", "en"),
    ("Aaj ka rashifal kya hai?", "hinglish"),
    ("Play some music", "en"),
    ("Bus timing bata do", "hinglish"),
    ("What's trending on social media?", "en"),
    ("Cricket score kya hai abhi?", "hinglish"),
    ("मुझे एक कहानी सुनाओ", "hi"),
    ("Diwali kab hai is saal?", "hinglish"),
    ("Tell me a fun fact", "en"),
    ("Nearest petrol pump kaha hai?", "hinglish"),
    ("What's your favorite color?", "en"),
    ("Aaj ki taza khabrein sunao", "hinglish"),
    ("How do I learn Python?", "en"),
    ("Bacchon ke liye koi game suggest karo", "hinglish"),
]
for t, l in UNKNOWN_EXTRA:
    add(t, "UNKNOWN", l)

# ---------- round 2 bulk-up for the weakest classes on the held-out report ----------
FIN_EXTRA2 = [
    ("Recurring deposit kaise kaam karti hai?", "hinglish"),
    ("What's the benefit of a fixed deposit over a savings account?", "en"),
    ("Inflation ka paison par kya asar padta hai?", "hinglish"),
    ("How do I start budgeting my monthly income?", "en"),
    ("Chit fund safe hota hai kya?", "hinglish"),
    ("What does 'principal amount' mean in a loan?", "en"),
    ("Bachat karne ka sabse accha tarika kya hai?", "hinglish"),
    ("Is postal savings safer than a bank?", "en"),
    ("ब्याज दर बढ़ने से EMI par kya farak padta hai?", "hi"),
    ("What is financial inclusion?", "en"),
    ("Paise invest karne se pehle kya dhyan rakhein?", "hinglish"),
    ("How can I track my monthly expenses?", "en"),
    ("Insurance premium aur bank interest mein kya fark hai?", "hinglish"),
    ("What is the penalty for late loan repayment?", "en"),
]
for t, l in FIN_EXTRA2:
    add(t, "FINANCIAL_LITERACY", l)

GRIEV_EXTRA2 = [
    ("Mera application bina kisi karan reject ho gaya", "hinglish", "DELAY"),
    ("I want to escalate my complaint to a higher authority", "en", None),
    ("Society ke fund mein gadbadi lag rahi hai, kya karu?", "hinglish", "GOVERNANCE"),
    ("Nobody is responding to my written complaint", "en", "DELAY"),
    ("Mujhse ghoos maangi gayi office mein", "hinglish", "STAFF"),
    ("How long does a grievance usually take to resolve?", "en", None),
    ("मेरी शिकायत का स्टेटस कैसे देखूं?", "hi", None),
    ("Complaint darj karne ke baad receipt milti hai kya?", "hinglish", None),
    ("I received the wrong amount from a scheme payout", "en", "PAYMENT"),
    ("Panchayat adhikari ne sahi jawab nahi diya", "hinglish", "STAFF"),
]
for text, lang, cat in GRIEV_EXTRA2:
    add(text, "GRIEVANCE", lang, {"category": cat} if cat else {})

PACS_INFO_EXTRA2 = [
    ("PACS ka full form kya hai?", "hinglish"),
    ("Is a PACS the same as a regular bank branch?", "en"),
    ("PACS ki sthapna kab hui thi?", "hinglish"),
    ("Who regulates PACS societies?", "en"),
    ("PACS किसानों को कौन सी सेवाएं देती है?", "hi"),
    ("What's the difference between a PACS and an FPO?", "en"),
    ("PACS gaon mein kitni common hoti hai?", "hinglish"),
    ("Does every village have its own PACS?", "en"),
    ("PACS ka board kaun chalata hai?", "hinglish"),
]
for t, l in PACS_INFO_EXTRA2:
    add(t, "PACS_INFO", l)

LOAN_EXTRA2 = [
    ("Loan approval mein kitna time lagta hai?", "hinglish"),
    ("What collateral is needed for a crop loan?", "en"),
    ("Loan default hone par kya hota hai?", "hinglish"),
    ("Can I prepay my loan without a penalty?", "en"),
    ("Kisan credit card ki limit kaise badhti hai?", "hinglish"),
    ("What's the difference between secured and unsecured loans?", "en"),
    ("Guarantor ke bina loan mil sakta hai kya?", "hinglish"),
    ("How is loan eligibility calculated?", "en"),
    ("Purana loan chukaye bina naya loan mil sakta hai?", "hinglish"),
    ("What documents are needed to apply for a gold loan?", "en"),
    ("Loan ka interest rate fix hota hai ya badalta rehta hai?", "hinglish"),
]
for t, l in LOAN_EXTRA2:
    add(t, "LOAN", l)

DOC_EXTRA2 = [
    ("This is a legal notice, can you explain the important parts?", "en"),
    ("Mujhe apne loan agreement ki shartein samajhni hain", "hinglish"),
    ("Certificate mein ye seal ka kya matlab hai?", "hinglish"),
    ("What does this insurance policy's exclusion clause mean?", "en"),
    ("Ye receipt kis payment ki hai samajh nahi aa raha", "hinglish"),
    ("Can you explain the terms on the back of this form?", "en"),
    ("इस पत्र में क्या कार्रवाई करने को कहा गया है?", "hi"),
]
for t, l in DOC_EXTRA2:
    add(t, "DOCUMENT_EXPLANATION", l)

BANKING_EXTRA2 = [
    ("Mobile banking app kaise install kare?", "hinglish"),
    ("How do I update my registered mobile number with the bank?", "en"),
    ("Joint account kholne ke liye dono logo ko jana padega kya?", "hinglish"),
    ("What happens if I don't maintain the minimum balance?", "en"),
    ("Cheque bounce hone par kya penalty lagti hai?", "hinglish"),
]
for t, l in BANKING_EXTRA2:
    add(t, "BANKING", l)

# ---------- Explicit Blueprint & Pipeline Examples ----------
BLUEPRINT_EXAMPLES = [
    ("PACS kya hota hai?", "PACS_INFO", "hinglish"),
    ("PACS kya hai?", "PACS_INFO", "hinglish"),
    ("PACS ke kya benefits hain?", "PACS_INFO", "hinglish"),
    ("PACS ka member kaise bane?", "PACS_MEMBERSHIP", "hinglish"),
    ("PACS membership kaise milegi?", "PACS_MEMBERSHIP", "hinglish"),
    ("PACS me member banne ke liye kya chahiye?", "PACS_MEMBERSHIP", "hinglish"),
    ("PACS mein judne ka process kya hai?", "PACS_MEMBERSHIP", "hinglish"),
    ("How can I become a PACS member?", "PACS_MEMBERSHIP", "en"),
    ("PACS me naam kaise add karwaye?", "PACS_MEMBERSHIP", "hinglish"),
    ("PACS ka member banane ke liye documents kya lagenge?", "PACS_MEMBERSHIP", "hinglish"),
    ("Fasal ka insurance kaise milega?", "CROP_INSURANCE", "hinglish"),
    ("Crop insurance enrollment procedure", "CROP_INSURANCE", "en"),
    ("PMFBY Kharif Chhattisgarh", "CROP_INSURANCE", "en"),
    ("Mera claim reject ho gaya.", "GRIEVANCE", "hinglish"),
    ("Mera crop insurance claim reject ho gaya. Complaint kaha karu?", "GRIEVANCE", "hinglish"),
    ("Complaint kaha kare?", "GRIEVANCE", "hinglish"),
    ("Cooperative society ka registration kaise kare?", "COOP_REGISTRATION", "hinglish"),
    ("Loan par interest kaise calculate hota hai?", "FINANCIAL_LITERACY", "hinglish"),
    ("Is notice ko samjhao.", "DOCUMENT_EXPLANATION", "hinglish"),
    ("fasal barbad ho gyi", "CROP_DAMAGE", "hinglish"),
    ("fasal kharab ho gayi", "CROP_DAMAGE", "hinglish"),
    ("meri crop damage ho gayi", "CROP_DAMAGE", "hinglish"),
    ("baarish me fasal chali gayi", "CROP_DAMAGE", "hinglish"),
    ("paani me fasal doob gyi", "CROP_DAMAGE", "hinglish"),
    ("Meri fasal baarish se kharab ho gayi, insurance ka claim kaise karu?", "CROP_DAMAGE", "hinglish"),
    ("Meri fasal kharab ho gayi hai, insurance claim ka complete process documents ke saath batao.", "CROP_DAMAGE", "hinglish"),
]
for t, intent, lang in BLUEPRINT_EXAMPLES:
    add(t, intent, lang)

random.shuffle(rows)
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"Wrote {len(rows)} examples to {OUT}")
from collections import Counter
c = Counter(r["intent"] for r in rows)
for k, v in sorted(c.items(), key=lambda x: -x[1]):
    print(f"  {k:22s} {v}")
