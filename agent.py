import json
from state_machine import update_state, hidden_state, reset_state
from prompt_builder import build_prompt
from gemini_api import ask_gemini, generate_dynamic_patient
from models import Stage

current_patient = None

def create_patient(difficulty=None):
    # Khởi tạo bệnh nhân bằng AI với các tiêu chí ngẫu nhiên
    print("Đang tải kịch bản bệnh nhân mới...")
    return generate_dynamic_patient(difficulty=difficulty)

def ask_agent(user_input, turn=0):
    global current_patient

    if current_patient is None:
        current_patient = create_patient()

    update_state(user_input)

    prompt = build_prompt(
        current_patient,
        hidden_state,
        turn=turn
    )

    raw_response = ask_gemini(
        prompt,
        user_input
    )

    try:
        json_data = json.loads(raw_response)
        reply = json_data.get("reply", raw_response)
        if "new_patience" in json_data and isinstance(json_data["new_patience"], int):
            hidden_state["patience"] = json_data["new_patience"]
        if "new_trust" in json_data and isinstance(json_data["new_trust"], int):
            hidden_state["trust"] = json_data["new_trust"]
        if "new_stress" in json_data and isinstance(json_data["new_stress"], int):
            hidden_state["stress"] = json_data["new_stress"]
        if "conversation_end" in json_data and isinstance(json_data["conversation_end"], bool):
            hidden_state["conversation_end"] = json_data["conversation_end"]
    except Exception:
        json_data = {"reply": raw_response}
        reply = raw_response

    stage_name = Stage.GREETING.value if turn == 0 else Stage.MAIN_CHAT.value

    trace_info = {
        "turn": turn,
        "stage": stage_name,
        "prompt": prompt,
        "json_response": json_data
    }

    return reply, trace_info

def reset_agent(difficulty=None):
    global current_patient
    reset_state()
    current_patient = create_patient(difficulty=difficulty)
    return current_patient