"""
app.py - Streamlit UI

Session State Architecture:
- st.session_state.hidden_state    → emotional state dict (trust, patience, stress, conversation_end)
- st.session_state.current_patient → active Patient object
- st.session_state.dialogue_history → list of {role, content} for LLM memory injection
- st.session_state.messages        → list of (role, display_text) tuples for chat UI
"""

import streamlit as st
from agent import ask_agent, reset_agent, create_patient
from state_machine import make_initial_state

st.title("Scripted Persona Agent Simulator")

# ---------------------------------------------------------------------------
# Session State Initialization — all state lives here, not in globals
# ---------------------------------------------------------------------------
if "hidden_state" not in st.session_state:
    st.session_state.hidden_state = make_initial_state()

if "current_patient" not in st.session_state:
    st.session_state.current_patient = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "dialogue_history" not in st.session_state:
    st.session_state.dialogue_history = []

if "trace_logs" not in st.session_state:
    st.session_state.trace_logs = []

if "selected_action" not in st.session_state:
    st.session_state.selected_action = None

# Shortcut reference for readability
hs = st.session_state.hidden_state

# ---------------------------------------------------------------------------
# Sidebar — New Patient Button
# ---------------------------------------------------------------------------
if st.sidebar.button("New Patient Scenario"):
    st.session_state.current_patient = reset_agent(state=st.session_state.hidden_state)
    st.session_state.messages = []
    st.session_state.dialogue_history = []
    st.session_state.trace_logs = []
    st.session_state.selected_action = None
    st.rerun()

# ---------------------------------------------------------------------------
# Sidebar — Generated Patient Profile
# ---------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.title("👤 Patient Profile")
if st.session_state.current_patient:
    pt = st.session_state.current_patient
    st.sidebar.write(f"**Name:** {pt.name}")
    st.sidebar.write(f"**Age:** {pt.age}")
    st.sidebar.write(f"**Occupation:** {pt.occupation}")
    st.sidebar.write(f"**Scenario:** {pt.scenario}")
    st.sidebar.write(f"**Case:** {pt.case}")
    p = pt.personality
    st.sidebar.write(f"**Personality:** Social: `{p.social}` | Honesty: `{p.honesty}` | Temper: `{p.temper}`")
else:
    st.sidebar.info("Chưa có kịch bản bệnh nhân nào.")

# ---------------------------------------------------------------------------
# Render Chat History
# ---------------------------------------------------------------------------
for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.write(content)

# ---------------------------------------------------------------------------
# Simple Action Bar
# ---------------------------------------------------------------------------
st.markdown("### ⚡ Pharmacist Actions")
col_a1, col_a2, col_a3, col_a4 = st.columns(4)

with col_a1:
    if st.button("💊 Give Medicine", use_container_width=True):
        st.session_state.selected_action = "GIVE_MEDICINE"
with col_a2:
    if st.button("📱 Check Prescription", use_container_width=True):
        st.session_state.selected_action = "CHECK_PRESCRIPTION"
with col_a3:
    if st.button("💳 Payment", use_container_width=True):
        st.session_state.selected_action = "PAYMENT"
with col_a4:
    if st.button("❌ Clear Action", use_container_width=True):
        st.session_state.selected_action = None

if st.session_state.selected_action:
    st.info(f"Selected Action: **{st.session_state.selected_action}** (will be attached to your next message)")

# ---------------------------------------------------------------------------
# Chat Input & Agent Invocation
# ---------------------------------------------------------------------------
message = st.chat_input("Nhập tin nhắn...")

