# TTS
import pyttsx3

def speak(text):
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)  # 말하는 속도 (기본: 200)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS 오류: {e}")
