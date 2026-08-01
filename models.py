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

class AgentResponse(BaseModel):
    """
    Structured JSON output enforced by Gemini's response schema.
    The LLM evaluates its own emotional response and signals conversation completion.
    """
    reply: str = Field(
        description="The patient's spoken dialogue in the SAME language as the pharmacist's latest message."
    )
    new_trust: int = Field(
        description="Updated trust score (0-100). Increase if the pharmacist is empathetic/professional, decrease if intrusive/rude."
    )
    new_patience: int = Field(
        description="Updated patience score (0-100). Decrease if the pharmacist is slow, repetitive, or interrogating."
    )
    new_stress: int = Field(
        description="Updated stress score (0-100). Increase if the pharmacist asks too many questions without resolving anything."
    )
    conversation_end: bool = Field(
        default=False,
        description="Set to true ONLY when the consultation has naturally concluded: medicine dispensed AND payment done AND both parties are saying goodbye."
    )

class EvaluationReport(BaseModel):
    out_of_character: bool = Field(description="True if the patient acted out of character or broke persona rules.")
    emotion_logic_score: int = Field(description="Score from 1-10 evaluating if trust and patience updated logically.")
    unlock_turn: int = Field(description="Turn index (0..max_turns-1) when hidden info was revealed, or -1 if never unlocked.")
    critique: str = Field(description="Detailed qualitative evaluation and feedback for the simulation.")