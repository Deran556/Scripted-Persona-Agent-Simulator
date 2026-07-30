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

    system_instruction = f"""
    You are a medical simulation expert designing practice scenarios for pharmacy students.
    Generate a random, realistic patient profile based on the following difficulty level: {difficulty}.
    
    Requirements:
    1. The patient has a chief complaint (surface-level symptom).
    2. The patient hides critical facts (hidden_information) that could lead to drug interactions or health risks if the pharmacist fails to ask proper probing questions.
    3. Ensure the patient's name, age, occupation, personality, and goals are logically aligned with the scenario.
    4. Design the patient scenario to support interaction stages: Stage 1 ({Stage.GREETING.value}) for initial greeting/complaint, and Stage 2 ({Stage.MAIN_CHAT.value}) for detailed dialogue.
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