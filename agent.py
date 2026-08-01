"""
agent.py - Patient Agent Orchestrator

Changes from previous version:
- hidden_state is no longer a module-level global.
- ask_agent() and reset_agent() now accept a `state` dict parameter (passed from st.session_state in app.py).
- dialogue_history is now passed into build_prompt() for conversation memory.
- State updates use the new LLM-driven update_state() from state_machine.py.
- current_patient removed from global scope; managed via st.session_state in app.py.
"""

import json
from prompt_builder import build_prompt
from gemini_api import ask_gemini, generate_dynamic_patient
from state_machine import update_state, reset_state, make_initial_state
from models import Stage
from typing import List, Dict, Any, Optional


def create_patient(difficulty: str = None):
    """Generates a new dynamic patient via Gemini."""
    print("Đang tải kịch bản bệnh nhân mới...")
    return generate_dynamic_patient(difficulty=difficulty)


def ask_agent(
    user_input: str,
    state: Dict[str, Any],
    patient,
    dialogue_history: List[Dict[str, str]],
    turn: int = 0
) -> tuple[str, Dict[str, Any]]:
    """
    Runs one turn of the patient agent.
    
    Args:
        user_input: The pharmacist's latest message.
        state: The current hidden_state dict (from st.session_state).
        patient: The current Patient object (from st.session_state).
        dialogue_history: List of {role, content} dicts for memory injection.
        turn: Current turn index.
    
    Returns:
        (reply_text, trace_info): Patient's reply string and debug trace dict.
    """
    # Build the full system prompt with memory injected
    prompt = build_prompt(
        patient=patient,
        hidden_state=state,
        turn=turn,
        dialogue_history=dialogue_history
    )

    # Call Gemini — returns a parsed AgentResponse Pydantic object
    agent_response = ask_gemini(prompt, user_input)

    # Apply LLM-evaluated emotion scores to state (no keyword matching)
    update_state(
        state=state,
        new_trust=agent_response.new_trust,
        new_patience=agent_response.new_patience,
        new_stress=agent_response.new_stress
    )

    # Persist conversation_end flag
    state["conversation_end"] = agent_response.conversation_end

    # Build debug trace
    stage_name = Stage.GREETING.value if turn == 0 else Stage.MAIN_CHAT.value
    trace_info = {
        "turn": turn,
        "stage": stage_name,
        "prompt": prompt,
        "json_response": agent_response.model_dump()
    }

    return agent_response.reply, trace_info


def reset_agent(state: Dict[str, Any], difficulty: str = None):
    """
    Resets the agent state in-place and generates a new patient.
    
    Args:
        state: The hidden_state dict to reset (from st.session_state).
        difficulty: Optional difficulty string for patient generation.
    
    Returns:
        The newly created Patient object.
    """
    reset_state(state)
    return create_patient(difficulty=difficulty)