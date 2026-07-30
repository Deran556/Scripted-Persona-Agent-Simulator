from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class Stage(str, Enum):
    GREETING = "Greeting"
    MAIN_CHAT = "Main Chat"

class Difficulty(str, Enum):
    EASY = "Dễ tính, cởi mở, hợp tác"
    MEDIUM = "Bình thường, hơi ngần ngại"
    HARD = "Khó tính, hay bực bội, đang giấu bệnh nền"
    VERY_HARD = "Gắt gỏng, nghi ngờ, cố tình né tránh câu hỏi"

class Personality(BaseModel):
    social: str     # e.g., "introvert", "extrovert"
    honesty: str    # e.g., "high", "medium", "low"
    temper: str     # e.g., "calm", "impatient", "irritable"

class Patient(BaseModel):
    name: str
    age: int
    occupation: str
    personality: Personality
    scenario: str
    case: str
    chief_complaint: str
    hidden_information: List[str]
    goal: str

# 🚀 NEW: The LLM will now evaluate the state itself!
class AgentResponse(BaseModel):
    reply: str = Field(description="The spoken dialogue of the patient. Do NOT use quotation marks.")
    new_patience: int = Field(description="Evaluate the pharmacist's tone. Decrease if rushed/rude, increase if empathetic. (0-100)")
    new_trust: int = Field(description="Evaluate the pharmacist's professionalism. Increase if they explain safety reasons well. (0-100)")
    new_stress: int = Field(description="Increase if the pharmacist asks too many interrogating questions without building trust. (0-100)")