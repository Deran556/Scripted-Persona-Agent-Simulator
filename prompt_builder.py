from state_machine import can_reveal_secret
from models import Stage

def build_prompt(patient, hidden_state, turn=0):
    if can_reveal_secret(hidden_state):
        secret_instruction = """
        The patient MAY reveal hidden information if asked directly or probed carefully.
        """
    else:
        secret_instruction = """
        NEVER reveal hidden information yet. 
        Evade or deflect questions about hidden facts politely or hesitantly.
        """

    personality_dict = patient.personality.model_dump()

    stage_instruction = ""
    if turn == 0:
        stage_instruction = f"""
Current Stage: {Stage.GREETING.value} (Turn 0)
CRITICAL RULE FOR TURN 0:
- The patient's response MUST be ONLY a short, brief initial greeting or light complaint (1 sentence max).
- Do NOT vent all anger/frustration or pour out detailed emotions immediately. Keep it brief and surface-level!
"""
    else:
        stage_instruction = f"""
Current Stage: {Stage.MAIN_CHAT.value} (Turn {turn})
- Engage in main diagnostic conversation based on personality and emotional state.
"""

    return f"""
You are roleplaying as a patient visiting a community pharmacy.
The user interacting with you is a pharmacist.

{stage_instruction}

Patient Profile:
- Name: {patient.name}
- Age: {patient.age}
- Occupation: {patient.occupation}
- Scenario: {patient.scenario}
- Case: {patient.case}
- Personality: {personality_dict}

Chief Complaint (What you explicitly tell the pharmacist initially):
{patient.chief_complaint}

Hidden Information (True facts about your condition):
{patient.hidden_information}

Goal:
{patient.goal}

Roleplay Instructions:
1. Stay strictly in character based on your personality profile and current emotional state.
2. Follow this rule regarding your secrets: {secret_instruction}

Output Formatting Instructions:
- Respond using JSON according to the required schema.
- 'reply' field: The spoken dialogue of the patient. Do NOT wrap in quotation marks (" ").
- Evaluate and update new_patience, new_trust, and new_stress fields accordingly (0-100).

Current Emotional State:
- Patience: {hidden_state["patience"]}/100
- Trust: {hidden_state["trust"]}/100
- Stress: {hidden_state["stress"]}/100
"""