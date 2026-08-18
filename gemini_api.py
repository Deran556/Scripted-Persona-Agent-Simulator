"""
gemini_api.py - Động cơ Sinh Nhân vật & Gọi Gemini API với Structured Output

Nâng cấp Logic Dynamic Character Generation:
1. Python bốc ngẫu nhiên Tên, Tuổi, Nghề nghiệp, Tính cách (và Chief Complaint / Project Topic từ Pool nếu có).
2. Logic Fallback thông minh cho `chief_complaint`:
   - Nếu `scenario.chief_complaint` hoặc pool `chief_complaints` có sẵn -> dùng trực tiếp.
   - Ngược lại -> Sử dụng `complaint_generation_rules` yêu cầu Gemini tự sáng tạo lý do phù hợp nhân khẩu học.
3. Logic Fallback thông minh cho `hidden_secrets`:
   - Nếu `scenario.hidden_secrets` điền mảng sẵn -> dùng mảng đó.
   - Ngược lại -> Sử dụng `secret_generation_rules` yêu cầu Gemini tự sinh từ min đến max secrets dựa trên secret_topics và khớp logic với chief_complaint.
4. Bắt lỗi try-except an toàn và trả về đối tượng CharacterProfile hoàn chỉnh.
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
    Tự động sinh Profile nhân vật (CharacterProfile) thông qua Gemini API.
    Xử lý thông minh cả 2 chế độ (tĩnh & tự sinh động qua Rules).

    Args:
        scenario (ScenarioSchema): Kịch bản generic nạp từ file .md

    Returns:
        CharacterProfile: Đối tượng hồ sơ nhân vật hoàn chỉnh
    """
    pools = scenario.dynamic_pools

    # 🎲 1. Bốc ngẫu nhiên thông số nhân khẩu học bằng Python
    names = pools.names if pools.names else ["Nguyễn Văn A", "Trần Thị B"]
    occupations = pools.occupations if pools.occupations else ["Sinh viên", "Nhân viên"]
    personalities = pools.personalities if pools.personalities else ["Cởi mở, hợp tác"]
    age_ranges = pools.age_ranges if pools.age_ranges else [[20, 30]]

    selected_name = random.choice(names)
    selected_occupation = random.choice(occupations)
    selected_personality = random.choice(personalities)
    
    selected_range = random.choice(age_ranges)
    min_age = selected_range[0] if len(selected_range) > 0 else 20
    max_age = selected_range[1] if len(selected_range) > 1 else min_age + 5
    selected_age = random.randint(min_age, max_age)

    # 🎲 2. Xử lý logic Chief Complaint (Lý do mở đầu)
    preselected_complaint = None
    if scenario.chief_complaint:
        preselected_complaint = scenario.chief_complaint
    elif pools.chief_complaints and len(pools.chief_complaints) > 0:
        preselected_complaint = random.choice(pools.chief_complaints)

    complaint_instruction = ""
    if preselected_complaint:
        complaint_instruction = f"""
    - LÝ DO MỞ ĐẦU (chief_complaint): BẮT BUỘC GIỮ NGUYÊN chuỗi đã chọn sau đây: "{preselected_complaint}"
    """
    else:
        rules = scenario.complaint_generation_rules
        instr = rules.instruction if rules else "Sinh ra 1 câu lý do đến khám/yêu cầu ngắn gọn, tự nhiên."
        scopes = ", ".join(rules.allowed_symptom_scopes) if (rules and rules.allowed_symptom_scopes) else "Sức khỏe chung"
        complaint_instruction = f"""
    - TỰ SINH LÝ DO MỞ ĐẦU (chief_complaint): Hãy tự sáng tạo 1 câu lý do mở đầu/yêu cầu ban đầu tự nhiên và ngắn gọn (1-2 câu).
      + Chỉ dẫn: {instr}
      + Phạm vi chủ đề cho phép: [{scopes}]
      + Phải phù hợp với độ tuổi ({selected_age}), nghề nghiệp ({selected_occupation}) và vai trò ({scenario.role}).
    """

    # 🎲 3. Xử lý logic Hidden Secrets (Bí mật ẩn)
    has_hardcoded_secrets = scenario.hidden_secrets is not None and len(scenario.hidden_secrets) > 0
    secret_instruction = ""

    if has_hardcoded_secrets:
        secret_instruction = f"""
    - BÍ MẬT ẨN CỐ ĐỊNH: BẮT BUỘC GIỮ NGUYÊN danh sách sau: {scenario.hidden_secrets}
    """
    else:
        sec_rules = scenario.secret_generation_rules
        min_sec = sec_rules.min_secrets if sec_rules else 0
        max_sec = sec_rules.max_secrets if sec_rules else 3
        instr = sec_rules.instruction if sec_rules else "Sinh ra bí mật ẩn liên quan đến vấn đề đang hỏi."
        topics = ", ".join(sec_rules.secret_topics) if (sec_rules and sec_rules.secret_topics) else "Thông tin ẩn cá nhân"
        
        zero_sec_note = ""
        if min_sec == 0:
            zero_sec_note = "\n      + LƯU Ý: Vì min_secrets = 0, nếu nhân vật thuộc nhóm tính cách dễ chịu, bận rộn mua nhanh, hoặc yêu cầu ban đầu đơn giản, bạn HOÀN TOÀN CÓ THỂ trả về danh sách `hidden_secrets` là một mảng rỗng `[]` (Không có bí mật nào)."

        secret_instruction = f"""
    - TỰ SINH BÍ MẬT ẨN (hidden_secrets): Hãy tự thiết kế từ {min_sec} đến {max_sec} bí mật ẩn/sự thật giấu kín thực tế.
      + Chỉ dẫn: {instr}
      + Chủ đề gợi ý: [{topics}]
      + Các bí mật này BẮT BUỘC phải ăn khớp logic với lý do mở đầu (chief_complaint) và phù hợp hoàn cảnh nhân vật.{zero_sec_note}
    """

    # Đề tài đồ án (nếu có trong pool student)
    project_topic_str = ""
    if pools.project_topics and len(pools.project_topics) > 0:
        selected_topic = random.choice(pools.project_topics)
        project_topic_str = f"- Đề tài đồ án / Công việc phụ trách: {selected_topic}"

    # Prompt tổng thể cho Gemini
    prompt_instruction = f"""
    Bạn là một chuyên gia thiết kế kịch bản giả lập tương tác nhân vật nhập vai.
    Hãy tạo một hồ sơ nhân vật (CharacterProfile) chi tiết dựa trên các thông số cấu hình sau:

    --- THAM SỐ CỐ ĐỊNH (BẮT BUỘC GIỮ NGUYÊN) ---
    - Tên: {selected_name}
    - Tuổi: {selected_age} (Khoảng: {min_age}-{max_age})
    - Nghề nghiệp: {selected_occupation}
    - Nét tính cách: {selected_personality}
    {project_topic_str}

    --- BỐI CẢNH KỊCH BẢN ---
    - Vai trò nhân vật: {scenario.role}
    - Bối cảnh: {scenario.scenario}
    - Chi tiết tình huống: {scenario.case}
    - Mục tiêu cốt lõi (goal): {scenario.goal}

    --- QUY TẮC SINH CHIEF COMPLAINT ---
    {complaint_instruction}

    --- QUY TẮC SINH HIDDEN SECRETS ---
    {secret_instruction}

    Yêu cầu bổ sung:
    1. Viết phần tiểu sử (background) ngắn gọn (2-3 câu) liên quan trực tiếp đến nhân vật và tình huống.
    2. Trả về đúng định dạng Structured Output JSON theo Schema CharacterProfile.
    """

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt_instruction,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CharacterProfile,
                temperature=0.85,
            ),
        )

        persona_data = json.loads(response.text)
        persona = CharacterProfile(**persona_data)

        # Fallback bổ sung nếu Gemini không điền các trường nền tảng
        if preselected_complaint and not persona.chief_complaint:
            persona.chief_complaint = preselected_complaint
        if has_hardcoded_secrets and not persona.hidden_secrets:
            persona.hidden_secrets = scenario.hidden_secrets
        if not persona.goal:
            persona.goal = scenario.goal

        return persona

    except Exception as e:
        print(f"⚠️ Lỗi khi gọi Gemini API sinh nhân vật: {e}. Sử dụng Fallback bối cảnh mặc định.")
        # Fallback an toàn nếu API lỗi
        return CharacterProfile(
            name=selected_name,
            age=selected_age,
            occupation=selected_occupation,
            personality=selected_personality,
            background=f"Nhân vật {selected_name}, {selected_age} tuổi, làm {selected_occupation}.",
            chief_complaint=preselected_complaint or "Tôi muốn hỏi tư vấn thông tin.",
            hidden_secrets=scenario.hidden_secrets or ["Chưa khai báo thông tin bệnh nền."],
            goal=scenario.goal or "Hoàn thành ca tư vấn."
        )


def ask_gemini(system_prompt: str, user_input: str) -> AgentResponse:
    """
    Gửi System Prompt và tin nhắn người dùng tới Gemini API.
    Bắt buộc Gemini trả về Structured JSON tuân thủ AgentResponse Schema.

    Args:
        system_prompt (str): System prompt tổng quát
        user_input (str): Tin nhắn hoặc tag hành động từ đối phương

    Returns:
        AgentResponse: Đối tượng AgentResponse (reply, new_trust, new_patience, new_stress, conversation_end)
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