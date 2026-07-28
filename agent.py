from state_machine import update_state, hidden_state, reset_state
from prompt_builder import build_prompt
from gemini_api import ask_gemini, generate_dynamic_patient

current_patient = None

def create_patient():
    print("Loading dynamic patient scenario...")
    return generate_dynamic_patient(difficulty="stubborn, irritable, hiding medical history")

def ask_agent(user_input):
    global current_patient

    if current_patient is None:
        current_patient = create_patient()

    update_state(user_input)

    prompt = build_prompt(
        current_patient,
        hidden_state
    )

    response = ask_gemini(
        prompt,
        user_input
    )

    return response

def reset_agent():
    global current_patient
    current_patient = create_patient()
    reset_state()