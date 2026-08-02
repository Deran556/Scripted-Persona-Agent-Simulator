"""
auto_test.py - Automated LLM-vs-LLM Simulation & Evaluation Framework

Changes from previous version:
- PatientAgent.step() now maintains its own local state dict (no global hidden_state dependency).
- Simulation loop breaks early when conversation_end=True OR pharmacist signals [DONE].
- run_automated_test() documents both early-stop conditions.
"""

import json
import time
from typing import Dict, Any, List
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# Workspace Integration & Fallback Imports
# ---------------------------------------------------------------------------
try:
    from config import TEST_AGENT_API_KEY, TEST_AGENT_MODEL
    from models import EvaluationReport
    from agent import ask_agent, reset_agent, create_patient
    from state_machine import make_initial_state, can_reveal_secret
except ImportError:
    TEST_AGENT_API_KEY = "YOUR_GEMINI_API_KEY"
    TEST_AGENT_MODEL = "gemini-2.5-flash"
    EvaluationReport = None

# Initialize Google GenAI Client for the Test Agents (Pharmacist & Evaluator)
client = genai.Client(api_key=TEST_AGENT_API_KEY)


# ===========================================================================
# 1. Patient Agent Wrapper (Target under Test)
# ===========================================================================
class PatientAgent:
    """
    Adapter wrapper for the Patient Agent under test.
    Maintains its own local state and dialogue_history (no global variables).
    """

    def __init__(self, difficulty: str = None):
        # Each test instance gets its own isolated state dict
        self.state = make_initial_state()
        self.patient = create_patient(difficulty=difficulty)
        self.dialogue_history: List[Dict[str, str]] = []

    def step(self, pharmacist_text: str, turn: int, action: str = "NONE") -> Dict[str, Any]:
        """
        Executes one interaction turn. Returns reply + updated metrics.

        Mirrors app.py's behavior: when an action is selected, the message sent to the
        patient agent is wrapped as "Action:\\n<ACTION>\\n\\nMessage:\\n<text>" instead of
        the raw text, so the patient LLM can detect medicine dispensed / payment done.
        """
        if action and action != "NONE":
            full_user_input = f"Action:\n{action}\n\nMessage:\n{pharmacist_text}"
        else:
            full_user_input = pharmacist_text

        self.dialogue_history.append({"role": "user", "content": full_user_input})

        reply_text, trace_info = ask_agent(
            user_input=full_user_input,
            state=self.state,
            patient=self.patient,
            dialogue_history=self.dialogue_history,
            turn=turn
        )

        self.dialogue_history.append({"role": "assistant", "content": reply_text})

        return {
            "text": reply_text,
            "trust": self.state.get("trust", 50),
            "patience": self.state.get("patience", 100),
            "stress": self.state.get("stress", 0),
            "conversation_end": self.state.get("conversation_end", False),
            "hidden_info_unlocked": can_reveal_secret(self.state)
        }

    def get_profile(self) -> Dict[str, Any]:
        """Returns the active patient profile as a dict."""
        return self.patient.model_dump() if self.patient else {}


# ===========================================================================
# 2. Pharmacist Agent (AI 1)
# ===========================================================================
PHARMACIST_SYSTEM_PROMPT = """
You are a highly experienced, practical, and busy community pharmacist.
Your responses MUST be extremely concise, natural, and limited to 1-2 sentences maximum.
Conduct the consultation in Vietnamese.

--- ACTION MECHANISM (mirrors the real app's UI action bar) ---
In the real product, the pharmacist can attach ONE action tag to a message, exactly like clicking
a button in the UI before sending a chat message. You must use this mechanism to actually progress
and conclude the consultation — it is NOT optional flavor text, the patient agent looks for these
exact tags to know medicine was dispensed / payment was made.

Available actions (attach AT MOST ONE per turn, only when it truly applies):
- CHECK_PRESCRIPTION: use when you need to verify what the patient is currently taking / bringing a prescription.
- GIVE_MEDICINE: use ONLY once you have decided on and are handing over the actual medication.
- PAYMENT: use ONLY after GIVE_MEDICINE has already happened in a previous turn, when the patient is paying and the transaction is finishing.
- NONE: use for all normal conversational turns (asking questions, giving advice, warnings) where no physical action is happening yet.

Format your output EXACTLY as:
ACTION: <CHECK_PRESCRIPTION|GIVE_MEDICINE|PAYMENT|NONE>
SAY: <your 1-2 sentence spoken line in Vietnamese>

Clinical & Behavioral Guidelines:
1. Direct Requests: Briefly warn about critical contraindications, then proceed if the patient insists.
2. Symptom Consultations: Ask 1-2 targeted SCHOLAR-MAC questions before recommending anything.
3. Handling Resistance: Give a quick safety warning, but keep probing gently rather than abandoning the consultation — do not finalize just because the patient hesitates once.
4. REQUIRED FLOW before ending: (a) gather enough history to make a safe recommendation, (b) use CHECK_PRESCRIPTION if the patient mentions other medicines/herbal remedies, (c) use GIVE_MEDICINE when you hand over the product, (d) use PAYMENT when the patient pays, (e) only THEN say goodbye.
5. Early Stopping: Append the exact tag "[DONE]" at the end of SAY ONLY on the turn where you use the PAYMENT action AND you are also saying goodbye. Never append [DONE] before PAYMENT has happened.

Output ONLY the two lines above (ACTION: and SAY:). No markdown, no stage directions, no extra commentary.
"""

