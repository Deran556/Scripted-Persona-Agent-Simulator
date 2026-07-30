"""
auto_test.py - Automated LLM-vs-LLM Simulation & Evaluation Framework

This script implements an automated testing loop between:
1. Pharmacist Agent (AI 1): Uses SCHOLAR-MAC framework to assess the patient and uncover medical facts.
2. Patient Agent (Target): Evaluated agent returning text and emotional state (trust, patience, hidden_unlocked).
3. Post-Simulation Evaluator (AI 2): QA AI assessing persona consistency, emotion logic, unlock turn, and critique.
4. Output Logging: Exports complete simulation trace & evaluation results to `test_report.json`.
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
    from agent import ask_agent, reset_agent
    import agent
    from state_machine import hidden_state, can_reveal_secret
except ImportError:
    # Standalone fallback placeholders if imported externally
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
    Receives text and outputs a dictionary:
    {"text": str, "trust": int, "patience": int, "hidden_info_unlocked": bool}
    """

    def __init__(self, difficulty: str = None):
        # Reset agent state and create a new dynamic patient scenario
        self.patient = reset_agent(difficulty=difficulty)

    def step(self, pharmacist_text: str, turn: int) -> Dict[str, Any]:
        """
        Executes a single interaction step with the Patient Agent.
        """
        reply_text, trace_info = ask_agent(pharmacist_text, turn=turn)

        # Evaluate if hidden secrets are unlocked based on state machine rules
        secret_revealed = can_reveal_secret(hidden_state)

        return {
            "text": reply_text,
            "trust": hidden_state.get("trust", 50),
            "patience": hidden_state.get("patience", 100),
            "hidden_info_unlocked": secret_revealed
        }

    def get_profile(self) -> Dict[str, Any]:
        """Returns the active patient profile dictionary."""
        if agent.current_patient:
            return agent.current_patient.model_dump()
        return {}


# ===========================================================================
# 2. Pharmacist Agent (AI 1)
# ===========================================================================
PHARMACIST_SYSTEM_PROMPT = """
You are a highly experienced, practical, and busy community pharmacist. 
Your responses MUST be extremely concise, natural, and limited to 1-2 sentences maximum.
Start the conversation by Vietnamese.

Clinical & Behavioral Guidelines:
1. Direct Requests (The patient demands a specific drug by name): 
   - Do NOT interrogate them endlessly. 
   - Briefly warn them about critical side effects, contraindications, or interactions for safety.
   - Proceed to approve the sale if they insist.
2. Symptom Consultations (The patient describes a symptom and asks for advice): 
   - Ask 1-2 quick, targeted questions to assess the condition (using simplified SCHOLAR-MAC principles).
   - Recommend an appropriate OTC medication based on their answers.
3. Handling Resistance: 
   - If the patient is impatient, evasive, or refuses to answer your probing questions, do not force them. 
   - Give a quick, professional safety warning and finalize the transaction.
4. Early Stopping: 
   - When the transaction is successfully completed, or if you have given your safety warning and the patient insists on leaving with the drug, append the tag "[DONE]" at the very end of your response to signal the end of the simulation.

Output Requirements:
- Output ONLY your direct spoken dialogue. 
- Keep it short, sharp, and strictly professional (no lecturing).
- Do NOT include markdown quotes, labels, or stage directions.
"""

def run_pharmacist_agent(history_logs: List[Dict[str, Any]], current_turn: int) -> str:
    """
    Generates the Pharmacist Agent's spoken dialogue using SCHOLAR-MAC strategy.
    """
    dialogue_history = []
    for log in history_logs:
        dialogue_history.append(f"Pharmacist: {log['pharmacist_said']}")
        dialogue_history.append(f"Patient: {log['patient_said']}")

    if current_turn == 0:
        user_prompt = "Greet the patient warmly, express willingness to help, and ask what brings them to the pharmacy today."
    else:
        user_prompt = f"""
Conversation History:
{chr(10).join(dialogue_history)}

Based on the patient's last response and the SCHOLAR-MAC framework, formulate your next spoken utterance to build trust and uncover relevant health information.
Output ONLY your direct spoken dialogue.
"""

    response = client.models.generate_content(
        model=TEST_AGENT_MODEL,
        contents=f"{PHARMACIST_SYSTEM_PROMPT}\n\nTask:\n{user_prompt}",
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=300,
        ),
    )
    return response.text.strip('"\n ')


