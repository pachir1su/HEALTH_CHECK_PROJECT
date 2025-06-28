# 이 파일 실행

import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, ttk
from sensor_reader import get_pulse
from health_ai import analyze_with_history
import threading
import pyttsx3
import datetime
import speech_recognition as sr
import pyaudio
import wave
import io
import os

class HealthApp:
    def __init__(self, root):
        self.root = root
        self.root.title("건강 체크 챗봇")
        self.history = [
            {"role":"system", "content": "당신은 헬스케어 상담 AI입니다. 사용자가 증상과 심박수를 제공하면 2문장 내로 간단히 조언해 주세요."}
        ]

        # TTS 설정
        self.tts_engine = pyttsx3.init()
        self.voice_id = None
        self.speech_rate = 150
        self.set_voices()

        # 음성 인식 상태
        self.voice_recognition_active = False
        self.audio_frames = []
        self.audio_stream = None
        self.audio = None

        self.create_widgets()

    def set_voices(self):
        voices = self.tts_engine.getProperty("voices")
        self.voice_map = {v.name: v.id for v in voices}
        self.voice_names = list(self.voice_map.keys())
        if self.voice_names:
            self.voice_id = self.voice_map[self.voice_names[0]]

    def create_widgets(self):
        # 버튼 프레임
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", pady=8)

        tk.Button(btn_frame, text="직접 입력", command=self.check_text).pack(side="left", padx=10)
        tk.Button(btn_frame, text="오늘 기록 보기", command=self.show_log).pack(side="left", padx=10)
        tk.Button(btn_frame, text="종료", command=self.root.quit).pack(side="left", padx=10)

        # TTS 음성/속도 설정
        tts_frame = tk.Frame(self.root)
        tts_frame.pack(pady=5)
        tk.Label(tts_frame, text="음성 선택:").pack(side="left")
        self.voice_box = ttk.Combobox(tts_frame, state="readonly", width=28)
        self.voice_box.pack(side="left", padx=5)
        self.voice_box["values"] = self.voice_names
        self.voice_box.bind("<<ComboboxSelected>>", self.change_voice)
        if self.voice_names:
            self.voice_box.current(0)
        tk.Label(tts_frame, text="속도:").pack(side="left", padx=(12,0))
        self.rate_slider = tk.Scale(tts_frame, from_=80, to=250, orient="horizontal", length=130, command=self.change_rate)
        self.rate_slider.set(self.speech_rate)
        self.rate_slider.pack(side="left", padx=(0,8))

        # 음성 인식 활성화/상태 표시
        vr_frame = tk.Frame(self.root)
        vr_frame.pack(pady=2)
        self.vr_btn = tk.Button(vr_frame, text="음성인식 ON", bg="green", fg="white", width=13, command=self.toggle_voice_recognition)
        self.vr_btn.pack(side="left")
        self.vr_status = tk.Label(vr_frame, text="●", fg="red", font=("맑은 고딕", 18, "bold"))
        self.vr_status.pack(side="left", padx=(7,0))

        # 채팅창
        self.chatbox = scrolledtext.ScrolledText(self.root, height=15, width=80, state="disabled", font=("맑은 고딕", 12))
        self.chatbox.pack(padx=10, pady=8)
        self.pulse_label = tk.Label(self.root, text="심박수: --- bpm", font=("맑은 고딕", 12, "bold"))
        self.pulse_label.pack(pady=2)

    def add_chat(self, who, text):
        self.chatbox.configure(state="normal")
        self.chatbox.insert("end", f"[{who}] {text}\n")
        self.chatbox.configure(state="disabled")
        self.chatbox.see("end")

    def change_voice(self, event=None):
        name = self.voice_box.get()
        self.voice_id = self.voice_map.get(name)
        self.tts_engine.setProperty('voice', self.voice_id)

    def change_rate(self, val):
        self.speech_rate = int(val)
        self.tts_engine.setProperty('rate', self.speech_rate)

    def speak(self, text):
        try:
            self.tts_engine.setProperty('voice', self.voice_id)
            self.tts_engine.setProperty('rate', self.speech_rate)
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"[TTS 오류] {e}")

    def toggle_voice_recognition(self):
        if not self.voice_recognition_active:
            # ON: 녹음 시작
            self.voice_recognition_active = True
            self.audio_frames = []
            self.vr_btn.config(text="음성인식 OFF", bg="red")
            self.vr_status.config(fg="blue")  # 듣는 중
            threading.Thread(target=self.start_recording).start()
        else:
            # OFF: 녹음 중지+STT
            self.voice_recognition_active = False
            self.vr_btn.config(text="음성인식 ON", bg="green")
            self.vr_status.config(fg="red")
            self.stop_recording_and_recognize()

    def start_recording(self):
        try:
            self.audio = pyaudio.PyAudio()
            stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
            self.audio_stream = stream
            self.add_chat("AI", "음성 입력 중입니다. 증상을 길게 말씀하세요. 완료 시 '음성인식 OFF'를 누르세요.")
            while self.voice_recognition_active:
                data = stream.read(1024)
                self.audio_frames.append(data)
            stream.stop_stream()
            stream.close()
            self.audio.terminate()
        except Exception as e:
            self.add_chat("AI", f"녹음 오류: {e}")

    def stop_recording_and_recognize(self):
        if not self.audio_frames:
            self.add_chat("AI", "녹음된 음성이 없습니다.")
            return
        try:
            wav_buffer = io.BytesIO()
            wf = wave.open(wav_buffer, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16bit
            wf.setframerate(16000)
            wf.writeframes(b''.join(self.audio_frames))
            wf.close()
            wav_buffer.seek(0)
            rec = sr.Recognizer()
            with sr.AudioFile(wav_buffer) as source:
                audio = rec.record(source)
            text = rec.recognize_google(audio, language="ko-KR")
            self.add_chat("USER", text)
            # 이어서 AI 분석/응답/로그 저장
            pulse = get_pulse()
            self.pulse_label.config(text=f"심박수: {pulse} bpm")
            self.history.append({"role":"user", "content":f"환자 증상: '{text}', 심박수: {pulse}bpm"})
            self.add_chat("AI", "AI 응답 대기중...")
            threading.Thread(target=self.ask_ai, args=(text, pulse)).start()
        except sr.UnknownValueError:
            self.add_chat("AI", "음성 인식 실패(잘 들리지 않음)")
        except Exception as e:
            self.add_chat("AI", f"음성 인식 오류: {e}")
        finally:
            self.audio_frames = []

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

    def ask_ai(self, symptom, pulse):
        ai_reply = analyze_with_history(self.history)
        self.history.append({"role":"assistant", "content":ai_reply})
        self.add_chat("AI", ai_reply)
        self.save_log(symptom, pulse, ai_reply)
        self.speak(ai_reply)

    def save_log(self, symptom, pulse, ai_reply):
        today = datetime.datetime.now().strftime("%Y%m%d")
        with open(f"log_{today}.txt", "a", encoding="utf-8") as f:
            time_str = datetime.datetime.now().strftime("%H:%M:%S")
            f.write(f"[{time_str}] 증상: {symptom} | 심박수: {pulse} | AI: {ai_reply}\n")

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

if __name__ == "__main__":
    root = tk.Tk()
    app = HealthApp(root)
    root.mainloop()
