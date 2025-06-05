# voice_chat.py

import time
import speech_recognition as sr
import pyttsx3
from sensor_reader import get_pulse
from health_ai import analyze_with_history

def speak(text):
    """pyttsx3를 이용한 간단 TTS"""
    if not text:
        return
    engine = pyttsx3.init()
    engine.setProperty("rate", 150)
    engine.say(text)
    engine.runAndWait()

def listen_from_mic(rec, mic):
    """마이크로부터 5초 동안 듣고, Google STT로 변환하여 문자열 반환"""
    with mic as source:
        print("⏳ 음성 인식 중... 말을 해주세요.")
        rec.adjust_for_ambient_noise(source, duration=0.3)
        audio = rec.listen(source, phrase_time_limit=5)
    try:
        return rec.recognize_google(audio, language="ko-KR")
    except sr.UnknownValueError:
        print("⚠ 음성 인식 실패: 잘 들리지 않음.")
        return None
    except sr.RequestError as e:
        print(f"⚠ 음성 인식 요청 오류: {e}")
        return None

def main():
    print("=== 터미널 헬스 체크 챗봇 CLI ===")
    print("증상을 말하면 심박수를 포함하여 AI가 조언해줍니다.")
    print("종료하려면 '종료'라고 말하거나 Ctrl+C 입력\n")

    rec = sr.Recognizer()
    mic = sr.Microphone()

    # 대화 히스토리 초기화 (시스템 메시지 포함)
    history = [
        {"role":"system", "content":
         "당신은 헬스케어 상담 AI입니다. 사용자가 증상과 심박수를 제공하면 "
         "2문장 내로 간단히 조언해 주세요."}
    ]

    try:
        while True:
            user_speech = listen_from_mic(rec, mic)
            if user_speech is None:
                continue

            user_speech = user_speech.strip()
            print(f">> 사용자: {user_speech}")

            if user_speech in ["종료", "끝내기", "그만"]:
                print("프로그램을 종료합니다.")
                break

            # 심박수 읽기
            pulse = get_pulse()
            print(f"▶ 현재 심박수: {pulse} bpm")

            # 히스토리에 사용자 메시지+심박수 정보 추가
            symptom_msg = f"환자 증상: '{user_speech}', 심박수: {pulse}bpm"
            history.append({"role":"user", "content":symptom_msg})

            # Gemini API 호출
            print("⏳ AI에게 질의 중...")
            ai_reply = analyze_with_history(history)
            print(f"<< AI: {ai_reply}")

            # 히스토리에 AI 응답 추가
            history.append({"role":"assistant", "content":ai_reply})

            # TTS로 읽어주기
            speak(ai_reply)
            print()
            time.sleep(0.3)

    except KeyboardInterrupt:
        print("\n프로그램을 강제 종료합니다.")

if __name__ == "__main__":
    main()
