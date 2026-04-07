"""
gemini_advisor.py
-----------------
Google Gemini-powered AI Career Advisor for the KUCCUPS AI Career Engine.

Usage:
    from models.gemini_advisor import GeminiAdvisor
    advisor = GeminiAdvisor(api_key="YOUR_KEY")
    response = advisor.chat(user_message, recommendations, student_context)
"""

from __future__ import annotations
import json
from typing import Any


# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------

def _build_system_prompt(recommendations: list[dict[str, Any]], student_context: dict[str, Any]) -> str:
    """
    Build a rich, context-aware system prompt so Gemini understands the
    student's profile, grades, eligibility and top career recommendations.
    """
    # ── Top 3 recommendations summary ──────────────────────────────────────
    rec_lines: list[str] = []
    for i, rec in enumerate(list(recommendations)[:5], 1):  # type: ignore[misc]
        dept: str    = str(rec.get("dept", "Unknown"))
        score: int   = int(rec.get("final_score", 0) * 100)
        jobs: Any    = rec.get("job_count", 0)
        status: str  = str(rec.get("dept_status", "UNKNOWN"))
        _progs: list = list(rec.get("programs", []))  # type: ignore[annotation-unchecked]
        programs: list[str] = [str(p) for p in _progs[:3]]
        uni_map: dict  = rec.get("university_mapping", {})  # type: ignore[annotation-unchecked]
        _skills: list  = list(rec.get("skills", []))  # type: ignore[annotation-unchecked]
        skills: list[str] = [str(s) for s in _skills[:4]]

        prog_detail = ""
        for prog in programs:
            unis = uni_map.get(prog, [])
            uni_str = ", ".join(unis[:2]) if unis else "KUCCPS-listed institutions"
            prog_detail += f"\n      • {prog} → {uni_str}"

        skill_str = ", ".join(str(s) for s in skills) if skills else "Core domain skills"

        rec_lines.append(
            f"  #{i}. {dept} | Match: {score}% | Status: {status} | Live Jobs (Kenya): {jobs}\n"
            f"      Top Skills: {skill_str}\n"
            f"      Programs:{prog_detail if prog_detail else ' (See KUCCPS portal)'}"
        )

    recs_text = "\n".join(rec_lines) if rec_lines else "  No recommendations computed yet."

    # ── Student academic context ────────────────────────────────────────────
    grades    = student_context.get("grades", {})
    interests = student_context.get("interests", "Not specified")
    target_q  = student_context.get("target_qualification", "All")
    mean_grade = student_context.get("mean_grade", "N/A")
    kcse_points = student_context.get("kcse_points", "N/A")

    grade_lines = ""
    if isinstance(grades, dict) and grades:
        grade_items = list(grades.items())  # type: ignore[misc]
        for subj, grade in grade_items[:10]:  # type: ignore[misc]
            grade_lines += f"\n    {subj}: {grade}"
    else:
        grade_lines = "\n    Not provided."

    prompt = f"""You are **KUCCUPS AI Career Advisor**, an expert Kenyan career guidance counsellor \
embedded inside the KUCCUPS AI Career Engine v2.2. Your role is to give precise, \
empathetic, and actionable career guidance to Kenyan secondary school leavers based \
on their KCSE results, interests, and KUCCPS eligibility data.

━━━━━━ STUDENT PROFILE ━━━━━━
• Target Qualification: {target_q}
• Mean Grade: {mean_grade}  |  Approximate Points: {kcse_points}
• Stated Interests / Passion: {interests}

KCSE Grades:{grade_lines}

━━━━━━ AI CAREER RECOMMENDATIONS (already computed) ━━━━━━
{recs_text}

━━━━━━ YOUR GUIDELINES ━━━━━━
1. **Always ground answers in the student's data above.** Never make up grades, programs,
   or universities that are not mentioned. If unsure, say so and direct them to kuccps.net.
2. **Be specific about Kenya**: salary ranges in KES, Kenyan institutions, KUCCPS procedures,
   HELB, county bursaries, etc.
3. **Be concise but complete** — use bullet points and bold text for clarity.
4. **Be encouraging** — many students feel anxious. Acknowledge their situation empathetically.
5. **For university/institution questions** — list from the recommendation data above.
   If not listed, say "Verify on kuccps.net" and give the step-by-step process.
6. **Do not answer questions unrelated to careers, education, or the Kenyan job market.**
   If off-topic, politely redirect.
7. **Use Markdown formatting** (bold, bullets, headers) as your responses are rendered in Streamlit.
"""
    return prompt


