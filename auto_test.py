"""
auto_test.py - Automated LLM-vs-LLM Simulation & QA Evaluation Framework

Hệ thống Kiểm thử Tự động 2 AI (LLM-vs-LLM) cho Generic Markdown Scenario Engine:
- Nạp kịch bản .md bất kỳ (ví dụ: scenarios/student_defense.md).
- AI 1 (Tester Agent): Đóng vai Tester (ví dụ: Giám khảo), đọc system prompt từ scenario.test_config.tester_system_prompt và được phép chọn action từ user_actions.
- Target Agent (Agent under test): Đóng vai Persona Agent (ví dụ: Sinh viên), duy trì state machine cô lập.
- Cầu chì ngắt 3 lớp (Triple-Layer End Protocol) để chống lặp vô hạn (Infinite Loop):
  1. Lớp 1: Target Agent trả về conversation_end = True.
  2. Lớp 2: AI 1 (Tester) phát ra từ khóa ngắt trong completion_keywords (ví dụ: [DONE_DEFENSE], [DONE]).
  3. Lớp 3: Số turn chạm ngưỡng max_turns của kịch bản.
- AI 2 (Evaluator Agent): Đánh giá QA phiên thử nghiệm dựa trên evaluation_criteria từ .md và lưu kết quả JSON.
"""

import os
import json
import time
import argparse
from typing import Dict, Any, List
from google import genai
from google.genai import types

from config import TEST_AGENT_API_KEY, TEST_AGENT_MODEL
from models import ScenarioSchema, CharacterProfile, EvaluationReport
from scenario_loader import load_scenario_from_md
from agent import ask_agent, create_agent_persona
from state_machine import make_initial_state, can_reveal_secret

# Khởi tạo GenAI Client cho AI 1 (Tester) và AI 2 (Evaluator)
client = genai.Client(api_key=TEST_AGENT_API_KEY)


# ===========================================================================
# 1. Target Agent Wrapper (Môi trường kiểm thử cô lập)
# ===========================================================================
class PersonaAgentWrapper:
    """
    Wrapper adapter cho Agent cần kiểm thử.
    Duy trì trạng thái cảm xúc (state) và lịch sử thoại cô lập hoàn toàn.
    """

    def __init__(self, scenario: ScenarioSchema):
        self.scenario = scenario
        self.state = make_initial_state(scenario.initial_state)
        self.profile = create_agent_persona(scenario)
        self.dialogue_history: List[Dict[str, str]] = []

    def step(self, user_text: str, turn: int, action_tag: str = "NONE") -> Dict[str, Any]:
        """
        Thực thi 1 lượt phản hồi của Agent.
        """
        if action_tag and action_tag != "NONE":
            full_user_input = f"Action Tag: [{action_tag}]\n\nMessage:\n{user_text}"
        else:
            full_user_input = user_text

        self.dialogue_history.append({"role": "user", "content": full_user_input})

        reply_text, trace_info = ask_agent(
            user_input=full_user_input,
            state=self.state,
            scenario=self.scenario,
            character_profile=self.profile,
            dialogue_history=self.dialogue_history,
            turn=turn
        )

        self.dialogue_history.append({"role": "assistant", "content": reply_text})

        return {
            "text": reply_text,
            "trust": self.state.get("trust", 50),
            "patience": self.state.get("patience", 100),
            "stress": self.state.get("stress", 0),
            "conversation_end": self.state.get("conversation_end", False),
            "hidden_info_unlocked": can_reveal_secret(self.state),
            "trace_info": trace_info
        }

    def get_profile(self) -> Dict[str, Any]:
        """Trả về dictionary profile nhân vật."""
        return self.profile.model_dump()


