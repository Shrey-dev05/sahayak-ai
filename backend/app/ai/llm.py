"""
LLM provider adapter.

The orchestrator never calls an SDK directly - it calls `get_llm_provider()`
and uses the small interface below. This is the one place to touch when
wiring up a real model.

MockLLM (default, zero-config): does NOT generate free text. It returns the
retrieved chunk text as-is. This is deliberate for a prototype: it can never
hallucinate a fact, because it never invents a sentence - every word shown
to the user already existed in an approved document. That is a feature, not
a limitation, until a real model is wired up with the same evidence-first
prompting rules.

AnthropicLLM: a ready-to-enable adapter. To activate it:
  1. pip install anthropic
  2. export ANTHROPIC_API_KEY=...
  3. export LLM_PROVIDER=anthropic
It sends ONLY the retrieved evidence + the user's question, with a system
prompt that forbids answering beyond the evidence (see PROMPT below) -
matching the plan's "evidence-first answering, no invented facts" rule.
"""
from typing import List
from app.core.config import LLM_PROVIDER, GEMINI_API_KEY, GEMINI_MODEL
import httpx

PROMPT = (
    "You are Sahayak, a rural cooperative/governance assistant. Answer ONLY "
    "using the evidence passages given. Use simple language. If the evidence "
    "does not contain the answer, say you could not verify it - never invent "
    "facts, deadlines, phone numbers or eligibility rules. Reply in {language}."
)


class LLMProvider:
    def simplify_and_answer(self, question: str, evidence: List[str], language: str) -> str:
        raise NotImplementedError

    def generate_response_bundle(self, question: str, evidence: List[str] = None, language: str = "en") -> dict:
        ans = self.simplify_and_answer(question, evidence or [], language)
        return {"answer_text": ans, "kiosk_summary": None}


class MockLLM(LLMProvider):
    """Extractive stand-in: returns the strongest evidence passage verbatim."""

    def simplify_and_answer(self, question: str, evidence: List[str], language: str) -> str:
        if not evidence:
            return ""
        return evidence[0]

    def generate_response_bundle(self, question: str, evidence: List[str] = None, language: str = "en") -> dict:
        if not evidence:
            return {"answer_text": "", "kiosk_summary": None}
        ans = evidence[0]
        summary = (ans.split(".")[0] + ".") if "." in ans else ans[:140]
        return {"answer_text": ans, "kiosk_summary": summary}


INTELLIGENT_SAHAYAK_SYSTEM_PROMPT = """You are Sahayak AI, an intelligent, empathetic, and knowledgeable assistant for rural farmers, cooperative members, and citizens.

Core Instructions:
1. Provide practical, accurate, and constructive solutions to ANY question asked by the user, covering agriculture, crop advisory, pest and disease management, farming techniques, cooperative societies (PACS, DCCBs), credit & loans (KCC), government schemes (PM-KISAN, PMFBY, AIF, etc.), financial literacy, grievance redressal, and rural problem-solving.
2. When VERIFIED CONTEXT is provided below, treat it as the authoritative local reference and incorporate its facts, deadlines, and guidelines into your answer.
3. When verified context is not provided or the user asks something beyond pre-indexed documents, use your own intelligence, reasoning, and domain knowledge to provide a helpful, step-by-step solution. Never refuse with a dead-end rejection.
4. Tone & Style:
   - Respectful, encouraging, and direct.
   - Use clear formatting with bullet points or numbered action steps where helpful.
   - For contested legal disputes, provide practical guidance and recommend consulting the appropriate Registrar or official authority.
"""


