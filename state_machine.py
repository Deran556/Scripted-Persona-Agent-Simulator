"""
state_machine.py - LLM-Driven State Machine

Changes from previous version:
- Removed ALL hardcoded keyword matching (e.g., "if thank in text").
- update_state() now accepts LLM-evaluated scores directly from parsed JSON.
- The LLM is responsible for evaluating the pharmacist's empathy and tone.
- hidden_state is a plain dict. Per-user state is managed via st.session_state in app.py.
"""

def make_initial_state() -> dict:
    """Returns a fresh hidden state dict. Used to initialize or reset a session."""
    return {
        "patience": 100,
        "trust": 50,
        "stress": 0,
        "conversation_end": False
    }

def clamp_state(state: dict) -> None:
    """Clamps numeric emotion scores to the valid 0-100 range."""
    for key in ["patience", "trust", "stress"]:
        if key in state:
            state[key] = max(0, min(100, state[key]))

def update_state(state: dict, new_trust: int, new_patience: int, new_stress: int) -> None:
    """
    Applies LLM-evaluated emotion scores directly to the state dict.
    No keyword matching. The LLM is the sole evaluator of the pharmacist's tone.
    
    Args:
        state: The hidden_state dict to update (from st.session_state or global fallback).
        new_trust: Trust score returned by the LLM (0-100).
        new_patience: Patience score returned by the LLM (0-100).
        new_stress: Stress score returned by the LLM (0-100).
    """
    state["trust"] = new_trust
    state["patience"] = new_patience
    state["stress"] = new_stress
    clamp_state(state)

def reset_state(state: dict) -> None:
    """Resets a state dict to initial values in-place."""
    state["patience"] = 100
    state["trust"] = 50
    state["stress"] = 0
    state["conversation_end"] = False

def can_reveal_secret(state: dict) -> bool:
    """Returns True when trust is high enough for secret disclosure (for auto_test compatibility)."""
    return state["trust"] >= 60