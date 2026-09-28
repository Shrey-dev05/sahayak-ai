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
        self.model = model or GEMINI_MODEL or "gemini-3.5-flash-lite"

    def generate_response_bundle(self, question: str, evidence: List[str] = None, language: str = "en") -> dict:
        if not self.api_key:
            fb = evidence[0] if (evidence and len(evidence) > 0) else "Service temporarily offline. Please verify API key configuration."
            return {"answer_text": fb, "kiosk_summary": None}

        if evidence and len(evidence) > 0:
            context_block = "VERIFIED CONTEXT FROM APPROVED KNOWLEDGE BASE:\n" + "\n\n".join(f"- {e}" for e in evidence)
        else:
            context_block = "VERIFIED CONTEXT: (No pre-indexed document found. Use your own intelligence, agricultural expertise, and domain knowledge to provide a complete, practical solution.)"

        lang_lower = (language or "en").lower()
        if "hi" in lang_lower:
            lang_instruction = "CRITICAL LANGUAGE REQUIREMENT: You MUST reply strictly in fluent, respectful, grammatically correct pure Hindi in Devanagari script (हिंदी लिपि). Do NOT use Hinglish or Roman script."
        else:
            lang_instruction = (
                "CRITICAL LANGUAGE REQUIREMENT: You MUST reply strictly in clear, direct, and accessible pure English. "
                "If the user question was phonetically transcribed into Devanagari from English (for example 'समवन इस कैप्चरड माय लैंड इन लीगली व्हाट शोल्ड ई दो' "
                "which means 'Someone has captured my land illegally, what should I do?'), understand the English question and provide your complete, detailed response strictly in English. "
                "Never reply in Hindi if the question is asked in English."
            )

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

        # Try designated model, with fallbacks to other active models with generous free quotas
        models_to_try = [self.model, "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]
        seen = set()
        candidate_models = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

        for m in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={self.api_key}"
            try:
                with httpx.Client(timeout=12.0) as client:
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

        # Safe fallback if API is unreachable
        fb = evidence[0] if (evidence and len(evidence) > 0) else "I am here to assist you, but currently experiencing connectivity to the AI service. Please ask again shortly."
        return {"answer_text": fb, "kiosk_summary": None}

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