class GeminiLLM(LLMProvider):
    """
    Google Gemini Free Model integration with autonomous intelligence.
    Grounded in verified knowledge when available; uses broad intelligence
    and reasoning to solve any problem in English, Hindi, or Hinglish.
    """

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or GEMINI_MODEL or "gemini-3.8-flash"

    def generate_response_bundle(self, question: str, evidence: List[str] = None, language: str = "en") -> dict:
        if not self.api_key:
            return self._build_offline_fallback(question, evidence, language)

        if evidence and len(evidence) > 0:
            context_block = "VERIFIED CONTEXT FROM APPROVED KNOWLEDGE BASE:\n" + "\n\n".join(f"- {e}" for e in evidence)
        else:
            context_block = "VERIFIED CONTEXT: (No pre-indexed document found. Use your own intelligence, agricultural expertise, and domain knowledge to provide a complete, practical solution.)"

        lang_lower = (language or "en").lower()
        if "hi" in lang_lower:
            lang_instruction = "CRITICAL LANGUAGE REQUIREMENT: You MUST reply strictly in fluent, respectful, grammatically correct pure Hindi in Devanagari script (हिंदी लिपि). Do NOT use Hinglish or Roman script."
        else:
            lang_instruction = "CRITICAL LANGUAGE REQUIREMENT: You MUST reply strictly in clear, direct, and accessible pure English."

        prompt_content = (
            f"{INTELLIGENT_SAHAYAK_SYSTEM_PROMPT}\n\n"
            f"{context_block}\n\n"
            f"{lang_instruction}\n\n"
            f"USER QUESTION:\n{question}\n\n"
            f"RESPONSE FORMAT INSTRUCTIONS:\n"
            f"If this is a problem, farming issue, scheme inquiry, crop damage claim, or loan/grievance question, format your response in TWO clearly marked sections:\n\n"
            f"[KIOSK_SUMMARY]\n"
            f"CRITICAL: This summary will be SPOKEN ALOUD and displayed on the physical touch-screen kiosk.\n"
            f"The citizen listening to the kiosk MUST be able to understand EXACTLY WHAT TO DO just by listening to this summary!\n"
            f"It must clearly state in 3-4 simple, concrete bullet points:\n"
            f"• The immediate action to take (e.g. reporting within 72 hours under PMFBY).\n"
            f"• What documents/proof to gather (e.g. damage photos, Aadhaar, bank passbook, land 7/12 papers).\n"
            f"• Where to go or who to contact (e.g. PACS, CSC center, bank branch, or toll-free helpline 14447).\n"
            f"Do NOT just repeat the problem statement! State the concrete solution steps so anyone listening immediately understands what to do!\n\n"
            f"[DETAILED_SOLUTION]\n"
            f"(A complete, simple, and step-by-step guide for a rural citizen on their mobile phone. Include: Problem Overview, Documents Needed Checklist, Step-by-Step Actions, Warnings/Deadlines like 72h window, and Helpline Numbers if applicable)\n\n"
            f"If the question is a brief greeting or simple one-line definition, you may provide a direct single answer without the tags."
        )

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt_content}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1200,
            }
        }

        # Try designated model, with fallbacks to other active models
        models_to_try = [self.model, "gemini-3.8-flash", "gemini-flash-latest", "gemini-3.7-flash"]
        seen = set()
        candidate_models = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

        for m in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={self.api_key}"
            try:
                with httpx.Client(timeout=30.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            # Exclude internal reasoning/thought if present
                            answer_parts = [
                                p.get("text", "") for p in parts
                                if "text" in p and not p.get("thought", False)
                            ]
                            if not answer_parts:
                                answer_parts = [p.get("text", "") for p in parts if "text" in p]
                            res_text = "\n".join(answer_parts).strip()
                            if res_text:
                                if "[KIOSK_SUMMARY]" in res_text and "[DETAILED_SOLUTION]" in res_text:
                                    s_parts = res_text.split("[DETAILED_SOLUTION]")
                                    k_sum = s_parts[0].replace("[KIOSK_SUMMARY]", "").strip()
                                    d_sol = s_parts[1].strip() if len(s_parts) > 1 else k_sum
                                    # Ensure kiosk summary is truly actionable
                                    if len(k_sum) > 30 and ("problem summary" not in k_sum.lower() or len(k_sum.split("\n")) > 2):
                                        return {"answer_text": d_sol, "kiosk_summary": k_sum}
                                    # If kiosk part was just a heading, use detailed solution
                                    return {"answer_text": d_sol, "kiosk_summary": self._extract_actionable_lines(d_sol)}
                                elif "[KIOSK_SUMMARY]" in res_text:
                                    clean = res_text.replace("[KIOSK_SUMMARY]", "").strip()
                                    return {"answer_text": clean, "kiosk_summary": clean}
                                elif "[DETAILED_SOLUTION]" in res_text:
                                    clean = res_text.replace("[DETAILED_SOLUTION]", "").strip()
                                    return {"answer_text": clean, "kiosk_summary": self._extract_actionable_lines(clean)}
                                else:
                                    # Fallback parsing if LLM didn't include tags
                                    actionable_summary = self._extract_actionable_lines(res_text)
                                    return {"answer_text": res_text, "kiosk_summary": actionable_summary}
            except Exception:
                continue

        # Safe fallback if API is unreachable or rate limited
        return self._build_offline_fallback(question, evidence, language)

    def _build_offline_fallback(self, question: str, evidence: List[str] = None, language: str = "en") -> dict:
        lang_lower = (language or "en").lower()
        is_hindi = "hi" in lang_lower
        q_lower = (question or "").lower()

        # 1. If evidence passages exist in approved knowledge base, prioritize them
        if evidence and len(evidence) > 0:
            primary_evidence = "\n\n".join(evidence[:3])
            summary = self._extract_actionable_lines(evidence[0])
            return {
                "answer_text": primary_evidence,
                "kiosk_summary": summary
            }

        # 2. Knowledge domain detection for intelligent offline responses
        if any(w in q_lower for w in ["fasal", "crop", "nuksan", "damage", "barish", "rain", "flood", "pmfby", "bima", "claim"]):
            if is_hindi:
                kiosk_summary = (
                    "• 72 घंटे के भीतर प्रधानमंत्री फसल बीमा योजना (PMFBY) पोर्टल, बैंक या टोल-फ्री 14447 पर सूचना दें।\n"
                    "• खेत में खराब फसल की फोटो, आधार कार्ड, बैंक पासबुक और खसरा/खतौनी के कागजात तैयार रखें।\n"
                    "• नजदीकी पैक्स (PACS), सीएससी (CSC) केंद्र या कृषि समन्वयक से तुरंत संपर्क करें।"
                )
                answer_text = (
                    "फसल नुकसान दावा प्रक्रिया (PMFBY Guide):\n\n"
                    "1. तत्काल सूचना (72 घंटे की समय-सीमा):\n"
                    "बाढ़, भारी बारिश या प्राकृतिक आपदा से फसल खराब होने पर 72 घंटे के भीतर संबंधित बैंक, बीमा कंपनी या राष्ट्रीय टोल-फ्री नंबर 14447 पर सूचित करें।\n\n"
                    "2. आवश्यक दस्तावेज़:\n"
                    "- आधार कार्ड और बैंक पासबुक की प्रति\n"
                    "- भूमि स्वामित्व दस्तावेज (खसरा/खतौनी या 7/12)\n"
                    "- फसल बुवाई प्रमाण पत्र (पटवारी/गिरदावरी रिपोर्ट)\n"
                    "- नुकसानग्रस्त फसल की स्पष्ट तस्वीरें\n\n"
                    "3. संपर्क केंद्र:\n"
                    "नजदीकी पैक्स (PACS) कार्यालय, कॉमन सर्विस सेंटर (CSC) या स्थानीय कृषि विस्तार अधिकारी से तत्काल संपर्क करें।"
                )
            else:
                kiosk_summary = (
                    "• Report crop loss within 72 hours via PMFBY portal, your bank branch, or toll-free helpline 14447.\n"
                    "• Gather damage photos, Aadhaar card, bank passbook, and land ownership (7/12 or Khasra) documents.\n"
                    "• Contact your local PACS, CSC center, or District Agriculture Officer immediately."
                )
                answer_text = (
                    "Crop Damage Claim Guide (PMFBY):\n\n"
                    "1. Immediate Notification (72-Hour Window):\n"
                    "In case of localized perils like flooding or unseasonal rain, report the loss within 72 hours to your bank, the insurance company, or toll-free 14447.\n\n"
                    "2. Required Documents:\n"
                    "- Aadhaar card & updated bank passbook\n"
                    "- Land records (Khasra/Khatauni or 7/12 extract)\n"
                    "- Sowing certificate / Girdawari report\n"
                    "- Clear photographs of the damaged crop\n\n"
                    "3. Where to Submit:\n"
                    "Submit claim forms at your servicing PACS, CSC Center, or District Agriculture Office."
                )
            return {"answer_text": answer_text, "kiosk_summary": kiosk_summary}

        if any(w in q_lower for w in ["kcc", "loan", "rin", "byaj", "karz", "interest", "credit"]):
            if is_hindi:
                kiosk_summary = (
                    "• किसान क्रेडिट कार्ड (KCC) पर समय पर भुगतान करने पर 3 लाख तक का ऋण केवल 4% प्रभावी ब्याज पर मिलता है।\n"
                    "• आवेदन के लिए जमीन की खतौनी, आधार कार्ड, पैन कार्ड और पासपोर्ट साइज फोटो लेकर जाएं।\n"
                    "• अपनी नजदीकी पैक्स (PACS) या बैंक शाखा में सीधे आवेदन करें।"
                )
                answer_text = (
                    "किसान क्रेडिट कार्ड (KCC) ब्याज सहायता व ऋण दिशानिर्देश:\n\n"
                    "1. ब्याज दर व सब्सिडी:\n"
                    "KCC पर सामान्य ब्याज दर 7% है। केंद्र सरकार समय पर भुगतान करने पर 3% अतिरिक्त ब्याज छूट प्रदान करती है, जिससे प्रभावी ब्याज केवल 4% रह जाता है।\n\n"
                    "2. आवश्यक दस्तावेज़:\n"
                    "- भरा हुआ KCC आवेदन पत्र\n"
                    "- पहचान व पता प्रमाण (आधार कार्ड, वोटर कार्ड)\n"
                    "- भूमि स्वामित्व अभिलेख (खसरा/खतौनी या लगान रसीद)\n"
                    "- बैंक खाता पासबुक और 2 पासपोर्ट फोटो\n\n"
                    "3. आवेदन स्थल:\n"
                    "अपनी प्राथमिक कृषि ऋण समिति (PACS), सहकारी बैंक या वाणिज्यिक बैंक शाखा से संपर्क करें।"
                )
            else:
                kiosk_summary = (
                    "• KCC offers agricultural loans up to Rs 3 Lakh at an effective 4% interest rate with prompt repayment.\n"
                    "• Required papers: Land ownership records (Khasra/7-12), Aadhaar card, bank passbook, and photos.\n"
                    "• Apply directly at your local PACS or nearest bank branch."
                )
                answer_text = (
                    "Kisan Credit Card (KCC) Scheme Guidelines:\n\n"
                    "1. Interest Rates & Subvention:\n"
                    "Base interest rate is 7% for crop loans up to Rs 3 Lakh. Farmers who repay on time receive a 3% prompt repayment incentive, reducing the effective rate to 4%.\n\n"
                    "2. Required Checklist:\n"
                    "- Duly filled KCC application form\n"
                    "- Aadhaar card & PAN/Voter ID\n"
                    "- Certified land revenue record (7/12 or Khasra/Khatauni)\n"
                    "- 2 passport-size photographs\n\n"
                    "3. Contact Point:\n"
                    "Apply through your local Primary Agricultural Credit Society (PACS) or servicing bank branch."
                )
            return {"answer_text": answer_text, "kiosk_summary": kiosk_summary}

        if any(w in q_lower for w in ["kisan", "pm-kisan", "pmkisan", "kist", "installment", "dbt", "samman"]):
            if is_hindi:
                kiosk_summary = (
                    "• पीएम-किसान योजना के तहत हर साल ₹6,000 तीन बराबर किस्तों (₹2,000 प्रत्येक) में डीबीटी के जरिए सीधे खाते में मिलते हैं।\n"
                    "• e-KYC पूरा होना, जमीन का सत्यापन (Land Seeding) और बैंक खाते का आधार से लिंक होना अनिवार्य है।\n"
                    "• स्थिति जांचने के लिए pmkisan.gov.in पर 'Know Your Status' देखें या 155261 पर कॉल करें।"
                )
                answer_text = (
                    "प्रधानमंत्री किसान सम्मान निधि (PM-KISAN) सहायता:\n\n"
                    "1. योजना का लाभ:\n"
                    "पात्र किसान परिवारों को प्रति वर्ष ₹6,000 की वित्तीय सहायता ₹2,000 की 3 किस्तों में सीधे बैंक खाते में दी जाती है।\n\n"
                    "2. किस्त रुकने के मुख्य कारण व समाधान:\n"
                    "- e-KYC अधूरा होना: नजदीकी CSC केंद्र पर बायोमेट्रिक या OTP से पूरा करें।\n"
                    "- आधार-बैंक सीडिंग: अपने बैंक में जाकर आधार NPCI मैपिंग कराएं।\n"
                    "- Land Seeding: राजस्व/कृषि अधिकारी से मिलकर भूमि विवरण सत्यापित कराएं।\n\n"
                    "3. आधिकारिक हेल्पलाइन: 155261 / 1800-115-526।"
                )
            else:
                kiosk_summary = (
                    "• PM-KISAN provides Rs 6,000 annually in 3 installments of Rs 2,000 via DBT directly to bank accounts.\n"
                    "• Mandatory checks: e-KYC completion, land seeding verification, and Aadhaar-linked bank account.\n"
                    "• Track status at pmkisan.gov.in under 'Know Your Status' or call helpline 155261."
                )
                answer_text = (
                    "PM-KISAN Scheme Overview & Problem Resolution:\n\n"
                    "1. Financial Benefit:\n"
                    "Eligible farmer families receive Rs 6,000 per year transferred in 3 equal installments of Rs 2,000 directly via DBT.\n\n"
                    "2. Essential Prerequisites:\n"
                    "- Complete e-KYC (via OTP on portal or biometric at CSC)\n"
                    "- Verify Land Seeding status with your local revenue/agriculture department\n"
                    "- Ensure bank account is mapped to Aadhaar via NPCI\n\n"
                    "3. Helpline Numbers: 155261 / 011-24300606."
                )
            return {"answer_text": answer_text, "kiosk_summary": kiosk_summary}

        if any(w in q_lower for w in ["pacs", "society", "samiti", "bylaw", "agm", "registrar", "member"]):
            if is_hindi:
                kiosk_summary = (
                    "• पैक्स (PACS) एक लोकतांत्रिक सहकारी संस्था है, जिसमें प्रत्येक सदस्य किसान को एक वोट का समान अधिकार है।\n"
                    "• वार्षिक आम बैठक (AGM) की सूचना 15 दिन पूर्व और न्यूनतम 20% कोरम होना अनिवार्य है।\n"
                    "• किसी भी अनियमितता की स्थिति में जिला सहायक निबंधक (ARCS) के समक्ष शिकायत दर्ज करें।"
                )
                answer_text = (
                    "पैक्स (PACS) मॉडल उपनियम व किसान अधिकार:\n\n"
                    "1. सदस्यता व मताधिकार:\n"
                    "PACS कार्यक्षेत्र का प्रत्येक किसान सदस्य बन सकता है। सभी सदस्यों को AGM में मतदान का समान अधिकार प्राप्त है।\n\n"
                    "2. बैठक व पारदर्शिता नियम:\n"
                    "- वार्षिक आम सभा (AGM) वित्तीय वर्ष समाप्ति के 6 माह के भीतर आयोजित होनी आवश्यक है।\n"
                    "- वित्तीय लेखापरीक्षा (Audit) रिपोर्ट सदस्यों के निरीक्षण हेतु उपलब्ध होनी चाहिए।\n\n"
                    "3. शिकायत निवारण:\n"
                    "अध्यक्ष या सचिव द्वारा नियमों का उल्लंघन किए जाने पर जिला सहकारी निबंधक (ARCS) को आवेदन प्रस्तुत करें।"
                )
            else:
                kiosk_summary = (
                    "• PACS is a democratic cooperative where every farmer member has equal voting rights.\n"
                    "• Annual General Meeting (AGM) requires 15 days advance notice and a minimum 20% quorum.\n"
                    "• For violations, submit a grievance to the District Assistant Registrar (ARCS)."
                )
                answer_text = (
                    "PACS Model Bylaws & Governance Framework:\n\n"
                    "1. Membership & Democratic Control:\n"
                    "Every farmer within the jurisdiction is entitled to regular membership with one member, one vote rights.\n\n"
                    "2. Meetings & Audits:\n"
                    "- The AGM must be convened within 6 months of financial year end.\n"
                    "- Annual audit reports and member registers must be available for inspection.\n\n"
                    "3. Redressal Channel:\n"
                    "Grievances regarding election, membership refusal, or fund mismanagement should be addressed to the District Registrar of Cooperative Societies."
                )
            return {"answer_text": answer_text, "kiosk_summary": kiosk_summary}

        # General rural citizen assistance
        if is_hindi:
            kiosk_summary = (
                "• कृषि, ऋण व फसल सहायता के लिए अपने नजदीकी पैक्स (PACS), सीएससी केंद्र या कृषि विभाग कार्यालय जाएं।\n"
                "• अपने साथ आधार कार्ड, जमीन के दस्तावेज व बैंक पासबुक अवश्य रखें।\n"
                "• राष्ट्रीय किसान कॉल सेंटर टोल-फ्री नंबर 1800-180-1551 पर कभी भी संपर्क करें।"
            )
            answer_text = (
                "सहायक AI नागरिक सहायता केंद्र:\n\n"
                "आपकी सहायता के लिए आधिकारिक मार्गदर्शन:\n"
                "1. कृषि परामर्श व योजनाएं: पीएम किसान, फसल बीमा (PMFBY), केसीसी ऋण व कृषि यंत्र अनुदान।\n"
                "2. आवश्यक पहचान प्रमाण: आधार कार्ड, बैंक खाता विवरण, और भूमि अभिलेख।\n"
                "3. आधिकारिक हेल्पलाइन: राष्ट्रीय किसान कॉल सेंटर 1800-180-1551 (टोल-फ्री)।"
            )
        else:
            kiosk_summary = (
                "• Visit your nearest PACS, CSC Center, or District Agriculture Office for scheme and credit support.\n"
                "• Always carry your Aadhaar card, land ownership papers, and bank passbook.\n"
                "• For immediate agricultural advisory, call the Kisan Call Center toll-free at 1800-180-1551."
            )
            answer_text = (
                "Sahayak AI Citizen Assistance:\n\n"
                "Official guidance for rural schemes and services:\n"
                "1. Available Services: PM-Kisan, Crop Insurance (PMFBY), KCC Loans, and cooperative society support.\n"
                "2. Required Documentation: Aadhaar card, bank passbook, and land ownership records.\n"
                "3. National Helpline: Kisan Call Center toll-free 1800-180-1551."
            )
        return {"answer_text": answer_text, "kiosk_summary": kiosk_summary}

    def _extract_actionable_lines(self, text: str) -> str:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            return text

        action_lines = []
        for line in lines:
            lower = line.lower()
            # Skip pure introductory problem restatement headings
            if any(h in lower for h in ["problem summary", "समस्या का विवरण", "1. समस्या", "overview"]) and len(line) < 100:
                continue
            # Pick lines that have bullet points, numbered steps, or concrete actions
            if (line.startswith(("-", "•", "*", "1.", "2.", "3.", "4.", "5.", "Step", "कदम")) or
                any(kw in line for kw in ["चाहिए", "करें", "दें", "ले जाएं", "जमा", "हेल्पलाइन", "घंटे", "hours", "submit", "step", "call", "document", "contact", "72"])):
                action_lines.append(line)

        if action_lines and len(action_lines) >= 2:
            return "\n".join(action_lines[:5])

        # If no explicit markers found, return the first 3-4 lines
        return "\n".join(lines[:4])

    def simplify_and_answer(self, question: str, evidence: List[str] = None, language: str = "en") -> str:
        bundle = self.generate_response_bundle(question, evidence, language)
        return bundle.get("answer_text", "")


class AnthropicLLM(LLMProvider):  # pragma: no cover - requires real credentials
    def __init__(self):
        import os
        import anthropic  # pip install anthropic
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def simplify_and_answer(self, question: str, evidence: List[str], language: str) -> str:
        joined = "\n\n".join(f"- {e}" for e in evidence)
        msg = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            system=PROMPT.format(language=language),
            messages=[{"role": "user", "content": f"Question: {question}\n\nEvidence:\n{joined}"}],
        )
        return "".join(b.text for b in msg.content if b.type == "text")


