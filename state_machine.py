hidden_state = {
    "patience": 100,
    "trust": 50,
    "stress": 0,
    "conversation_end": False
}

def clamp():
    for key in ["patience", "trust", "stress"]:
        hidden_state[key] = max(
            0,
            min(100, hidden_state[key])
        )

def update_state(user_input):
    text = user_input.lower()

    if "thank" in text or "good" in text or "cảm ơn" in text:
        hidden_state["trust"] += 10

    if "stupid" in text or "dumb" in text:
        hidden_state["patience"] -= 20
        hidden_state["stress"] += 20

    clamp()

def reset_state():
    hidden_state["patience"] = 100
    hidden_state["trust"] = 50
    hidden_state["stress"] = 0
    hidden_state["conversation_end"] = False

def can_reveal_secret(hidden_state):
    return hidden_state["trust"] >= 70