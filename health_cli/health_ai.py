# health_ai.py

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("`.env` 파일에 GOOGLE_API_KEY를 설정하세요.")

# 최신 Gemini 엔드포인트(v1beta, gemini-1.5-flash)
GEN_AI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def analyze_with_history(history):
    """
    history: [
        {"role": "system",    "content": "당신은 헬스케어 상담 AI입니다."},
        {"role": "user",      "content": "환자 증상: 기침, 심박수: 80bpm"},
        {"role": "assistant", "content": "현재 기침과 80bpm이라면..."},
        ...
    ]
    """
    # Gemini 채팅 REST API는 아래와 같은 "contents" 구조를 요구
    contents = []
    for turn in history:
        role = turn["role"]
        content = turn["content"]
        if role == "system":
            # system 프롬프트는 첫 user 역할의 직전 메시지로 넣는 것이 가장 자연스럽습니다.
            # 하지만, v1beta는 'system' 역할을 따로 지원하지 않으니, 첫 user 메시지로 포함.
            contents.append({
                "role": "user",
                "parts": [{"text": content}]
            })
        elif role == "user":
            contents.append({
                "role": "user",
                "parts": [{"text": content}]
            })
        elif role == "assistant":
            contents.append({
                "role": "model",
                "parts": [{"text": content}]
            })
    
    body = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.95,
            "maxOutputTokens": 256
        }
    }

    headers = {"Content-Type": "application/json; charset=utf-8"}
    params = {"key": GOOGLE_API_KEY}

    try:
        response = requests.post(
            GEN_AI_ENDPOINT,
            params=params,
            headers=headers,
            data=json.dumps(body)
        )
        response.raise_for_status()
        data = response.json()
        # 응답에서 텍스트 추출 (최신 API 구조 기준)
        candidates = data.get("candidates", [])
        if not candidates:
            return "[Gemini 오류] AI 응답 없음"
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return "[Gemini 오류] AI 텍스트 파싱 실패"
        reply_text = parts[0].get("text", "").strip()
        return reply_text

    except requests.exceptions.HTTPError:
        try:
            err = response.json()
            return f"[Gemini API 오류] HTTP {response.status_code} - {err}"
        except Exception:
            return f"[Gemini API 오류] HTTP {response.status_code}"
    except Exception as e:
        return f"[Gemini API 오류] {e}"