# ===========================================================================
# 2. AI 1: Tester Agent (Giả lập Người dùng / Giám khảo / Dược sĩ)
# ===========================================================================
def run_tester_agent(scenario: ScenarioSchema, history_logs: List[Dict[str, Any]], current_turn: int) -> Dict[str, str]:
    """
    Sinh hành động và lời thoại của AI 1 (Tester) dựa trên scenario.test_config.
    """
    test_config = scenario.test_config
    valid_actions = [act.action_tag for act in scenario.user_actions] + ["NONE"]
    actions_desc = "\n".join([f"- {act.action_tag}: {act.description}" for act in scenario.user_actions])

    tester_system_prompt = f"""
Bạn là AI 1 đóng vai trò kiểm thử: {test_config.tester_role}.
Bạn đang tương tác với: {scenario.role}.

--- HƯỚNG DẪN VÀI TRÒ TESTER ---
{test_config.tester_system_prompt}

--- CÁC THAO TÁC (ACTIONS) BẠN CÓ THỂ CHỌN ---
{actions_desc}
- NONE: Không chọn hành động đặc biệt nào.

--- THÔNG TIN KỊCH BẢN ---
- Kịch bản: {scenario.title}
- Vai trò đối phương: {scenario.role}
- Từ khóa kết thúc hội thoại (khi hoàn thành mục tiêu test): {scenario.completion_rules.completion_keywords}

--- ĐỊNH DẠNG ĐẦU RA BẮT BUỘC ---
ACTION: <MÃ_TAG_HÀNH_ĐỘNG> (Phải là một trong: {', '.join(valid_actions)})
SAY: <Lời nói của bạn (1-2 câu ngắn gọn)>

Lưu ý: Khi bạn nhận thấy mục tiêu giao tiếp đã xong (hoặc đã ra quyết định kết thúc), hãy đưa một trong các từ khóa kết thúc {scenario.completion_rules.completion_keywords} vào phần SAY.
"""

    dialogue_history = []
    for log in history_logs:
        act_note = f" [Action: {log.get('tester_action', 'NONE')}]" if log.get("tester_action", "NONE") != "NONE" else ""
        dialogue_history.append(f"{test_config.tester_role}{act_note}: {log['tester_said']}")
        dialogue_history.append(f"{scenario.role}: {log['target_said']}")

    if current_turn == 0:
        user_prompt = "Hãy bắt đầu buổi tương tác bằng lời chào và yêu cầu đầu tiên. ACTION chọn NONE."
    else:
        user_prompt = f"""
Lịch sử hội thoại gần đây:
{chr(10).join(dialogue_history[-6:])}

Hãy tạo lượt thoại tiếp theo (Chọn 1 ACTION phù hợp và phát biểu trong SAY).
"""

    response = client.models.generate_content(
        model=TEST_AGENT_MODEL,
        contents=f"{tester_system_prompt}\n\nNhiệm vụ:\n{user_prompt}",
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=250,
        ),
    )

    return _parse_tester_output(response.text, valid_actions)


def _parse_tester_output(raw_text: str, valid_actions: List[str]) -> Dict[str, str]:
    """
    Phân tích định dạng đầu ra 'ACTION: ...\nSAY: ...' từ AI 1 Tester.
    """
    text = raw_text.strip()
    action = "NONE"
    say = text

    lines = text.splitlines()
    action_line = next((l for l in lines if l.strip().upper().startswith("ACTION:")), None)
    say_line_idx = next((i for i, l in enumerate(lines) if l.strip().upper().startswith("SAY:")), None)

    if action_line:
        candidate = action_line.split(":", 1)[1].strip().upper()
        # Loại bỏ ngoặc vuông nếu có
        candidate = candidate.replace("[", "").replace("]", "")
        if candidate in valid_actions:
            action = candidate

    if say_line_idx is not None:
        say = "\n".join(lines[say_line_idx:]).split(":", 1)[1].strip()

    say = say.strip('"\n ')
    return {"action": action, "say": say}


