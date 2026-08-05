"""
models.py - Khung dữ liệu Pydantic Schema cho Generic Markdown Scenario Engine

Định nghĩa toàn bộ các Pydantic Schema tổng quát được sử dụng trong hệ thống:
- DynamicPools: Các bể dữ liệu ngẫu nhiên (tên, tuổi, nghề nghiệp, tính cách)
- InitialState: Điểm cảm xúc khởi tạo (trust, patience, stress)
- CompletionRules: Quy tắc kết thúc hội thoại (max_turns, completion_keywords)
- UserAction: Định nghĩa các action button trên giao diện
- TestConfig: Cấu hình cho framework kiểm thử tự động auto_test.py
- ScenarioSchema: Schema tổng thể nạp từ file kịch bản .md
- CharacterProfile: Profile nhân vật chi tiết được sinh bởi LLM
- AgentResponse: JSON Schema bắt buộc cho phản hồi của Agent
- EvaluationReport: Báo cáo đánh giá chất lượng phiên giả lập
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class Stage(str, Enum):
    """Các giai đoạn của cuộc hội thoại"""
    GREETING = "Greeting"
    MAIN_CHAT = "Main Chat"


class DynamicPools(BaseModel):
    """
    Bể dữ liệu động cho phép bốc ngẫu nhiên thông số nhân vật.
    Sử dụng Field(default=...) để đảm bảo fallback nếu file .md thiếu dữ liệu.
    """
    names: List[str] = Field(
        default_factory=lambda: ["Nguyễn Văn A", "Trần Thị B", "Lê Văn C", "Phạm Thị D"],
        description="Danh sách tên ngẫu nhiên"
    )
    age_ranges: List[List[int]] = Field(
        default_factory=lambda: [[18, 25], [26, 35], [36, 50]],
        description="Các khoảng tuổi ngẫu nhiên [min_age, max_age]"
    )
    occupations: List[str] = Field(
        default_factory=lambda: ["Sinh viên", "Nhân viên văn phòng", "Kỹ sư", "Giáo viên"],
        description="Danh sách nghề nghiệp ngẫu nhiên"
    )
    personalities: List[str] = Field(
        default_factory=lambda: ["Thân thiện, cởi mở", "Rụt rè, lo lắng", "Bình tĩnh, tự tin", "Gắt gỏng, nghi ngờ"],
        description="Danh sách nét tính cách ngẫu nhiên"
    )


class InitialState(BaseModel):
    """
    Điểm trạng thái cảm xúc ban đầu của nhân vật (0-100).
    """
    trust: int = Field(default=50, description="Điểm tin tưởng ban đầu (0-100)")
    patience: int = Field(default=100, description="Điểm kiên nhẫn ban đầu (0-100)")
    stress: int = Field(default=0, description="Điểm căng thẳng ban đầu (0-100)")
    conversation_end: bool = Field(default=False, description="Trạng thái kết thúc hội thoại")


class CompletionRules(BaseModel):
    """
    Quy tắc ngắt hội thoại để tránh lỗi vô hạn turn (Infinite Loop).
    """
    max_turns: int = Field(default=10, description="Số turn tối đa trước khi cưỡng chế ngắt")
    completion_keywords: List[str] = Field(
        default_factory=lambda: ["[DONE]", "[KET_THUC]", "[DONE_DEFENSE]", "[HOAN_THANH]"],
        description="Các từ khóa/tag tín hiệu kết thúc từ phía User hoặc Tester"
    )


class UserAction(BaseModel):
    """
    Định nghĩa một nút bấm thao tác trên Dynamic Action Bar (Streamlit UI / Auto Test).
    """
    label: str = Field(default="Hành động", description="Tên hiển thị trên button UI")
    action_tag: str = Field(default="NONE", description="Mã tag đính kèm vào tin nhắn chat")
    description: str = Field(default="", description="Mô tả công dụng của hành động")


class TestConfig(BaseModel):
    """
    Cấu hình chạy kiểm thử tự động LLM-vs-LLM cho auto_test.py.
    """
    tester_role: str = Field(default="Giám khảo", description="Vai trò của AI 1 (Tester)")
    tester_system_prompt: str = Field(default="", description="System prompt định hướng cho AI 1")
    evaluation_criteria: List[str] = Field(
        default_factory=lambda: [
            "Kiểm tra xem Agent có giữ đúng vai không",
            "Kiểm tra xem điểm số cảm xúc cập nhật có hợp lý không",
            "Kiểm tra xem bí mật ẩn có được tiết lộ khi Trust > 60 hay không"
        ],
        description="Danh sách các tiêu chí để AI 2 (Evaluator) chấm điểm"
    )


class ScenarioSchema(BaseModel):
    """
    Pydantic Schema tổng thể của một Kịch bản (Scenario).
    Tích hợp Pydantic Field(default=...) đảm bảo 100% không crash khi file .md bị thiếu thuộc tính.
    """
    title: str = Field(default="Kịch bản mặc định", description="Tiêu đề kịch bản")
    role: str = Field(default="Nhân vật mô phỏng", description="Vai trò của Agent (ví dụ: Sinh viên, Bệnh nhân)")
    user_role: str = Field(default="Người tương tác", description="Vai trò của User (ví dụ: Giám khảo, Dược sĩ)")
    scenario: str = Field(default="", description="Tóm tắt bối cảnh tổng quan")
    case: str = Field(default="", description="Chi tiết ca mô phỏng cụ thể")
    chief_complaint: str = Field(default="", description="Yêu cầu/Lý do ban đầu nhân vật đưa ra công khai")
    hidden_secrets: List[str] = Field(default_factory=list, description="Danh sách các sự thật ẩn / bí mật")
    goal: str = Field(default="", description="Mục tiêu cốt lõi của nhân vật")
    
    dynamic_pools: DynamicPools = Field(default_factory=DynamicPools, description="Bể dữ liệu bốc ngẫu nhiên")
    initial_state: InitialState = Field(default_factory=InitialState, description="Điểm cảm xúc ban đầu")
    completion_rules: CompletionRules = Field(default_factory=CompletionRules, description="Quy tắc ngắt hội thoại")
    user_actions: List[UserAction] = Field(default_factory=list, description="Danh sách nút bấm thao tác UI")
    test_config: TestConfig = Field(default_factory=TestConfig, description="Cấu hình test tự động")
    
    instructions: str = Field(default="", description="Nội dung Markdown Body (chứa chỉ dẫn chuyên sâu)")


class CharacterProfile(BaseModel):
    """
    Profile chi tiết của nhân vật sau khi được Gemini sinh ra dựa trên ScenarioSchema và DynamicPools.
    """
    name: str = Field(default="Nguyễn Văn A", description="Tên nhân vật")
    age: int = Field(default=22, description="Tuổi nhân vật")
    occupation: str = Field(default="Sinh viên", description="Nghề nghiệp")
    personality: str = Field(default="Bình tĩnh", description="Tính cách đặc trưng")
    background: str = Field(default="", description="Tiểu sử / Hoàn cảnh chi tiết")
    chief_complaint: str = Field(default="", description="Lý do / Lời mở đầu công khai")
    hidden_secrets: List[str] = Field(default_factory=list, description="Các bí mật ẩn của nhân vật này")
    goal: str = Field(default="", description="Mục tiêu hành động")


class AgentResponse(BaseModel):
    """
    Schema phản hồi từ Gemini API (Structured Output JSON).
    Đánh giá trạng thái tâm lý và cờ kết thúc hội thoại.
    """
    reply: str = Field(
        description="Lời thoại của nhân vật, phản hồi lại tin nhắn mới nhất"
    )
    new_trust: int = Field(
        description="Điểm tin tưởng mới cập nhật (0-100)"
    )
    new_patience: int = Field(
        description="Điểm kiên nhẫn mới cập nhật (0-100)"
    )
    new_stress: int = Field(
        description="Điểm căng thẳng mới cập nhật (0-100)"
    )
    conversation_end: bool = Field(
        default=False,
        description="Đánh dấu True nếu cuộc hội thoại đã hoàn thành tự nhiên và hai bên chia tay"
    )


class EvaluationReport(BaseModel):
    """
    Báo cáo chấm điểm từ AI 2 (Evaluator) trong auto_test.py.
    """
    out_of_character: bool = Field(description="True nếu Agent đóng sai vai hoặc vi phạm nguyên tắc persona")
    emotion_logic_score: int = Field(description="Thang điểm 1-10 đánh giá tính logic khi thay đổi cảm xúc")
    unlock_turn: int = Field(description="Turn (0-indexed) tiết lộ bí mật ẩn, hoặc -1 nếu chưa bao giờ tiết lộ")
    critique: str = Field(description="Nhận xét định tính chi tiết về phiên mô phỏng")