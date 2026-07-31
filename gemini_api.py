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
# Patient Diversity Pools (Names, Demographics, Occupations, Personalities)
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

def ask_gemini(system_prompt, user_input):
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"""
{system_prompt}

User:
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
    return response.text.strip()

def generate_dynamic_patient(difficulty=None):
    if not difficulty:
        difficulty_options = [d.value for d in Difficulty]
        difficulty = random.choice(difficulty_options)

    # 🎲 Pre-generate random Python demographic constraints before calling Gemini
    gender = random.choice(["Male", "Female"])
    selected_name = random.choice(MALE_NAMES if gender == "Male" else FEMALE_NAMES)
    
    min_age, max_age = random.choice(AGE_GROUPS)
    selected_age = random.randint(min_age, max_age)
    
    selected_occupation = random.choice(OCCUPATIONS)
    selected_personality = random.choice(PERSONALITY_STYLES)

    system_instruction = f"""
    You are a medical simulation expert designing practice scenarios for pharmacy students.
    Generate a realistic patient profile based strictly on the following pre-determined parameters:

    --- PRE-DETERMINED PATIENT PARAMETERS ---
    - Name: {selected_name}
    - Gender: {gender}
    - Age: {selected_age} (Age group range: {min_age}-{max_age})
    - Occupation: {selected_occupation}
    - Personality Style: {selected_personality}
    - Scenario Difficulty: {difficulty}

    Requirements & Diversity Guidelines:
    1. Use the EXACT Name, Age, and Occupation provided above. Do NOT change them.
    2. Generate a chief_complaint (surface symptom / initial request) appropriate for this persona and demographic.
    3. Generate hidden_information (1-4 true medical facts/conditions/medications) that present drug interactions or health risks if the pharmacist fails to probe carefully.
    4. Ensure high demographic diversity: generate young adults, college students, parents, office workers, manual workers, pregnant women, as well as elderly. Avoid repeatedly generating elderly patients with chronic diseases.
    5. Design the scenario to support interaction stages: Stage 1 ({Stage.GREETING.value}) for initial greeting/complaint, and Stage 2 ({Stage.MAIN_CHAT.value}) for detailed dialogue.
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