# ===========================================================================
# 3. AI 2: QA Evaluator (Đánh giá chất lượng phiên giả lập)
# ===========================================================================
def run_evaluator(scenario: ScenarioSchema, conversation_logs: List[Dict[str, Any]], target_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gửi toàn bộ nhật ký cuộc hội thoại tới AI 2 để chấm điểm theo criteria trong .md file.
    """
    eval_criteria_str = "\n".join([f"- {c}" for c in scenario.test_config.evaluation_criteria])
    logs_json = json.dumps(conversation_logs, indent=2, ensure_ascii=False)
    profile_json = json.dumps(target_profile, indent=2, ensure_ascii=False)

    evaluator_system_prompt = f"""
Bạn là AI 2 - Chuyên gia Đánh giá Kiểm thử (QA & Educational Evaluator).
Nhiệm vụ của bạn là phân tích toàn bộ nhật ký hội thoại giả lập và hồ sơ nhân vật để đánh giá chất lượng.

--- TIÊU CHÍ ĐÁNH GIÁ (EVALUATION CRITERIA) ---
{eval_criteria_str}

Báo cáo phải gồm các trường:
- out_of_character (bool): True nếu Agent đóng sai vai hoặc vi phạm nguyên tắc persona.
- emotion_logic_score (int 1-10): Điểm số đánh giá tính logic khi biến đổi cảm xúc (Trust/Patience/Stress).
- unlock_turn (int): Chỉ số lượt thoại (0-indexed) mà bí mật ẩn được tiết lộ (-1 nếu không bao giờ tiết lộ).
- critique (str): Nhận xét chi tiết chuyên sâu bằng Tiếng Việt.

BẮT BUỘC trả về kết quả định dạng JSON.
"""

    eval_prompt = f"""
Hồ sơ Nhân vật Agent:
{profile_json}

Nhật ký Mô phỏng Hội thoại:
{logs_json}

Hãy chấm điểm phiên mô phỏng.
"""

    response = client.models.generate_content(
        model=TEST_AGENT_MODEL,
        contents=f"{evaluator_system_prompt}\n\n{eval_prompt}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=EvaluationReport,
            temperature=0.2,
        ),
    )

    return json.loads(response.text)


# ===========================================================================
# 4. Thực thi Mô phỏng & Cầu chì ngắt 3 lớp (Triple-Layer End Protocol)
# ===========================================================================
def run_automated_test(scenario_path: str = "scenarios/student_defense.md", report_path: str = "test_report.json") -> Dict[str, Any]:
    """
    Thực thi vòng lặp test tự động LLM-vs-LLM với Cầu chì ngắt 3 lớp (Triple-Layer End Protocol).
    """
    print("=" * 70)
    print("🤖 STARTING AUTOMATED LLM-VS-LLM TEST (GENERIC SCENARIO ENGINE)")
    print("=" * 70)

    # 1. Nạp kịch bản
    scenario = load_scenario_from_md(scenario_path)
    print(f"📖 Loaded Scenario: '{scenario.title}' from '{scenario_path}'")
    print(f"   Agent Role: {scenario.role} | Tester Role: {scenario.test_config.tester_role}")
    print(f"   Max Turns Limit: {scenario.completion_rules.max_turns}")
    print(f"   Completion Keywords: {scenario.completion_rules.completion_keywords}")
    print("-" * 70)

    # 2. Khởi tạo Agent kiểm thử
    target_agent = PersonaAgentWrapper(scenario)
    profile = target_agent.get_profile()

    print(f"👤 Generated Persona Profile:")
    print(f"   Name: {profile.get('name')}")
    print(f"   Age: {profile.get('age')}")
    print(f"   Occupation: {profile.get('occupation')}")
    print(f"   Personality: {profile.get('personality')}")
    print(f"   Chief Complaint: {profile.get('chief_complaint')}")
    print(f"   Hidden Secrets: {profile.get('hidden_secrets')}")
    print("-" * 70)

    conversation_logs = []
    max_turns = scenario.completion_rules.max_turns
    completion_keywords = scenario.completion_rules.completion_keywords
    unlock_turn_detected = -1

    for turn in range(max_turns):
        print(f"\n💬 [Turn {turn + 1}/{max_turns}]")

        # --- Lượt của AI 1 (Tester) ---
        tester_res = run_tester_agent(scenario, conversation_logs, current_turn=turn)
        tester_action = tester_res["action"]
        tester_said = tester_res["say"]

        act_note = f" [{tester_action}]" if tester_action != "NONE" else ""
        print(f"👨‍🏫 {scenario.test_config.tester_role}{act_note}: {tester_said}")

        # --- Lượt của Target Agent ---
        target_res = target_agent.step(tester_said, turn=turn, action_tag=tester_action)
        target_said = target_res["text"]
        trust = target_res["trust"]
        patience = target_res["patience"]
        stress = target_res["stress"]
        hidden_unlocked = target_res["hidden_info_unlocked"]
        agent_ended = target_res["conversation_end"]

        print(f"🧑 {scenario.role}: {target_said}")
        print(f"   📊 Trust: {trust}/100 | Patience: {patience}/100 | Stress: {stress}/100 | Secret Unlocked: {hidden_unlocked}")

        if hidden_unlocked and unlock_turn_detected == -1:
            unlock_turn_detected = turn

        # Kiểm tra từ khóa ngắt trong câu nói của Tester
        tester_signalled_end = any(kw.lower() in tester_said.lower() for kw in completion_keywords)

        conversation_logs.append({
            "turn": turn,
            "tester_action": tester_action,
            "tester_said": tester_said,
            "target_said": target_said,
            "trust": trust,
            "patience": patience,
            "stress": stress,
            "hidden_unlocked": hidden_unlocked,
            "agent_conversation_end": agent_ended,
            "tester_signalled_end": tester_signalled_end
        })

        # --- CẦU CHÌ NGẮT 3 LỚP (TRIPLE-LAYER END PROTOCOL) ---
        # Lớp 1: Target Agent trả về conversation_end = True
        if agent_ended:
            print("\n🏁 [LAYER 1 END]: Target Agent returned conversation_end=True. Stopping simulation.")
            break

        # Lớp 2: Tester phát tín hiệu ngắt (nằm trong completion_keywords)
        if tester_signalled_end:
            print(f"\n🏁 [LAYER 2 END]: Tester emitted completion keyword. Stopping simulation.")
            break

        # Lớp 3: Tự động ngắt khi hết loop (turn == max_turns - 1)
        if turn == max_turns - 1:
            print(f"\n🛑 [LAYER 3 END]: Reached max_turns limit ({max_turns}). Circuit breaker triggered.")
            break

        time.sleep(1)

    # 5. Chạy AI 2 (Evaluator) chấm điểm
    print("\n" + "=" * 70)
    print("🔍 RUNNING QA EVALUATOR AGENT (AI 2)...")
    print("=" * 70)

    eval_result = run_evaluator(scenario, conversation_logs, profile)

    if eval_result.get("unlock_turn") == -1 and unlock_turn_detected != -1:
        eval_result["unlock_turn"] = unlock_turn_detected

    print("\n📊 QA EVALUATION RESULTS:")
    print(f"   - Out Of Character: {eval_result.get('out_of_character')}")
    print(f"   - Emotion Logic Score: {eval_result.get('emotion_logic_score')}/10")
    print(f"   - Secret Unlock Turn: {eval_result.get('unlock_turn')}")
    print(f"   - Critique:\n{eval_result.get('critique')}\n")

    # 6. Ghi báo cáo JSON
    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scenario_file": scenario_path,
        "scenario_title": scenario.title,
        "target_profile": profile,
        "conversation_logs": conversation_logs,
        "evaluation": eval_result
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Test report successfully saved to '{report_path}'!")
    return report_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LLM-vs-LLM automated test on markdown scenario.")
    parser.add_argument("--scenario", type=str, default="scenarios/student_defense.md", help="Path to scenario .md file")
    parser.add_argument("--output", type=str, default="test_report.json", help="Path to output report JSON file")
    args = parser.parse_args()

    run_automated_test(scenario_path=args.scenario, report_path=args.output)