import json
from google import genai
from google.genai import types
from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    TEMPERATURE,
    MAX_OUTPUT_TOKENS,
    TOP_P,
)
from models import Patient

client = genai.Client(api_key=GEMINI_API_KEY)

def ask_gemini(system_prompt, user_input):
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"""
{system_prompt}

User:
{user_input}
""",
        config={
            "temperature": TEMPERATURE,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "top_p": TOP_P,
        },
    )
    # Strip any potential leading/trailing quotes and extra whitespace
    return response.text.strip('"\n ')

def generate_dynamic_patient(difficulty="difficult, hesitant, hiding underlying health conditions"):
    system_instruction = f"""
    You are a medical simulation expert designing practice scenarios for pharmacy students.
    Generate a random, realistic patient profile based on the following difficulty requirements: {difficulty}.
    
    Requirements:
    1. The patient has a chief complaint (surface-level symptom).
    2. The patient hides critical facts (hidden_information) that could lead to drug interactions or health risks if the pharmacist fails to ask proper probing questions.
    3. Ensure the patient's name, age, occupation, personality, and goals are logically aligned with the scenario.
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