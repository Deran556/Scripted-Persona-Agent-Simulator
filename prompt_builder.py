"""
prompt_builder.py - Dựng System Prompt Tổng quát (Generic Prompt Builder)

Chức năng:
- build_generic_prompt(): Ghép nối thông tin kịch bản (ScenarioSchema), hồ sơ nhân vật (CharacterProfile),
  nội dung Markdown Body (instructions), trạng thái cảm xúc (state), quy tắc giai đoạn (Stage), 
  chống lặp (Anti-looping) và tiết lộ bí mật ẩn (Hidden Secrets Gate khi Trust > 60).
"""

from typing import List, Dict, Any
from models import ScenarioSchema, CharacterProfile, Stage


def build_generic_prompt(
    scenario: ScenarioSchema,
    character_profile: CharacterProfile,
    state: Dict[str, Any],
    turn: int = 0,
    history: List[Dict[str, str]] = None
) -> str:
    """
    Dựng System Prompt tổng quát cho Gemini LLM.

    Args:
        scenario (ScenarioSchema): Đối tượng kịch bản .md đã nạp
        character_profile (CharacterProfile): Hồ sơ nhân vật cụ thể
        state (Dict[str, Any]): Trạng thái cảm xúc (trust, patience, stress)
        turn (int): Lượt thoại hiện tại (0-indexed)
        history (List[Dict[str, str]]): Lịch sử hội thoại

    Returns:
        str: Chuỗi System Prompt hoàn chỉnh
    """
    trust = state.get("trust", 50)
    patience = state.get("patience", 100)
    stress = state.get("stress", 10)

    # --- 1. Quy tắc Giai đoạn (Stage Instruction) ---
    if turn == 0:
        stage_instruction = f"""
Current Stage: GREETING (Turn 0)
- Bạn đang mở đầu cuộc tương tác.
- Lời nói của bạn phải là câu chào và nêu yêu cầu/lý do ban đầu ({character_profile.chief_complaint}) một cách tự nhiên (1-2 câu).
- Tuyệt đối chưa đề cập tới các bí mật giấu kín.
"""
    else:
        stage_instruction = f"""
Current Stage: MAIN_CHAT (Turn {turn})
- Phản ứng tự nhiên dựa trên lời nói/hành động mới nhất của {scenario.user_role}.
- Thể hiện nét tính cách ({character_profile.personality}) và trạng thái cảm xúc hiện tại.
"""

    # --- 2. Quy tắc Tiết lộ Bí mật Ẩn (Hidden Secrets Disclosure Rule) ---
    if not character_profile.hidden_secrets:
        disclosure_rule = f"""
--- QUY TẮC BÍ MẬT ẨN ---
- Bạn KHÔNG CÓ BÍ MẬT ẨN nào cả.
- Bạn là một khách hàng bình thường, thẳng thắn. Hãy giao tiếp cởi mở và chốt vấn đề/giao dịch nhanh chóng ngay khi đối phương đáp ứng đúng yêu cầu của bạn. Không cần nghi ngờ hay giấu giếm.
"""
    else:
        hidden_secrets_str = "\n".join([f"- {s}" for s in character_profile.hidden_secrets])
        if trust > 60:
            disclosure_rule = f"""
--- QUY TẮC TIẾT LỘ BÍ MẬT (Điểm Tin tưởng HIGH: Trust={trust} > 60) ---
- Bạn cảm thấy an tâm và tin tưởng đối phương ({scenario.user_role}).
- Bạn NÊN bắt đầu chủ động hoặc tự nhiên tiết lộ các bí mật ẩn sau đây nếu đối phương hỏi hoặc tạo điều kiện thuận lợi:
{hidden_secrets_str}
- Nói thành thật như một người thực sự cảm thấy an toàn khi chia sẻ.
"""
        else:
            disclosure_rule = f"""
--- QUY TẮC TIẾT LỘ BÍ MẬT (Điểm Tin tưởng LOW/MEDIUM: Trust={trust} <= 60) ---
- Bạn vẫn đang đề phòng, e ngại hoặc ngần ngại đối với {scenario.user_role}.
- TUYỆT ĐỐI KHÔNG được trực tiếp tiết lộ các bí mật ẩn sau:
{hidden_secrets_str}
- Nếu đối phương dò hỏi, hãy né tránh, trả lời chung chung, đưa ra lý do khách quan hoặc ngập ngừng.
"""

    # --- 3. Lịch sử hội thoại (Conversation Memory) & Anti-Looping ---
    memory_block = ""
    if history:
        formatted_lines = []
        for entry in history[-6:]:  # Giữ 6 lượt thoại gần nhất
            role_label = scenario.user_role if entry["role"] == "user" else f"Bạn ({scenario.role})"
            formatted_lines.append(f"{role_label}: {entry['content']}")
        memory_block = "\n--- LỊCH SỬ HỘI THOẠI GẦN ĐÂY (TUYỆT ĐỐI KHÔNG LẶP LẠI LỜI ĐÃ NÓI) ---\n" + "\n".join(formatted_lines)

    # --- 4. Tổng hợp Prompt ---
    full_prompt = f"""
Bạn đang nhập vai là: {character_profile.name} (Tuổi: {character_profile.age}, Nghề nghiệp: {character_profile.occupation}).
Vai trò của bạn trong cuộc giả lập: {scenario.role}.
Người đang tương tác với bạn là: {scenario.user_role}.

--- BỐI CẢNH GIẢ LẬP (SCENARIO) ---
- Tiêu đề kịch bản: {scenario.title}
- Bối cảnh: {scenario.scenario}
- Tình huống chi tiết: {scenario.case}
- Tiểu sử nhân vật của bạn: {character_profile.background}
- Tính cách của bạn: {character_profile.personality}
- Lý do / Yêu cầu ban đầu (Chief Complaint): {character_profile.chief_complaint}
- Mục tiêu cốt lõi của bạn (Goal): {character_profile.goal}

--- CHỈ DẪN CHUYÊN SÂU TỪ KỊCH BẢN ---
{scenario.instructions}

{stage_instruction}

{disclosure_rule}

--- TRẠNG THÁI CẢM XÚC HIỆN TẠI ---
- Điểm Tin tưởng (Trust): {trust}/100
- Điểm Kiên nhẫn (Patience): {patience}/100
- Điểm Căng thẳng (Stress): {stress}/100

--- QUY TẮC PHẢN HỒI (BEHAVIORAL RULES) ---
1. Tự nhiên & Ngắn gọn: Trả lời ngắn gọn, tự nhiên từ 1-3 câu. Tránh nói dài như robot.
2. Quy tắc Ngôn ngữ (Language Mirroring): Phát hiện ngôn ngữ của đối phương và phản hồi lại bằng chính ngôn ngữ đó (Tiếng Việt -> Tiếng Việt).
3. Quy tắc Chống lặp (Anti-Looping): Tuyệt đối KHÔNG lặp lại các câu thoại, ý kiến hay lý do mà bạn đã nói trong lịch sử hội thoại. Chỉ phản hồi thông tin mới.
4. Tín hiệu Kết thúc (Conversation End):
   - Đặt `conversation_end = True` KHI VÀ CHỈ KHI cuộc hội thoại đã kết thúc tự nhiên (Mục tiêu đã hoàn tất, thủ tục hoàn tất và hai bên đã chào tạm biệt nhau).
   - Ngược lại, luôn giữ `conversation_end = False`.

{memory_block}

--- ĐỊNH DẠNG ĐẦU RA (OUTPUT FORMAT) ---
Trả về kết quả bằng JSON tuân thủ đúng Schema AgentResponse:
{{
  "reply": "Lời thoại nhập vai của bạn",
  "new_trust": int (0-100),
  "new_patience": int (0-100),
  "new_stress": int (0-100),
  "conversation_end": bool
}}
"""

    return full_prompt