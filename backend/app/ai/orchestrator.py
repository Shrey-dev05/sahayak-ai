"""
Deterministic orchestration sequence: the LLM generates solutions grounded
in verified facts and broad domain intelligence. Kiosk displays brief summaries
and mobile displays detailed step-by-step guides with PDF generation.
"""
from typing import List, Optional
from sqlalchemy.orm import Session as DBSession
from app import models, schemas
from app.ai.intents import classify_intent, is_complex
from app.ai.llm import get_llm_provider
from app.rag.retrieval import score_chunks
from app.rag.fact_check import requires_specific_fact, evidence_has_fact, missing_named_entity
from app.services.action_plan import build_action_plan
from app.services.qr_service import create_qr_session
from app.speech.tts import clean_for_speech

import re

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")

# Comprehensive Hinglish markers: Hindi pronouns, question words, verbs, auxiliaries, postpositions, and rural domain terms
HINGLISH_MARKERS = {
    # Pronouns & Possessives
    "mera", "meri", "mere", "mujhe", "mujhko", "hum", "humara", "humare", "humari",
    "aap", "aapka", "aapke", "aapki", "aapko", "tum", "tumhara", "tumhe",
    "yeh", "ye", "woh", "wo", "unka", "unke", "unki", "kisko", "kiska", "kiske", "kisne", "apna", "apne", "apni",
    # Postpositions & Conjunctions
    "ka", "ki", "ke", "ko", "se", "me", "mein", "par", "pe", "aur", "ya", "bhi", "toh", "to", "agar", "jab", "tab", "ab", "sab", "sabse",
    # Question words
    "kya", "kaise", "kyu", "kyun", "kab", "kaha", "kahan", "kitna", "kitne", "kitni", "kaun",
    # Verbs, Auxiliaries & Actions
    "hai", "hain", "ho", "hu", "hoon", "tha", "thi", "the", "hoga", "hogi", "honge", "hote", "hoti", "hota",
    "kare", "karen", "karein", "karo", "karna", "karta", "karti", "karte", "kiya", "kiye", "de", "dena", "diya", "diye", "lo", "lena", "liya",
    "batao", "bataiye", "bataye", "bata", "chahiye", "raha", "rahe", "rahi",
    "aaya", "aaye", "aayega", "aayegi", "aayenge", "milega", "milegi", "milenge", "milta", "milti", "sakta", "sakte", "sakti",
    "gaya", "gaye", "gayi", "lagta", "lagte", "lagti", "lagega", "lagegi", "lagengi",
    "baat", "bolo", "bolna", "sun", "suno", "dekh", "dekho", "dekhein", "samjhao",
    "nahi", "nhi", "mat", "na",
    # Domain concepts frequently uttered in Hinglish
    "fasal", "bima", "nuksan", "kharab", "barbad", "paise", "paisa", "kisan", "kisano", "kheti",
    "zameen", "zamin", "karz", "byaj", "samiti", "suchi", "shikayat", "darj", "madad", "sadasya",
    "aavedan", "patra", "kist", "khata", "labh", "labharthi", "sahkari", "muavza", "daur", "panjikaran"
}

ENGLISH_INDICATORS = {
    "what", "how", "when", "where", "why", "who", "which",
    "is", "are", "was", "were", "am", "be", "been", "being",
    "do", "does", "did", "have", "has", "had", "can", "could", "will", "would", "shall", "should", "may", "might", "must",
    "the", "this", "that", "these", "those", "my", "your", "his", "her", "their", "our", "its",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "us", "them",
    "for", "with", "from", "about", "into", "through", "during", "before", "after",
    "please", "tell", "explain", "process", "procedure", "claim", "insurance",
    "document", "documents", "required", "eligibility", "eligible", "status", "apply", "application",
    "deadline", "helpline", "contact", "download", "damage", "damaged", "compensation", "officer",
    "authority", "department", "cooperative", "complaint", "grievance", "register", "help"
}

PDF_KEYWORDS_RE = re.compile(
    r"\b(pdf|download\s+pdf|make\s+a?\s*pdf|generate\s+pdf|pdf\s+bana|pdf\s+chahiye|pdf\s+banao|pdf\s+nikalo|print\s+pdf)\b",
    re.IGNORECASE
)

