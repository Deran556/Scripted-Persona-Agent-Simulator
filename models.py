from pydantic import BaseModel
from typing import List

class Personality(BaseModel):
    social: str     # e.g., "introvert", "extrovert"
    honesty: str    # e.g., "high", "medium", "low"
    temper: str     # e.g., "calm", "impatient", "irritable"

class AgentResponse(BaseModel):
    reply: str

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