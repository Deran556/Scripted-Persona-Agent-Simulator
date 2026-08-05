"""
state_machine.py - Bộ quản lý Trạng thái Cảm xúc Nhân vật (State Machine)

Quản lý các thông số cảm xúc động của nhân vật (Trust, Patience, Stress).
Đảm bảo điểm số luôn nằm trong khoảng hợp lệ [0, 100].
"""

from typing import Optional
from models import InitialState


def make_initial_state(initial_config: Optional[InitialState] = None) -> dict:
    """Tạo mới một dictionary trạng thái ban đầu dựa trên cấu hình kịch bản."""
    if initial_config:
        return {
            "patience": initial_config.patience,
            "trust": initial_config.trust,
            "stress": initial_config.stress,
            "conversation_end": initial_config.conversation_end
        }
    return {
        "patience": 100,
        "trust": 50,
        "stress": 0,
        "conversation_end": False
    }


def clamp_state(state: dict) -> None:
    """Cắt giới hạn điểm cảm xúc trong đoạn từ 0 đến 100."""
    for key in ["patience", "trust", "stress"]:
        if key in state:
            state[key] = max(0, min(100, int(state[key])))


def update_state(state: dict, new_trust: int, new_patience: int, new_stress: int) -> None:
    """
    Cập nhật điểm cảm xúc được chấm bởi Gemini API và cắt giới hạn 0-100.

    Args:
        state (dict): Dictionary trạng thái hiện tại
        new_trust (int): Điểm tin tưởng mới
        new_patience (int): Điểm kiên nhẫn mới
        new_stress (int): Điểm căng thẳng mới
    """
    state["trust"] = new_trust
    state["patience"] = new_patience
    state["stress"] = new_stress
    clamp_state(state)


def reset_state(state: dict, initial_config: Optional[InitialState] = None) -> None:
    """Đặt lại trạng thái về ban đầu."""
    if initial_config:
        state["patience"] = initial_config.patience
        state["trust"] = initial_config.trust
        state["stress"] = initial_config.stress
        state["conversation_end"] = initial_config.conversation_end
    else:
        state["patience"] = 100
        state["trust"] = 50
        state["stress"] = 0
        state["conversation_end"] = False


def can_reveal_secret(state: dict) -> bool:
    """Trả về True nếu điểm Trust đã vượt ngưỡng 60 để tiết lộ bí mật ẩn."""
    return state.get("trust", 0) > 60