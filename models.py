"""
models.py - Khung dữ liệu Pydantic Schema cho Generic Markdown Scenario Engine

Cập nhật:
- Thêm ComplaintGenerationRules và SecretGenerationRules hỗ trợ Gemini tự động sinh ngẫu nhiên
  lý do đến khám (chief_complaint) và bí mật ẩn (hidden_secrets) theo luật (Rules).
- Cập nhật ScenarioSchema hỗ trợ cả 2 chế độ (tương thích ngược):
  + Chế độ cũ: chief_complaint / hidden_secrets chuỗi/mảng tĩnh điền sẵn trong YAML.
  + Chế độ mới: complaint_generation_rules / secret_generation_rules tự động sinh qua Gemini API.
- Đảm bảo 100% tất cả các trường đều có Pydantic Field(default=...) hoặc Field(default_factory=...)
  để ứng dụng không bao giờ bị crash do thiếu dữ liệu từ file .md.
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
    Bể dữ liệu động bốc ngẫu nhiên thông số nhân vật (Tên, Tuổi, Nghề nghiệp, Tính cách, Chief Complaints, Project Topics).
    """
    names: List[str] = Field(
        default_factory=lambda: ["Nguyễn Văn A", "Trần Thị B"],
        description="Danh sách tên ngẫu nhiên"
    )
    age_ranges: List[List[int]] = Field(
        default_factory=lambda: [[20, 30]],
        description="Các khoảng tuổi ngẫu nhiên [min_age, max_age]"
    )
    occupations: List[str] = Field(
        default_factory=lambda: ["Sinh viên", "Nhân viên"],
        description="Danh sách nghề nghiệp ngẫu nhiên"
    )
    personalities: List[str] = Field(
        default_factory=lambda: ["Cởi mở, hợp tác", "Rụt rè, ngần ngại", "Gắt gỏng, vội vã"],
        description="Danh sách các nhóm nét tính cách"
    )
    chief_complaints: List[str] = Field(
        default_factory=list,
        description="Bể lý do đến khám / yêu cầu ban đầu (nếu có)"
    )
    project_topics: List[str] = Field(
        default_factory=list,
        description="Bể đề tài đồ án / công việc (nếu có)"
    )


class ComplaintGenerationRules(BaseModel):
    """
    Cấu hình hướng dẫn Gemini AI tự động sinh lý do đến khám/yêu cầu ban đầu (chief_complaint) sống động.
    """
    instruction: str = Field(
        default="Sinh ra 1 câu lý do đến khám/yêu cầu ngắn gọn, tự nhiên và phù hợp với vai trò nhân vật.",
        description="Chỉ dẫn chuyên biệt cho Gemini sinh lý do mở đầu"
    )
    allowed_symptom_scopes: List[str] = Field(
        default_factory=lambda: ["Các vấn đề sức khỏe phổ biến", "Tư vấn chuyên môn"],
        description="Phạm vi chủ đề hoặc triệu chứng được phép sinh"
    )


class SecretGenerationRules(BaseModel):
    """
    Cấu hình cho phép Gemini AI tự động sinh ngẫu nhiên 1-3 bí mật ẩn dựa theo các chủ đề (Topics).
    """
    min_secrets: int = Field(default=0, description="Số lượng bí mật tối thiểu cần sinh")
    max_secrets: int = Field(default=3, description="Số lượng bí mật tối đa cần sinh")
    instruction: str = Field(
        default="Sinh ra bí mật ẩn liên quan đến vấn đề đang hỏi và hoàn cảnh nhân vật.",
        description="Chỉ dẫn cho Gemini khi sinh bí mật ẩn"
    )
    secret_topics: List[str] = Field(
        default_factory=lambda: ["Thói quen xấu", "Thông tin chưa kể"],
        description="Danh sách chủ đề gợi ý để AI sinh bí mật ẩn"
    )


class InitialState(BaseModel):
    """
    Điểm trạng thái cảm xúc ban đầu của nhân vật (0-100).
    """
    trust: int = Field(default=50, description="Điểm tin tưởng ban đầu (0-100)")
    patience: int = Field(default=100, description="Điểm kiên nhẫn ban đầu (0-100)")
    stress: int = Field(default=10, description="Điểm căng thẳng ban đầu (0-100)")
    conversation_end: bool = Field(default=False, description="Cờ trạng thái kết thúc cuộc hội thoại")


class CompletionRules(BaseModel):
    """
    Quy tắc ngắt cuộc hội thoại để tránh lỗi vô hạn turn (Infinite Loop).
    """
    max_turns: int = Field(default=10, description="Số turn tối đa trước khi cưỡng chế ngắt")
    completion_keywords: List[str] = Field(
        default_factory=lambda: ["[DONE]", "[PASSED]", "[FAILED]", "[PAYMENT]", "[DONE_DEFENSE]"],
        description="Từ khóa/tag hành động từ phía User hoặc Tester để kết thúc hội thoại"
    )


class UserAction(BaseModel):
    """
    Định nghĩa nút bấm thao tác nghiệp vụ trên Dynamic Action Bar.
    """
    label: str = Field(default="Thao tác", description="Tên hiển thị trên nút bấm")
    action_tag: str = Field(default="NONE", description="Mã tag đính kèm vào tin nhắn chat")
    description: str = Field(default="", description="Mô tả công dụng của hành động")