QR_SPOKEN_INVITE = {
    "en": "For the complete step by step guide, checklist, and PDF download, please scan the QR code on the screen with your phone.",
    "hi": "पूरी विस्तृत जानकारी, चेकलिस्ट और PDF डाउनलोड के लिए स्क्रीन पर दिए गए QR कोड को अपने मोबाइल फोन से स्कैन करें।",
}

PDF_CONFIRM_TEXT = {
    "en": "I have generated your Sahayak Action Guide PDF. You can save or print it for your records.",
    "hi": "मैंने आपकी सहायता कार्य योजना का PDF तैयार कर दिया है। आप इसे सेव या प्रिंट कर सकते हैं।",
}

NO_EVIDENCE = {
    "en": "I could not verify this from the available information yet. Please try asking differently, or check with your cooperative office directly.",
    "hi": "मुझे इसकी पुष्टि उपलब्ध जानकारी से नहीं मिली। कृपया अलग तरीके से पूछें या सहकारी कार्यालय से संपर्क करें।",
}
HANDOFF_TEXT = {
    "en": "This needs your camera or a longer form - your phone works better for it. Scan the QR to continue there.",
    "hi": "यह काम आपके कैमरे या लंबे फॉर्म से जुड़ा है - फोन पर बेहतर होगा। जारी रखने के लिए QR स्कैन करें।",
}


def detect_language_style(text: str, default_lang: Optional[str] = None) -> str:
    """
    Automatically identifies whether user input is Hindi (Devanagari or Romanized Hindi)
    or English, returning 'hi' or 'en'. Hinglish speech/mode is removed: any Hindi or
    Romanized Hindi query maps directly to pure Hindi ('hi') in Devanagari script.
    """
    if not text or not text.strip():
        if default_lang in ["hi", "en"]:
            return default_lang
        return "hi"

    # 1. Any Devanagari script is conclusively Hindi
    if DEVANAGARI_RE.search(text):
        return "hi"

    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    if not words:
        if default_lang in ["hi", "en"]:
            return default_lang
        return "hi"

    word_set = set(words)
    hinglish_matches = word_set.intersection(HINGLISH_MARKERS)
    english_matches = word_set.intersection(ENGLISH_INDICATORS)

    h_count = len(hinglish_matches)
    e_count = len(english_matches)

    # 2. Check for distinct Hindi/Romanized markers or grammatical particles -> map to pure Hindi
    strong_hindi = any(w in word_set for w in [
        "kaise", "kya", "chahiye", "batao", "bataiye", "bataye", "milega", "milegi", "milenge",
        "kare", "karein", "karna", "karo", "nuksan", "kharab", "barbad", "mera", "meri", "mere",
        "mujhe", "mujhko", "nahi", "nhi", "hoga", "hogi", "aayega", "aayegi", "darj", "paise", "paisa",
        "fasal", "bima", "kisan", "zameen", "zamin", "shikayat", "aavedan", "kist"
    ])

    if strong_hindi or (h_count > 0 and h_count >= e_count):
        return "hi"

    # 3. Pure English check
    if e_count > 0:
        return "en"

    # 4. Fallback gracefully
    if default_lang in ["hi", "en"]:
        return default_lang
    return "hi" if h_count > 0 else "en"


