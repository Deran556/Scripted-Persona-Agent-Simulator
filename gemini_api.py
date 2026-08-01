"""
gemini_api.py - Gemini API Calls

Changes from previous version:
- ask_gemini() enforces strict Pydantic JSON schema via response_schema=AgentResponse.
- Returns parsed AgentResponse object instead of raw text, giving caller direct access to
  reply, new_trust, new_patience, new_stress, and conversation_end.
- generate_dynamic_patient() unchanged except documentation improvements.
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
from models import Patient, AgentResponse, Difficulty, Stage

client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------------------------------------------------------
# Patient Diversity Pools
# ---------------------------------------------------------------------------
MALE_NAMES = [
    "Nguyễn Văn An", "Trần Minh Khoa", "Lê Hoàng Nam", "Phạm Quốc Bảo",
    "Vũ Đức Thắng", "Đặng Tuấn Anh", "Bùi Huy Hoàng", "Đỗ Thanh Tùng",
    "Phan Việt Cường", "Ngo Thành Long"
]

FEMALE_NAMES = [
    "Nguyễn Thị Mai", "Trần Thu Hà", "Lê Phương Thảo", "Phạm Bích Ngọc",
    "Vũ Khánh Linh", "Đặng Hương Giang", "Bùi Anh Thư", "Đỗ Hải Yến",
    "Phan Như Quỳnh", "Ngo Thanh Vân"
]

OCCUPATIONS = [
    "Student", "Teacher", "Office Worker", "Engineer", "Driver",
    "Chef", "Factory Worker", "Farmer", "Salesperson", "Programmer",
    "Accountant", "Freelancer", "Retired", "Construction Worker", "Nurse"
]

PERSONALITY_STYLES = [
    "Friendly", "Reserved", "Anxious", "Suspicious", "Impatient", "Talkative", "Confident"
]

AGE_GROUPS = [
    (18, 30),
    (31, 45),
    (46, 60),
    (61, 80)
]


def ask_gemini(system_prompt: str, user_input: str) -> AgentResponse:
    """
    Calls Gemini to generate a patient response, strictly enforcing AgentResponse JSON schema.
    
    Returns:
        AgentResponse: Parsed Pydantic object with reply, new_trust, new_patience,
                       new_stress, and conversation_end fields.
    """
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"""
{system_prompt}

Pharmacist's latest message:
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
    # Parse directly into the Pydantic model for strict validation
    return AgentResponse.model_validate_json(response.text)


def generate_dynamic_patient(difficulty: str = None) -> Patient:
    """
    Generates a diverse, randomized patient profile.
    Python pre-generates demographic constraints before calling Gemini to ensure diversity.
    """
    if not difficulty:
        difficulty = random.choice([d.value for d in Difficulty])

    # 🎲 Pre-select diversity constraints in Python (not delegated to LLM)
    gender = random.choice(["Male", "Female"])
    selected_name = random.choice(MALE_NAMES if gender == "Male" else FEMALE_NAMES)
    min_age, max_age = random.choice(AGE_GROUPS)
    selected_age = random.randint(min_age, max_age)
    selected_occupation = random.choice(OCCUPATIONS)
    selected_personality = random.choice(PERSONALITY_STYLES)

    system_instruction = f"""
    You are a medical simulation expert designing practice scenarios for pharmacy students.
    Generate a realistic patient profile based on these pre-determined parameters:

    --- PRE-DETERMINED PARAMETERS (do NOT change these) ---
    - Name: {selected_name}
    - Gender: {gender}
    - Age: {selected_age} (range: {min_age}-{max_age})
    - Occupation: {selected_occupation}
    - Personality Style: {selected_personality}
    - Difficulty: {difficulty}

    Requirements:
    1. Use the EXACT Name, Age, and Occupation above. Do NOT change them.
    2. Generate a realistic chief_complaint (surface symptom/initial visit reason).
    3. Generate 1-4 hidden_information items (true medical facts that could cause drug interactions or safety risks if missed by the pharmacist).
    4. Vary the case type: young adults, parents, office workers, manual workers, pregnant women, elderly — NOT always elderly with chronic disease.
    5. Design for two stages: {Stage.GREETING.value} (brief opening) and {Stage.MAIN_CHAT.value} (probing dialogue).
    """

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=system_instruction,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Patient,
            temperature=0.9,
        ),
    )

    patient_data = json.loads(response.text)
    return Patient(**patient_data)