if message:
    # Auto-generate patient if not yet created
    if st.session_state.current_patient is None:
        st.session_state.current_patient = create_patient()

    turn = len([m for m in st.session_state.messages if m[0] == "user"])

    # Combine action tag with message if an action was selected
    if st.session_state.selected_action:
        user_display_text = f"[{st.session_state.selected_action}] {message}"
        full_user_input = f"Action:\n{st.session_state.selected_action}\n\nMessage:\n{message}"
        st.session_state.selected_action = None
    else:
        user_display_text = message
        full_user_input = message

    with st.chat_message("user"):
        st.write(user_display_text)

    st.session_state.messages.append(("user", user_display_text))
    st.session_state.dialogue_history.append({"role": "user", "content": full_user_input})

    # Call patient agent with session state
    reply, trace_info = ask_agent(
        user_input=full_user_input,
        state=st.session_state.hidden_state,
        patient=st.session_state.current_patient,
        dialogue_history=st.session_state.dialogue_history,
        turn=turn
    )

    with st.chat_message("assistant"):
        st.write(reply)

    st.session_state.messages.append(("assistant", reply))
    st.session_state.dialogue_history.append({"role": "assistant", "content": reply})
    st.session_state.trace_logs.append(trace_info)
    st.rerun()

# ---------------------------------------------------------------------------
# Conversation Completed Card
# ---------------------------------------------------------------------------
if hs.get("conversation_end", False):
    st.markdown("---")
    st.success("✅ **Consultation Completed**\n\nThe patient has left the pharmacy.")
    btn_col1, btn_col2 = st.columns(2)

    with btn_col1:
        if st.button("🔄 Continue Chat", use_container_width=True):
            hs["conversation_end"] = False
            followup_msg = "Dược sĩ ơi, cho tôi hỏi thêm một câu nữa được không?"
            st.session_state.messages.append(("user", "(The patient turned around to ask one more question)"))
            st.session_state.dialogue_history.append({"role": "user", "content": followup_msg})
            turn = len([m for m in st.session_state.messages if m[0] == "user"])
            reply, trace_info = ask_agent(
                user_input=followup_msg,
                state=st.session_state.hidden_state,
                patient=st.session_state.current_patient,
                dialogue_history=st.session_state.dialogue_history,
                turn=turn
            )
            st.session_state.messages.append(("assistant", reply))
            st.session_state.dialogue_history.append({"role": "assistant", "content": reply})
            st.session_state.trace_logs.append(trace_info)
            st.rerun()

    with btn_col2:
        if st.button("👤 New Patient", use_container_width=True):
            st.session_state.current_patient = reset_agent(state=st.session_state.hidden_state)
            st.session_state.messages = []
            st.session_state.dialogue_history = []
            st.session_state.trace_logs = []
            st.session_state.selected_action = None
            st.rerun()

# ---------------------------------------------------------------------------
# Sidebar — Emotion State & Conversation Status
# ---------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.title("Patient Emotion State")
st.sidebar.write({
    "patience": hs["patience"],
    "trust": hs["trust"],
    "stress": hs["stress"]
})

status_str = "ENDED" if hs.get("conversation_end", False) else "ACTIVE"
st.sidebar.markdown(f"**Conversation Status:** `{status_str}`")

# Sidebar — Debriefing
with st.sidebar.expander("🕵️ Reveal Hidden Medical Facts (Debriefing)"):
    if st.session_state.current_patient:
        pt = st.session_state.current_patient
        st.write("**Chief Complaint:**", pt.chief_complaint)
        st.write("**Hidden Information:**", pt.hidden_information)
        st.write("**Goal:**", pt.goal)
    else:
        st.write("Start a conversation to generate a patient.")

# Main — Developer Logs & Prompt Trace
with st.expander("🛠️ Developer Logs & Prompt Trace"):
    if st.session_state.trace_logs:
        for log in st.session_state.trace_logs:
            st.markdown(f"### 📍 Turn {log['turn']} - Stage: `{log['stage']}`")
            st.markdown("**Prompt Sent to Model:**")
            st.code(log["prompt"], language="markdown")
            st.markdown("**JSON Returned from Model:**")
            st.json(log["json_response"])
            st.divider()
    else:
        st.info("Chưa có log dữ liệu. Hãy nhắn tin để xem trace prompt và JSON.")