def build_actionable_kiosk_summary(
    answer: str,
    action_plan_out: Optional[schemas.ActionPlanOut],
    llm_kiosk_summary: Optional[str],
    lang_style: str
) -> str:
    """
    Constructs a complete, concrete, and actionable spoken/visual summary for the kiosk
    so that a citizen listening to the kiosk immediately understands:
    1. The core actions to take
    2. The documents to gather
    3. The deadline and where to submit / who to call.
    """
    if llm_kiosk_summary and len(llm_kiosk_summary.split("\n")) >= 3:
        lower = llm_kiosk_summary.lower()
        if any(w in lower for w in ["करें", "कदम", "चाहिए", "घंटे", "दस्तावेज़", "hours", "step", "submit", "document", "call", "14447"]):
            return llm_kiosk_summary.strip()

    if action_plan_out and action_plan_out.steps:
        steps_lines = "\n".join(f"• {s}" for s in action_plan_out.steps[:3])
        docs_text = ", ".join(action_plan_out.documents_required[:4]) if action_plan_out.documents_required else ""
        warn_text = action_plan_out.warnings[0] if action_plan_out.warnings else ""

        if lang_style == "hi":
            res = f"तुरंत करने योग्य मुख्य कदम:\n{steps_lines}"
            if docs_text:
                res += f"\n• ज़रूरी कागज़ात: {docs_text}"
            if warn_text:
                res += f"\n• महत्वपूर्ण नियम: {warn_text}"
            res += "\n• सहायता: टोल-फ्री 14447 (किसान कॉल सेंटर) पर कॉल करें।"
            return res
        else:
            res = f"Key Action Steps to Solve This:\n{steps_lines}"
            if docs_text:
                res += f"\n• Required Documents: {docs_text}"
            if warn_text:
                res += f"\n• Important: {warn_text}"
            res += "\n• Helpline: Call toll-free 14447 (Kisan Call Center)."
            return res

    lines = [l.strip() for l in answer.split("\n") if l.strip()]
    action_lines = []
    for line in lines:
        lower = line.lower()
        if any(h in lower for h in ["problem summary", "समस्या का विवरण", "1. समस्या", "overview"]) and len(line) < 100:
            continue
        if (line.startswith(("-", "•", "*", "1.", "2.", "3.", "4.", "5.", "Step", "कदम")) or
            any(kw in line for kw in ["चाहिए", "करें", "दें", "ले जाएं", "जमा", "हेल्पलाइन", "घंटे", "hours", "submit", "step", "call", "document", "contact", "72"])):
            action_lines.append(line)

    if action_lines and len(action_lines) >= 2:
        return "\n".join(action_lines[:5])

    return "\n".join(lines[:4])


