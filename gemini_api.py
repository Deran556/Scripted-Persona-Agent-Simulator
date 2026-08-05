"""
gemini_api.py - Động cơ sinh nhân vật & Gọi Gemini API với Structured Output

Chức năng:
- generate_dynamic_persona(scenario: ScenarioSchema): Bốc ngẫu nhiên thông số từ scenario.dynamic_pools 
  (Tên, Tuổi, Nghề nghiệp, Tính cách) và dùng Gemini API để tạo CharacterProfile chi tiết.
- ask_gemini(system_prompt, user_input): Gửi prompt tới Gemini API và nhận phản hồi cấu trúc 
  chuẩn Pydantic AgentResponse (reply, new_trust, new_patience, new_stress, conversation_end).
"""

import json
import random
from google import genai
from google.genai import types
from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    TEMPERATURE,
    MAX_OUTPUT_TOKENS,
    TOP_P,
)
from models import ScenarioSchema, CharacterProfile, AgentResponse

# Khởi tạo Google GenAI Client
client = genai.Client(api_key=GEMINI_API_KEY)


def generate_dynamic_persona(scenario: ScenarioSchema) -> CharacterProfile:
    """
    Bốc ngẫu nhiên các yếu tố từ scenario.dynamic_pools và yêu cầu Gemini API 
    sinh ra một Profile nhân vật hoàn chỉnh (CharacterProfile).

    Args:
        scenario (ScenarioSchema): Kịch bản generic đã nạp

    Returns:
        CharacterProfile: Hồ sơ nhân vật chi tiết được tạo tự động
    """
    pools = scenario.dynamic_pools

    # 🎲 Bốc ngẫu nhiên các tham số từ dynamic_pools của kịch bản
    names = pools.names if pools.names else ["Nguyễn Văn A", "Trần Thị B"]
    occupations = pools.occupations if pools.occupations else ["Sinh viên", "Kỹ sư"]
    personalities = pools.personalities if pools.personalities else ["Bình tĩnh, tự tin"]
    age_ranges = pools.age_ranges if pools.age_ranges else [[18, 25]]

    selected_name = random.choice(names)
    selected_occupation = random.choice(occupations)
    selected_personality = random.choice(personalities)
    
    selected_range = random.choice(age_ranges)
    min_age = selected_range[0] if len(selected_range) > 0 else 18
    max_age = selected_range[1] if len(selected_range) > 1 else min_age + 5
    selected_age = random.randint(min_age, max_age)

    # Prompt yêu cầu Gemini đóng vai chuyên gia tạo nhân vật
    prompt_instruction = f"""
    Bạn là một chuyên gia thiết kế kịch bản mô phỏng tương tác nhân vật.
    Hãy tạo một hồ sơ nhân vật (CharacterProfile) chi tiết dựa trên các tham số đã bốc ngẫu nhiên sau:

    --- THAM SỐ CỐ ĐỊNH (BẮT BUỘC GIỮ NGUYÊN) ---
    - Tên: {selected_name}
    - Tuổi: {selected_age} (Khoảng: {min_age}-{max_age})
    - Nghề nghiệp: {selected_occupation}
    - Nét tính cách chủ đạo: {selected_personality}

    --- THÔNG TIN KỊCH BẢN VÀ VAI TRÒ ---
    - Vai trò nhân vật: {scenario.role}
    - Bối cảnh chung: {scenario.scenario}
    - Chi tiết ca: {scenario.case}
    - Lý do công khai ban đầu (chief_complaint): {scenario.chief_complaint}
    - Danh sách bí mật ẩn (hidden_secrets): {scenario.hidden_secrets}
    - Mục tiêu cốt lõi (goal): {scenario.goal}

    Yêu cầu:
    1. Giữ nguyên Tên, Tuổi, Nghề nghiệp và Tính cách cố định ở trên.
    2. Viết tiểu sử (background) ngắn gọn (2-3 câu) phù hợp với bối cảnh kịch bản.
    3. Trả về đúng định dạng JSON theo Schema CharacterProfile.
    """

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt_instruction,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CharacterProfile,
            temperature=0.85,
        ),
    )

    # Validate và khởi tạo mô hình Pydantic từ kết quả JSON
    persona_data = json.loads(response.text)
    persona = CharacterProfile(**persona_data)
    
    # Đảm bảo các thuộc tính gốc từ Scenario được lưu giữ đầy đủ
    if not persona.chief_complaint:
        persona.chief_complaint = scenario.chief_complaint
    if not persona.hidden_secrets:
        persona.hidden_secrets = scenario.hidden_secrets
    if not persona.goal:
        persona.goal = scenario.goal

    return persona


def ask_gemini(system_prompt: str, user_input: str) -> AgentResponse:
    """
    Gửi System Prompt và tin nhắn người dùng tới Gemini API.
    Bắt buộc Gemini trả về Structured JSON tuân thủ AgentResponse Schema.

    Args:
        system_prompt (str): Prompt hệ thống đã dựng (chứa bối cảnh, luật lệ)
        user_input (str): Tin nhắn hoặc hành động mới nhất của User/Tester

    Returns:
        AgentResponse: Đối tượng AgentResponse chứa reply, new_trust, new_patience, new_stress, conversation_end
    """
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"""
{system_prompt}

Tin nhắn/Hành động mới nhất từ đối phương:
{user_input}
""",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AgentResponse,
            temperature=TEMPERATURE,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            top_p=TOP_P,
        ),
    )

    return AgentResponse.model_validate_json(response.text)