GROQ_SYSTEM_PROMPT = """You are Sahayak AI.
You help rural cooperative members understand:
- cooperative laws
- PACS
- government schemes
- agriculture
- crop insurance
- financial literacy
- grievances

IMPORTANT RULES:
1. Answer using the supplied VERIFIED CONTEXT.
2. Do not invent government facts.
3. Do not invent deadlines.
4. Do not invent eligibility criteria.
5. Do not invent phone numbers.
6. Do not invent government offices.
7. Do not invent URLs.
8. If the evidence is insufficient, say that it could not be verified.
9. Explain complex information in simple language.
10. Prefer the user's language.
11. Give practical next steps when supported by evidence.
12. Mention sources for important factual claims.
13. Do not present yourself as a lawyer.
14. For ambiguous legal matters, recommend the appropriate verified authority.

VERIFIED CONTEXT:
{context}"""


class GroqLLM(LLMProvider):  # pragma: no cover - requires a live Groq API key
    def __init__(self):
        import os
        from groq import Groq  # pip install groq
        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])

    def simplify_and_answer(self, question: str, evidence: List[str], language: str) -> str:
        context = "\n\n".join(f"- {e}" for e in evidence)
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            temperature=0.1,
            messages=[
                {"role": "system", "content": GROQ_SYSTEM_PROMPT.format(context=context)},
                {"role": "user", "content": question},
            ],
        )
        return response.choices[0].message.content


def get_llm_provider() -> LLMProvider:
    if LLM_PROVIDER == "gemini":
        return GeminiLLM()
    if LLM_PROVIDER == "anthropic":
        return AnthropicLLM()
    if LLM_PROVIDER == "groq":
        return GroqLLM()
    return MockLLM()
