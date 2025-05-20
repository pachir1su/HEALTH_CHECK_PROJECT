import os
import google.generativeai as genai

from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def analyze(symptom, pulse):
    prompt = (
    f"환자가 '{symptom}' 증상, 심박수 {pulse}bpm입니다. "
    "2문장 이내로 짤막하게 건강 상태를 조언해 주세요."
)


    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Gemini 응답 오류: {e}"