def handle_message(db: DBSession, session: models.Session, text: str, language: str) -> schemas.ChatResponse:
    req_lang = language or session.language or "en"
    lang_style = detect_language_style(text, req_lang)
    if session.language != lang_style:
        session.language = lang_style
        db.commit()
    intent_name, confidence, entities = classify_intent(text)
    forced_complex = is_complex(text)
    is_pdf_req = bool(PDF_KEYWORDS_RE.search(text))

    hits = score_chunks(db, text, top_k=3)
    chunks = [c for c, _score in hits]

    sources: List[schemas.SourceOut] = []
    for c, sc in hits:
        doc = db.get(models.Document, c.document_id)
        if doc:
            sources.append(schemas.SourceOut(
                document_id=doc.id, title=doc.title, issuer=doc.issuer,
                source_url=doc.source_url, last_verified_at=doc.last_verified_at,
                relevance=sc,
            ))

    action_plan_row = build_action_plan(db, session.id, chunks) if chunks else None
    action_plan_out = None
    if action_plan_row:
        action_plan_out = schemas.ActionPlanOut(
            title=action_plan_row.title, steps=action_plan_row.steps,
            documents_required=action_plan_row.documents_required, warnings=action_plan_row.warnings,
        )

    llm = get_llm_provider()
    evidence_texts = [c.text for c in chunks] if chunks else []
    kiosk_summary: Optional[str] = None
    qr_data = None

    # Detect pure nonsense / random characters (e.g. "asdkjqwe nonsense gibberish xyz123")
    q_words = re.findall(r"\w+", text.lower())
    known_markers = HINGLISH_MARKERS.union(ENGLISH_INDICATORS).union({
        "जमीन", "कब्जा", "कब्ज़ा", "मदद", "सहायता", "बताओ", "क्या", "कैसे", "कहाँ", "कब", "नमस्ते", "हेलो",
        "fasal", "crop", "kisan", "farmer", "loan", "kcc", "pacs", "bima", "claim", "police", "court"
    })
    is_recognized_query = bool(set(q_words).intersection(known_markers)) or (DEVANAGARI_RE.search(text) is not None)

    if is_pdf_req:
        response_mode = "SCREEN_SUMMARY"
        answer = PDF_CONFIRM_TEXT.get(lang_style, PDF_CONFIRM_TEXT["en"])
        spoken_text = clean_for_speech(answer, lang_style)
    elif forced_complex:
        response_mode = "MOBILE_HANDOFF"
        answer = HANDOFF_TEXT.get(lang_style, HANDOFF_TEXT["en"])
        kiosk_summary = answer
        qr_obj = create_qr_session(db, session.id)
        qr_data = {"token": qr_obj.token, "join_url": f"/mobile/?token={qr_obj.token}", "expires_at": qr_obj.expires_at}
        invite = QR_SPOKEN_INVITE.get(lang_style, QR_SPOKEN_INVITE["en"])
        spoken_text = clean_for_speech(f"{answer}. {invite}", lang_style)
    elif intent_name == "UNKNOWN" and not chunks and not is_recognized_query:
        response_mode = "HUMAN_ESCALATION"
        answer = NO_EVIDENCE.get(lang_style, NO_EVIDENCE["en"])
        sources = []
        spoken_text = clean_for_speech(answer, lang_style)
    elif (fact_type := requires_specific_fact(text)) and not evidence_has_fact([c.text for c in chunks], fact_type, text):
        response_mode = "HUMAN_ESCALATION"
        sources = []
        bundle = llm.generate_response_bundle(text, evidence_texts, lang_style)
        answer = bundle.get("answer_text") or NO_EVIDENCE.get(lang_style, NO_EVIDENCE["en"])
        kiosk_summary = bundle.get("kiosk_summary")
        spoken_text = clean_for_speech(kiosk_summary or answer, lang_style)
    elif missing_named_entity(text, [c.text for c in chunks]):
        response_mode = "HUMAN_ESCALATION"
        sources = []
        bundle = llm.generate_response_bundle(text, evidence_texts, lang_style)
        answer = bundle.get("answer_text") or NO_EVIDENCE.get(lang_style, NO_EVIDENCE["en"])
        kiosk_summary = bundle.get("kiosk_summary")
        spoken_text = clean_for_speech(kiosk_summary or answer, lang_style)
    else:
        bundle = llm.generate_response_bundle(text, evidence_texts, lang_style)
        answer = bundle.get("answer_text") or NO_EVIDENCE.get(lang_style, NO_EVIDENCE["en"])
        kiosk_summary = bundle.get("kiosk_summary")

        # Response mode classification conforming to architectural specification
        response_mode = "SCREEN_SUMMARY" if (len(answer) > 140 or "\n" in answer or action_plan_out) else "SPEECH_ONLY"

        is_complex_solution = (
            (action_plan_out is not None) or
            (kiosk_summary is not None and len(answer) > 180) or
            len(answer) > 250 or
            (intent_name in ("agri_insurance", "grievance", "cooperative_governance") and len(answer) > 150)
        )

        if is_complex_solution:
            kiosk_summary = build_actionable_kiosk_summary(answer, action_plan_out, kiosk_summary, lang_style)
            qr_obj = create_qr_session(db, session.id)
            qr_data = {"token": qr_obj.token, "join_url": f"/mobile/?token={qr_obj.token}", "expires_at": qr_obj.expires_at}
            invite = QR_SPOKEN_INVITE.get(lang_style, QR_SPOKEN_INVITE["en"])
            spoken_text = clean_for_speech(f"{kiosk_summary}. {invite}", lang_style)
        else:
            kiosk_summary = None
            spoken_text = clean_for_speech(answer, lang_style)

    user_msg = models.Message(session_id=session.id, role="user", text=text,
                               intent=intent_name, confidence=confidence, entities=entities)
    db.add(user_msg)
    assistant_msg = models.Message(session_id=session.id, role="assistant", text=answer,
                                    intent=intent_name, response_mode=response_mode)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    for s in sources:
        db.add(models.SourceCitation(message_id=assistant_msg.id, document_id=s.document_id,
                                      chunk_id="", relevance=s.relevance))
    db.commit()

    from urllib.parse import quote
    audio_url = f"/voice/tts?text={quote(spoken_text)}&language={lang_style}"

    return schemas.ChatResponse(
        answer_text=answer,
        spoken_text=spoken_text,
        kiosk_summary=kiosk_summary,
        response_mode=response_mode,
        intent=intent_name,
        action_plan=action_plan_out,
        sources=sources,
        qr=qr_data,
        language=lang_style,
        confidence=confidence,
        trigger_pdf=is_pdf_req,
        audio_url=audio_url,
    )
