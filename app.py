import streamlit as st
import agent
from agent import ask_agent, reset_agent
from state_machine import hidden_state

st.title("Scripted Persona Agent Simulator")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "trace_logs" not in st.session_state:
    st.session_state.trace_logs = []

# new patient button
if st.sidebar.button("New Patient Scenario"):
    reset_agent()
    st.session_state.messages = []
    st.session_state.trace_logs = []
    st.rerun()

for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.write(content)

message = st.chat_input("Nhập tin nhắn...")

if message:
    turn = len([m for m in st.session_state.messages if m[0] == "user"])

    with st.chat_message("user"):
        st.write(message)

    st.session_state.messages.append(("user", message))

    reply, trace_info = ask_agent(message, turn=turn)

    with st.chat_message("assistant"):
        st.write(reply)

    st.session_state.messages.append(("assistant", reply))
    st.session_state.trace_logs.append(trace_info)

st.sidebar.title("Patient Emotion State")
st.sidebar.write(hidden_state)

# 🔍 DEBRIEF / REVEAL SECTION (Collapsed by default so you don't see it while chatting)
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