# ===========================================================================
# 3. Post-Simulation Evaluator (AI 2)
# ===========================================================================
EVALUATOR_SYSTEM_PROMPT = """
You are a QA AI and Medical Education Evaluator analyzing a simulated Patient Agent in a pharmacy training environment.

Review the complete conversation log and the Patient's true profile.
Analyze and evaluate:
1. out_of_character (boolean): Did the patient stay in character based on their personality and profile?
2. emotion_logic_score (integer 1-10): Did trust/patience update logically based on the pharmacist's empathy and probing questions?
3. unlock_turn (integer): At which turn index (0..max_turns-1) did the patient reveal their hidden secret/medical condition? Return -1 if never unlocked.
4. critique (string): Provide detailed, constructive feedback on persona consistency, emotion logic, and interaction quality.

Output MUST be valid JSON adhering strictly to the schema.
"""

def run_evaluator(conversation_logs: List[Dict[str, Any]], patient_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sends complete logs and profile to the Evaluator LLM and returns structured JSON output.
    """
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
            contents=f"{EVALUATOR_SYSTEM_PROMPT}\n\nReturn JSON output.\n{eval_prompt}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        return json.loads(response.text)


# ===========================================================================
# 4. Simulation Execution & Output Logging
# ===========================================================================
def run_automated_test(max_turns: int = 7, report_path: str = "test_report.json") -> Dict[str, Any]:
    """
    Runs the complete 7-turn simulation loop between Pharmacist Agent and Patient Agent,
    followed by AI QA evaluation and saving results to `test_report.json`.
    """
    print("=" * 65)
    print("🤖 Starting Automated LLM-vs-LLM Simulation & Evaluation Test")
    print("=" * 65)

    # Instantiate target Patient Agent under test
    patient_agent = PatientAgent()
    patient_profile = patient_agent.get_profile()

    print(f"📋 Generated Patient Profile:")
    print(f"   Name: {patient_profile.get('name', 'N/A')}")
    print(f"   Chief Complaint: {patient_profile.get('chief_complaint', 'N/A')}")
    print(f"   Hidden Information: {patient_profile.get('hidden_information', [])}")
    print("-" * 65)

    conversation_logs = []
    unlock_turn_detected = -1

    # Conversational loop for max_turns = 7
    for turn in range(max_turns):
        print(f"\n💬 [Turn {turn + 1}/{max_turns}]")

        # 1. Pharmacist Agent speaks
        pharmacist_said = run_pharmacist_agent(conversation_logs, current_turn=turn)
        print(f"👨‍⚕️ Pharmacist: {pharmacist_said}")

        # 2. Patient Agent responds and updates emotional state
        patient_res = patient_agent.step(pharmacist_said, turn=turn)
        patient_said = patient_res["text"]
        trust = patient_res["trust"]
        patience = patient_res["patience"]
        hidden_unlocked = patient_res["hidden_info_unlocked"]

        print(f"🧑 Patient: {patient_said}")
        print(f"   📊 State -> Trust: {trust}/100 | Patience: {patience}/100 | Secret Unlocked: {hidden_unlocked}")

        if hidden_unlocked and unlock_turn_detected == -1:
            unlock_turn_detected = turn

        # Append turn metrics to log
        turn_log = {
            "turn": turn,
            "pharmacist_said": pharmacist_said,
            "patient_said": patient_said,
            "trust": trust,
            "patience": patience,
            "hidden_unlocked": hidden_unlocked
        }
        conversation_logs.append(turn_log)

        time.sleep(1)

    print("\n" + "=" * 65)
    print("🔍 Running Post-Simulation QA Evaluator (AI 2)...")
    print("=" * 65)

    # 3. Post-simulation evaluation by AI 2
    evaluation_result = run_evaluator(conversation_logs, patient_profile)

    # Ensure unlock_turn is populated if state machine unlocked it
    if evaluation_result.get("unlock_turn") == -1 and unlock_turn_detected != -1:
        evaluation_result["unlock_turn"] = unlock_turn_detected

    print("\n📊 QA Evaluation Results:")
    print(f"   - Out Of Character: {evaluation_result.get('out_of_character')}")
    print(f"   - Emotion Logic Score: {evaluation_result.get('emotion_logic_score')}/10")
    print(f"   - Unlock Turn: {evaluation_result.get('unlock_turn')}")
    print(f"   - Critique:\n{evaluation_result.get('critique')}\n")

    # 4. Output logging to test_report.json
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
    run_automated_test(max_turns=7)