# ---------------------------------------------------------------------------
# GeminiAdvisor class
# ---------------------------------------------------------------------------

class GeminiAdvisor:
    """Thin wrapper around the Google Generative AI SDK for career advising."""

    # Fallback chain — confirmed available models (run ListModels to verify)
    # gemini-2.0-flash-lite is cheaper/lower quota than 2.0-flash
    MODEL_CHAIN = [
        "gemini-2.0-flash",          # fastest, primary
        "gemini-2.0-flash-lite",     # lighter quota, fallback #1
        "gemini-flash-lite-latest",  # alias, fallback #2
    ]
    MODEL_NAME  = MODEL_CHAIN[0]  # kept for test_connection()

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key.strip()
        self._client: Any = None
        self._available = False
        self._init_error: str = ""
        self._try_init()

    def _try_init(self) -> None:
        try:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=self.api_key)
            self._client = genai
            self._available = True
        except ImportError:
            self._init_error = (
                "The `google-generativeai` package is not installed. "
                "Run: pip install google-generativeai"
            )
        except Exception as e:
            self._init_error = f"Gemini init error: {e}"

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def error_message(self) -> str:
        return self._init_error

    # ── Main chat method ────────────────────────────────────────────────────

    def chat(
        self,
        user_message: str,
        history: list[dict[str, str]],
        recommendations: list[dict[str, Any]],
        student_context: dict[str, Any],
    ) -> str:
        """
        Send a message to Gemini with full student context baked into the
        system prompt.

        Args:
            user_message:     The latest user question.
            history:          List of {"role": "user"|"ai", "content": str}
                              messages (excluding the latest user message).
            recommendations:  Output list from the recommender engine.
            student_context:  Dict with keys: grades, interests, mean_grade,
                              kcse_points, target_qualification.

        Returns:
            AI response string.
        """
        if not self._available:
            return f"⚠️ **Gemini unavailable**: {self._init_error}"

        import google.generativeai as genai  # type: ignore
        try:
            from google.generativeai.types import HarmCategory, HarmBlockThreshold  # type: ignore
            safety = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH:       HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT:        HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        except Exception:
            safety = {}

        system_prompt = _build_system_prompt(recommendations, student_context)

        # Convert chat history to Gemini format
        gemini_history: list[dict[str, Any]] = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

        last_err = ""
        for model_name in self.MODEL_CHAIN:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_prompt,
                    safety_settings=safety,  # type: ignore[arg-type]
                )
                chat_session = model.start_chat(history=gemini_history)
                response = chat_session.send_message(user_message)
                return response.text
            except Exception as e:
                last_err = str(e)
                _e_low = last_err.lower()
                # Only retry next model on quota errors; fail fast on auth errors
                if "api_key_invalid" in _e_low or "api key not valid" in _e_low:
                    return (
                        "❌ **Invalid API Key.** Please generate a new key at "
                        "[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) "
                        "and update your `.env` file."
                    )
                if "quota" not in _e_low and "429" not in last_err:
                    # Non-quota error — don't bother trying other models
                    break
                # Quota error — try next model in chain
                continue

        # All models exhausted
        import re as _re
        retry_match = _re.search(r'retry in (\d+)', last_err)
        retry_secs  = retry_match.group(1) if retry_match else "60"
        return (
            f"⏳ **Quota exceeded on all available Gemini models.**\n\n"
            f"- Retry automatically in **{retry_secs} seconds**, or\n"
            f"- Generate a **new API key** at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) "
            f"(your current key has likely hit its daily free-tier limit)\n"
            f"- Or upgrade to a paid Gemini plan for higher quotas.\n\n"
            f"*The heuristic advisor is still available while you wait.*"
        )

    def test_connection(self) -> tuple[bool, str]:
        """Quick ping to verify the API key works, trying each model in the fallback chain."""
        if not self._available:
            return False, self._init_error
        try:
            import google.generativeai as genai  # type: ignore
            for model_name in self.MODEL_CHAIN:
                try:
                    model = genai.GenerativeModel(model_name)
                    model.generate_content("Reply with exactly: API OK")
                    return True, f"✅ Connected to Gemini! (model: **{model_name}**)"
                except Exception as e:
                    _e = str(e)
                    if "quota" in _e.lower() or "429" in _e:
                        continue  # try next model
                    return False, f"❌ {_e}"
            return False, (
                "❌ **All Gemini models hit quota.** Your free-tier daily limit is exhausted. "
                "Get a new key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)."
            )
        except Exception as e:
            return False, f"❌ {e}"