def run_pharmacist_agent(history_logs: List[Dict[str, Any]], current_turn: int) -> Dict[str, str]:
    """Generates the Pharmacist Agent's action + concise spoken dialogue."""
    dialogue_history = []
    for log in history_logs:
        action_note = f" [action: {log.get('pharmacist_action', 'NONE')}]" if log.get("pharmacist_action", "NONE") != "NONE" else ""
        dialogue_history.append(f"Pharmacist{action_note}: {log['pharmacist_said']}")
        dialogue_history.append(f"Patient: {log['patient_said']}")

    if current_turn == 0:
        user_prompt = "Greet the patient warmly and ask what brings them to the pharmacy today. ACTION should be NONE."
    else:
        user_prompt = f"""
Conversation History:
{chr(10).join(dialogue_history)}

Formulate your NEXT turn: pick the appropriate ACTION (usually NONE, until the flow calls for
CHECK_PRESCRIPTION / GIVE_MEDICINE / PAYMENT) and a brief spoken line (1-2 sentences max).
Only append [DONE] to SAY if this turn's ACTION is PAYMENT and you are wrapping up.
"""

    response = client.models.generate_content(
        model=TEST_AGENT_MODEL,
        contents=f"{PHARMACIST_SYSTEM_PROMPT}\n\nTask:\n{user_prompt}",
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=200,
        ),
    )
    return _parse_pharmacist_output(response.text)


def _parse_pharmacist_output(raw_text: str) -> Dict[str, str]:
    """
    Parses the pharmacist LLM's 'ACTION: ...\nSAY: ...' format.
    Falls back gracefully if the model doesn't follow the format exactly.
    """
    text = raw_text.strip()
    action = "NONE"
    say = text

    lines = text.splitlines()
    action_line = next((l for l in lines if l.strip().upper().startswith("ACTION:")), None)
    say_line_idx = next((i for i, l in enumerate(lines) if l.strip().upper().startswith("SAY:")), None)

    if action_line:
        candidate = action_line.split(":", 1)[1].strip().upper()
        if candidate in ("CHECK_PRESCRIPTION", "GIVE_MEDICINE", "PAYMENT", "NONE"):
            action = candidate

    if say_line_idx is not None:
        say = "\n".join(lines[say_line_idx:]).split(":", 1)[1].strip()
    elif action_line:
        # ACTION present but no SAY line found; nothing else to fall back on
        say = ""

    say = say.strip('"\n ')
    return {"action": action, "say": say}


# ===========================================================================
# 3. Post-Simulation Evaluator (AI 2)
# ===========================================================================
EVALUATOR_SYSTEM_PROMPT = """
You are a QA AI and Medical Education Evaluator analyzing a simulated Patient Agent.

Review the conversation log and the Patient's true profile. Evaluate:
1. out_of_character (boolean): Did the patient stay in character?
2. emotion_logic_score (integer 1-10): Did trust/patience/stress update logically?
3. unlock_turn (integer): When did the patient reveal hidden info? -1 if never.
4. critique (string): Detailed feedback on persona consistency and interaction quality.

Output MUST be valid JSON adhering strictly to the schema.
"""

