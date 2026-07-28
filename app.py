import streamlit as st
from agent import ask_agent, reset_agent
from state_machine import hidden_state

st.title("Scripted Persona Agent Simulator")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Nút tạo ca bệnh mới
if st.sidebar.button("New Patient Scenario"):
    reset_agent()
    st.session_state.messages = []
    st.rerun()

for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.write(content)

message = st.chat_input("Nhập tin nhắn...")

if message:
    with st.chat_message("user"):
        st.write(message)

    st.session_state.messages.append(
        ("user", message)
    )

    response = ask_agent(message)

    with st.chat_message("assistant"):
        st.write(response)

    st.session_state.messages.append(
        ("assistant", response)
    )

st.sidebar.title("Patient Emotion State")
st.sidebar.write(hidden_state)