import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
from sensor_reader import get_pulse
from health_ai import analyze_with_history
import threading
import pyttsx3
import datetime
import speech_recognition as sr

# TTS 함수
def speak(text):
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[TTS 오류] {e}")

# 로그 저장 함수
def save_log(symptom, pulse, ai_reply):
    today = datetime.datetime.now().strftime("%Y%m%d")
    with open(f"log_{today}.txt", "a", encoding="utf-8") as f:
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        f.write(f"[{time_str}] 증상: {symptom} | 심박수: {pulse} | AI: {ai_reply}\n")

# 음성 인식 함수 (스레드에서 실행)
def recognize_speech_from_mic(callback):
    rec = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            callback("AI", "음성 입력 대기 중...(마이크에 대고 증상을 말하세요)")
            rec.adjust_for_ambient_noise(source, duration=0.3)
            audio = rec.listen(source, phrase_time_limit=5)
            text = rec.recognize_google(audio, language="ko-KR")
            callback("USER", text)
            return text
    except sr.UnknownValueError:
        callback("AI", "음성 인식 실패(잘 들리지 않음)")
        return None
    except Exception as e:
        callback("AI", f"음성 인식 오류: {e}")
        return None

class HealthApp:
    def __init__(self, root):
        self.root = root
        self.root.title("건강 체크 챗봇")
        self.history = [
            {"role":"system", "content": "당신은 헬스케어 상담 AI입니다. 사용자가 증상과 심박수를 제공하면 2문장 내로 간단히 조언해 주세요."}
        ]
        self.create_widgets()

    def create_widgets(self):
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", pady=10)

        tk.Button(btn_frame, text="건강 체크(음성)", command=self.check_voice).pack(side="left", padx=10)
        tk.Button(btn_frame, text="직접 입력", command=self.check_text).pack(side="left", padx=10)
        tk.Button(btn_frame, text="오늘 기록 보기", command=self.show_log).pack(side="left", padx=10)
        tk.Button(btn_frame, text="종료", command=self.root.quit).pack(side="left", padx=10)

        self.chatbox = scrolledtext.ScrolledText(self.root, height=15, width=75, state="disabled", font=("맑은 고딕", 12))
        self.chatbox.pack(padx=10, pady=10)
        self.pulse_label = tk.Label(self.root, text="심박수: --- bpm", font=("맑은 고딕", 12, "bold"))
        self.pulse_label.pack(pady=3)

    def add_chat(self, who, text):
        self.chatbox.configure(state="normal")
        self.chatbox.insert("end", f"[{who}] {text}\n")
        self.chatbox.configure(state="disabled")
        self.chatbox.see("end")

    def check_text(self):
        symptom = simpledialog.askstring("증상 입력", "증상을 입력하세요:")
        if not symptom:
            return
        pulse = get_pulse()
        self.pulse_label.config(text=f"심박수: {pulse} bpm")
        self.add_chat("USER", f"{symptom} (심박수: {pulse})")
        self.history.append({"role":"user", "content":f"환자 증상: '{symptom}', 심박수: {pulse}bpm"})
        self.add_chat("AI", "AI 응답 대기중...")
        threading.Thread(target=self.ask_ai, args=(symptom, pulse)).start()

    def check_voice(self):
        def async_voice():
            symptom = recognize_speech_from_mic(self.add_chat)
            if not symptom:
                return
            pulse = get_pulse()
            self.pulse_label.config(text=f"심박수: {pulse} bpm")
            self.history.append({"role":"user", "content":f"환자 증상: '{symptom}', 심박수: {pulse}bpm"})
            self.add_chat("AI", "AI 응답 대기중...")
            self.ask_ai(symptom, pulse)
        threading.Thread(target=async_voice).start()

    def ask_ai(self, symptom, pulse):
        ai_reply = analyze_with_history(self.history)
        self.history.append({"role":"assistant", "content":ai_reply})
        self.add_chat("AI", ai_reply)
        save_log(symptom, pulse, ai_reply)
        speak(ai_reply)

    def show_log(self):
        today = datetime.datetime.now().strftime("%Y%m%d")
        log_file = f"log_{today}.txt"
        if not os.path.exists(log_file):
            messagebox.showinfo("오늘 기록", "기록이 없습니다.")
            return
        with open(log_file, encoding="utf-8") as f:
            content = f.read()
        log_win = tk.Toplevel(self.root)
        log_win.title("오늘 기록")
        text_widget = scrolledtext.ScrolledText(log_win, width=80, height=20)
        text_widget.pack(padx=10, pady=10)
        text_widget.insert("end", content)
        text_widget.configure(state="disabled")

import os

if __name__ == "__main__":
    root = tk.Tk()
    app = HealthApp(root)
    root.mainloop()