def run_evaluator(conversation_logs: List[Dict[str, Any]], patient_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Sends logs to the Evaluator LLM and returns structured JSON."""
    logs_json = json.dumps(conversation_logs, indent=2, ensure_ascii=False)
    profile_json = json.dumps(patient_profile, indent=2, ensure_ascii=False)

    eval_prompt = f"""
Patient Profile:
{profile_json}

Simulation Logs:
{logs_json}

Evaluate the simulation performance.
"""

    if EvaluationReport:
        response = client.models.generate_content(
            model=TEST_AGENT_MODEL,
            contents=f"{EVALUATOR_SYSTEM_PROMPT}\n\n{eval_prompt}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EvaluationReport,
                temperature=0.2,
            ),
        )
        return json.loads(response.text)
    else:
        response = client.models.generate_content(
            model=TEST_AGENT_MODEL,
            contents=f"{EVALUATOR_SYSTEM_PROMPT}\n\nReturn JSON.\n{eval_prompt}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        return json.loads(response.text)


# ===========================================================================
# 4. Simulation Execution & Output Logging
# ===========================================================================
def run_automated_test(max_turns: int = 12, report_path: str = "test_report.json") -> Dict[str, Any]:
    """
    Runs the simulation loop with TWO early-stop conditions:
    1. Patient agent returns conversation_end=True.
    2. Pharmacist agent outputs [DONE] flag.
    """
    print("=" * 65)
    print("🤖 Starting Automated LLM-vs-LLM Simulation & Evaluation Test")
    print("=" * 65)

    patient_agent = PatientAgent()
    patient_profile = patient_agent.get_profile()

    print(f"📋 Generated Patient Profile:")
    print(f"   Name: {patient_profile.get('name', 'N/A')}")
    print(f"   Age: {patient_profile.get('age', 'N/A')}")
    print(f" Personality: {patient_profile.get('personality', 'N/A')}")
    print(f"   Chief Complaint: {patient_profile.get('chief_complaint', 'N/A')}")
    print(f"   Hidden Information: {patient_profile.get('hidden_information', [])}")
    print("-" * 65)

    conversation_logs = []
    unlock_turn_detected = -1

    for turn in range(max_turns):
        print(f"\n💬 [Turn {turn + 1}/{max_turns}]")

        # --- Pharmacist speaks (and optionally acts) ---
        pharmacist_turn = run_pharmacist_agent(conversation_logs, current_turn=turn)
        pharmacist_action = pharmacist_turn["action"]
        raw_pharmacist_said = pharmacist_turn["say"]

        # Early stop condition 1: Pharmacist [DONE] flag — only honored if PAYMENT actually happened
        pharmacist_flagged_done = "[DONE]" in raw_pharmacist_said
        pharmacist_said = raw_pharmacist_said.replace("[DONE]", "").strip()
        pharmacist_done = pharmacist_flagged_done and pharmacist_action == "PAYMENT"

        action_note = f" [{pharmacist_action}]" if pharmacist_action != "NONE" else ""
        print(f"👨‍⚕️ Pharmacist{action_note}: {pharmacist_said}")
        if pharmacist_flagged_done and not pharmacist_done:
            print("   [Ignored premature [DONE] — PAYMENT action not yet issued]")
        elif pharmacist_done:
            print("   [Pharmacist signalled [DONE] after PAYMENT]")

        # --- Patient responds ---
        patient_res = patient_agent.step(pharmacist_said, turn=turn, action=pharmacist_action)
        patient_said = patient_res["text"]
        trust = patient_res["trust"]
        patience = patient_res["patience"]
        hidden_unlocked = patient_res["hidden_info_unlocked"]
        patient_ended = patient_res["conversation_end"]

        print(f"🧑 Patient: {patient_said}")
        print(f"   📊 Trust: {trust}/100 | Patience: {patience}/100 | Secret Unlocked: {hidden_unlocked} | Conv. End: {patient_ended}")

        if hidden_unlocked and unlock_turn_detected == -1:
            unlock_turn_detected = turn

        conversation_logs.append({
            "turn": turn,
            "pharmacist_action": pharmacist_action,
            "pharmacist_said": pharmacist_said,
            "patient_said": patient_said,
            "trust": trust,
            "patience": patience,
            "hidden_unlocked": hidden_unlocked,
            "conversation_end": patient_ended,
            "premature_done_flag": pharmacist_flagged_done and not pharmacist_done
        })

        # Early stop condition 2: Patient signals conversation_end
        if patient_ended:
            print("\n🏁 Patient signalled conversation_end=True. Stopping simulation.")
            break

        # Early stop condition 3: Pharmacist genuinely wrapped up (PAYMENT + [DONE])
        if pharmacist_done:
            print("\n🏁 Pharmacist completed PAYMENT and signalled [DONE]. Stopping simulation.")
            break

        time.sleep(1)

    # Post-simulation evaluation
    print("\n" + "=" * 65)
    print("🔍 Running Post-Simulation QA Evaluator (AI 2)...")
    print("=" * 65)

    evaluation_result = run_evaluator(conversation_logs, patient_profile)

    if evaluation_result.get("unlock_turn") == -1 and unlock_turn_detected != -1:
        evaluation_result["unlock_turn"] = unlock_turn_detected

    print("\n📊 QA Evaluation Results:")
    print(f"   - Out Of Character: {evaluation_result.get('out_of_character')}")
    print(f"   - Emotion Logic Score: {evaluation_result.get('emotion_logic_score')}/10")
    print(f"   - Unlock Turn: {evaluation_result.get('unlock_turn')}")
    print(f"   - Critique:\n{evaluation_result.get('critique')}\n")

    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "patient_profile": patient_profile,
        "conversation_logs": conversation_logs,
        "evaluation": evaluation_result
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Full test report saved to '{report_path}'!")
    return report_data


if __name__ == "__main__":
    run_automated_test(max_turns=12)