class TestConfig(BaseModel):
    """
    Cấu hình kiểm thử tự động LLM-vs-LLM cho auto_test.py.
    """
    tester_role: str = Field(default="Evaluator", description="Vai trò của AI 1 (Tester)")
    tester_system_prompt: str = Field(default="", description="System prompt định hướng cho AI 1")
    evaluation_criteria: List[str] = Field(
        default_factory=list,
        description="Các tiêu chí đánh giá cho AI 2 (Evaluator)"
    )


class ScenarioSchema(BaseModel):
    """
    Pydantic Schema tổng thể đại diện cho Kịch bản (.md file).
    Tương thích ngược hoàn hảo cả chế độ cũ (chuỗi tĩnh) và chế độ mới (dynamic rules).
    Sử dụng Field(default=...) cho TẤT CẢ thuộc tính, đảm bảo 100% không bao giờ crash nếu thiếu Form.
    """
    title: str = Field(default="Kịch bản mặc định", description="Tiêu đề kịch bản")
    role: str = Field(default="Nhân vật mô phỏng", description="Vai trò của Agent")
    user_role: str = Field(default="Người tương tác", description="Vai trò của User")
    scenario: str = Field(default="", description="Tóm tắt bối cảnh tổng quan")
    case: str = Field(default="", description="Chi tiết tình huống cụ thể")
    
    # Hỗ trợ tương thích ngược cho chief_complaint & hidden_secrets chuỗi/mảng tĩnh
    chief_complaint: Optional[str] = Field(
        default=None,
        description="Lý do/Yêu cầu mở đầu tĩnh (dùng tương thích ngược nếu file .md điền trực tiếp)"
    )
    hidden_secrets: Optional[List[str]] = Field(
        default=None,
        description="Danh sách bí mật ẩn tĩnh (dùng tương thích ngược nếu file .md điền trực tiếp)"
    )
    
    # Quy tắc sinh động mới
    complaint_generation_rules: Optional[ComplaintGenerationRules] = Field(
        default_factory=ComplaintGenerationRules,
        description="Quy tắc tự động sinh lý do mở đầu ngẫu nhiên qua Gemini API"
    )
    secret_generation_rules: Optional[SecretGenerationRules] = Field(
        default_factory=SecretGenerationRules,
        description="Quy tắc tự động sinh bí mật ẩn ngẫu nhiên qua Gemini API"
    )
    
    goal: str = Field(default="", description="Mục tiêu cốt lõi của nhân vật")
    
    dynamic_pools: DynamicPools = Field(default_factory=DynamicPools, description="Bể dữ liệu bốc ngẫu nhiên")
    initial_state: InitialState = Field(default_factory=InitialState, description="Trạng thái cảm xúc khởi tạo")
    completion_rules: CompletionRules = Field(default_factory=CompletionRules, description="Quy tắc ngắt hội thoại")
    user_actions: List[UserAction] = Field(default_factory=list, description="Thao tác nghiệp vụ trên Action Bar")
    test_config: TestConfig = Field(default_factory=TestConfig, description="Cấu hình chạy auto test")
    
    instructions: str = Field(default="", description="Nội dung Markdown Body (chứa chỉ dẫn chuyên sâu)")


class CharacterProfile(BaseModel):
    """
    Profile chi tiết của nhân vật được sinh tự động bởi Gemini API.
    """
    name: str = Field(default="Nguyễn Văn A", description="Họ tên nhân vật")
    age: int = Field(default=22, description="Tuổi nhân vật")
    occupation: str = Field(default="Sinh viên", description="Nghề nghiệp")
    personality: str = Field(default="Cởi mở, hợp tác", description="Tính cách đặc trưng")
    background: str = Field(default="", description="Tiểu sử / Hoàn cảnh chi tiết")
    chief_complaint: str = Field(default="", description="Lý do / Lời mở đầu công khai")
    hidden_secrets: List[str] = Field(default_factory=list, description="Danh sách các bí mật ẩn")
    goal: str = Field(default="", description="Mục tiêu hành động")


class AgentResponse(BaseModel):
    """
    Structured Output JSON nhận từ Gemini API cho mỗi lượt thoại của Agent.
    """
    reply: str = Field(
        description="Lời thoại nhập vai của nhân vật"
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
        description="True nếu cuộc hội thoại đã kết thúc tự nhiên và hai bên chào tạm biệt"
    )


class EvaluationReport(BaseModel):
    """
    Kết quả chấm điểm phiên mô phỏng từ AI 2 (Evaluator).
    """
    out_of_character: bool = Field(description="True nếu Agent đóng sai vai hoặc vi phạm nguyên tắc persona")
    emotion_logic_score: int = Field(description="Điểm 1-10 đánh giá tính logic khi biến đổi cảm xúc")
    unlock_turn: int = Field(description="Turn index (0-indexed) tiết lộ bí mật ẩn (-1 nếu chưa bao giờ tiết lộ)")
    critique: str = Field(description="Đánh giá định tính chi tiết bằng Tiếng Việt")