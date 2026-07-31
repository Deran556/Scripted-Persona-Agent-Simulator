import streamlit as st
import agent
from agent import ask_agent, reset_agent
from state_machine import hidden_state

st.title("Scripted Persona Agent Simulator")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "trace_logs" not in st.session_state:
    st.session_state.trace_logs = []

if "selected_action" not in st.session_state:
    st.session_state.selected_action = None

# New patient button in sidebar
if st.sidebar.button("New Patient Scenario"):
    reset_agent()
    st.session_state.messages = []
    st.session_state.trace_logs = []
    st.session_state.selected_action = None
    st.rerun()

# ---------------------------------------------------------------------------
# 👤 GENERATED PATIENT PROFILE IN SIDEBAR
# ---------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.title("👤 Patient Profile")
if agent.current_patient:
    st.sidebar.write(f"**Name:** {agent.current_patient.name}")
    st.sidebar.write(f"**Age:** {agent.current_patient.age}")
    st.sidebar.write(f"**Occupation:** {agent.current_patient.occupation}")
    st.sidebar.write(f"**Scenario:** {agent.current_patient.scenario}")
    st.sidebar.write(f"**Case:** {agent.current_patient.case}")
    p = agent.current_patient.personality
    st.sidebar.write(f"**Personality:** Social: `{p.social}` | Honesty: `{p.honesty}` | Temper: `{p.temper}`")
else:
    st.sidebar.info("Chưa có kịch bản bệnh nhân nào.")

# Render Chat History
for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.write(content)

# ---------------------------------------------------------------------------
# 🛠️ Simple Action Bar (Req 3)
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

# Chat Input
message = st.chat_input("Nhập tin nhắn...")

if message:
    turn = len([m for m in st.session_state.messages if m[0] == "user"])

    # Combine action and message if an action was selected
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

    reply, trace_info = ask_agent(full_user_input, turn=turn)

    with st.chat_message("assistant"):
        st.write(reply)

    st.session_state.messages.append(("assistant", reply))
    st.session_state.trace_logs.append(trace_info)
    st.rerun()

# ---------------------------------------------------------------------------
# 🏁 Conversation Completed Card (Req 2)
# ---------------------------------------------------------------------------
if hidden_state.get("conversation_end", False):
    st.markdown("---")
    st.success("✅ **Consultation Completed**\n\nThe patient has left the pharmacy.")
    btn_col1, btn_col2 = st.columns(2)

    with btn_col1:
        if st.button("🔄 Continue Chat", use_container_width=True):
            hidden_state["conversation_end"] = False
            # Simulate that the patient came back to ask one more question
            st.session_state.messages.append(("user", "(The patient turned around to ask one more question)"))
            turn = len([m for m in st.session_state.messages if m[0] == "user"])
            reply, trace_info = ask_agent("Dược sĩ ơi, cho tôi hỏi thêm một câu nữa...", turn=turn)
            st.session_state.messages.append(("assistant", reply))
            st.session_state.trace_logs.append(trace_info)
            st.rerun()

    with btn_col2:
        if st.button("👤 New Patient", use_container_width=True):
            reset_agent()
            st.session_state.messages = []
            st.session_state.trace_logs = []
            st.session_state.selected_action = None
            st.rerun()

# ---------------------------------------------------------------------------
# 📊 Sidebar Improvements (Req 7)
# ---------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.title("Patient Emotion State")
st.sidebar.write({
    "patience": hidden_state["patience"],
    "trust": hidden_state["trust"],
    "stress": hidden_state["stress"]
})

status_str = "ENDED" if hidden_state.get("conversation_end", False) else "ACTIVE"
st.sidebar.markdown(f"**Conversation Status:** `{status_str}`")

# 🔍 DEBRIEF / REVEAL SECTION
with st.sidebar.expander("🕵️ Reveal Hidden Medical Facts (Debriefing)"):
    if agent.current_patient:
        st.write("**Chief Complaint:**", agent.current_patient.chief_complaint)
        st.write("**Hidden Information:**", agent.current_patient.hidden_information)
        st.write("**Goal:**", agent.current_patient.goal)
    else:
        st.write("Start a conversation to generate a patient.")

# 🛠️ DEVELOPER LOGS & PROMPT TRACE EXTRACTOR
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