"""
agent.py - Điều phối Nhân vật Agent (Persona Agent Orchestrator)

Quản lý vòng đời hoạt động của Agent:
- Khởi tạo hồ sơ nhân vật động từ ScenarioSchema.
- Thực thi từng lượt giao tiếp (ask_agent) thông qua State Machine và Gemini API.
- Cập nhật điểm cảm xúc đảm bảo không vượt quá phạm vi [0, 100].
"""

import json
from typing import List, Dict, Any, Tuple
from models import ScenarioSchema, CharacterProfile, AgentResponse, Stage
from scenario_loader import load_scenario_from_md
from gemini_api import ask_gemini, generate_dynamic_persona
from state_machine import update_state, reset_state, make_initial_state
from prompt_builder import build_generic_prompt


def create_agent_persona(scenario: ScenarioSchema) -> CharacterProfile:
    """
    Tạo hồ sơ nhân vật động dựa trên kịch bản nạp vào.

    Args:
        scenario (ScenarioSchema): Kịch bản generic

    Returns:
        CharacterProfile: Hồ sơ nhân vật hoàn chỉnh
    """
    print(f"🎲 Đang khởi tạo nhân vật động cho kịch bản: '{scenario.title}'...")
    return generate_dynamic_persona(scenario)


def ask_agent(
    user_input: str,
    state: Dict[str, Any],
    scenario: ScenarioSchema,
    character_profile: CharacterProfile,
    dialogue_history: List[Dict[str, str]],
    turn: int = 0
) -> Tuple[str, Dict[str, Any]]:
    """
    Thực thi 1 lượt tương tác của Agent.

    Args:
        user_input (str): Tin nhắn hoặc tag hành động từ phía User/Tester
        state (Dict[str, Any]): Trạng thái cảm xúc hiện tại (trust, patience, stress, conversation_end)
        scenario (ScenarioSchema): Đối tượng kịch bản hiện tại
        character_profile (CharacterProfile): Hồ sơ nhân vật đang đóng vai
        dialogue_history (List[Dict[str, str]]): Lịch sử hội thoại
        turn (int): Lượt thoại hiện tại (0-indexed)

    Returns:
        Tuple[str, Dict[str, Any]]: (Lời thoại của Agent, Thông tin debug trace)
    """
    # 1. Dựng System Prompt tổng quát cho turn hiện tại
    prompt = build_generic_prompt(
        scenario=scenario,
        character_profile=character_profile,
        state=state,
        turn=turn,
        history=dialogue_history
    )

    # 2. Gọi Gemini API nhận phản hồi cấu trúc AgentResponse
    agent_response: AgentResponse = ask_gemini(system_prompt=prompt, user_input=user_input)

    # 3. Cập nhật State Machine (Cắt ngắt khoảng 0-100)
    update_state(
        state=state,
        new_trust=agent_response.new_trust,
        new_patience=agent_response.new_patience,
        new_stress=agent_response.new_stress
    )

    # 4. Cập nhật cờ kết thúc hội thoại từ LLM
    state["conversation_end"] = agent_response.conversation_end

    # 5. Dựng nhật ký debug trace
    stage_name = Stage.GREETING.value if turn == 0 else Stage.MAIN_CHAT.value
    trace_info = {
        "turn": turn,
        "stage": stage_name,
        "prompt": prompt,
        "json_response": agent_response.model_dump()
    }

    return agent_response.reply, trace_info


def reset_agent(state: Dict[str, Any], scenario: ScenarioSchema) -> CharacterProfile:
    """
    Đặt lại trạng thái cảm xúc và sinh ra một nhân vật hoàn toàn mới cho kịch bản.

    Args:
        state (Dict[str, Any]): Trạng thái cảm xúc cần reset
        scenario (ScenarioSchema): Kịch bản hiện tại

    Returns:
        CharacterProfile: Nhân vật mới sinh
    """
    reset_state(state, scenario.initial_state)
    return create_agent_persona(scenario)