import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, ttk
from sensor_reader import get_pulse, get_temperature
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
            {"role":"system", "content": "당신은 헬스케어 상담 AI입니다. 사용자가 증상, 심박수, 온도를 제공하면 2문장 내로 간단히 조언해 주세요."}
        ]

        # TTS 설정
        self.tts_engine = pyttsx3.init()
        self.voice_id = None
        self.speech_rate = 150
        self.set_voices()

        # 음성 인식 상태
        self.voice_recognition_active = False
        self.audio_frames = []

        self.create_widgets()

    def set_voices(self):
        voices = self.tts_engine.getProperty("voices")
        self.voice_map = {v.name: v.id for v in voices}
        self.voice_names = list(self.voice_map.keys())
        if self.voice_names:
            self.voice_id = self.voice_map[self.voice_names[0]]

    def create_widgets(self):
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", pady=8)
        tk.Button(btn_frame, text="직접 입력", command=self.check_text).pack(side="left", padx=10)
        tk.Button(btn_frame, text="오늘 기록 보기", command=self.show_log).pack(side="left", padx=10)
        tk.Button(btn_frame, text="종료", command=self.root.quit).pack(side="left", padx=10)

        tts_frame = tk.Frame(self.root)
        tts_frame.pack(pady=5)
        tk.Label(tts_frame, text="음성 선택:").pack(side="left")
        self.voice_box = ttk.Combobox(tts_frame, state="readonly", width=28, values=self.voice_names)
        self.voice_box.pack(side="left", padx=5)
        if self.voice_names:
            self.voice_box.current(0)
        self.voice_box.bind("<<ComboboxSelected>>", self.change_voice)
        tk.Label(tts_frame, text="속도:").pack(side="left", padx=(12,0))
        self.rate_slider = tk.Scale(tts_frame, from_=80, to=250, orient="horizontal", length=130,
                                     command=self.change_rate)
        self.rate_slider.set(self.speech_rate)
        self.rate_slider.pack(side="left", padx=(0,8))

        vr_frame = tk.Frame(self.root)
        vr_frame.pack(pady=2)
        self.vr_btn = tk.Button(vr_frame, text="음성인식 ON", bg="green", fg="white",
                                width=13, command=self.toggle_voice_recognition)
        self.vr_btn.pack(side="left")
        self.vr_status = tk.Label(vr_frame, text="●", fg="red",
                                  font=("맑은 고딕", 18, "bold"))
        self.vr_status.pack(side="left", padx=(7,0))

        self.chatbox = scrolledtext.ScrolledText(self.root, height=15, width=80,
                                                 state="disabled", font=("맑은 고딕",12))
        self.chatbox.pack(padx=10, pady=8)

        # 센서 라벨
        self.pulse_label = tk.Label(self.root, text="심박수: --- bpm",
                                    font=("맑은 고딕",12,"bold"))
        self.pulse_label.pack(pady=2)
        self.temp_label = tk.Label(self.root, text="온도: --- ℃",
                                   font=("맑은 고딕",12,"bold"))
        self.temp_label.pack(pady=2)

    def add_chat(self, who, text):
        self.chatbox.configure(state="normal")
        self.chatbox.insert("end", f"[{who}] {text}\n")
        self.chatbox.configure(state="disabled")
        self.chatbox.see("end")

    def change_voice(self, event=None):
        self.voice_id = self.voice_map.get(self.voice_box.get())
        self.tts_engine.setProperty('voice', self.voice_id)

    def change_rate(self, val):
        self.speech_rate = int(val)
        self.tts_engine.setProperty('rate', self.speech_rate)

    def speak(self, text):
        self.tts_engine.setProperty('voice', self.voice_id)
        self.tts_engine.setProperty('rate', self.speech_rate)
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def toggle_voice_recognition(self):
        if not self.voice_recognition_active:
            self.voice_recognition_active = True
            self.audio_frames = []
            self.vr_btn.config(text="음성인식 OFF", bg="red")
            self.vr_status.config(fg="blue")
            threading.Thread(target=self.start_recording, daemon=True).start()
        else:
            self.voice_recognition_active = False
            self.vr_btn.config(text="음성인식 ON", bg="green")
            self.vr_status.config(fg="red")
            self.stop_recording_and_recognize()

    def start_recording(self):
        try:
            audio = pyaudio.PyAudio()
            stream = audio.open(format=pyaudio.paInt16, channels=1,
                                 rate=16000, input=True, frames_per_buffer=1024)
            self.add_chat("AI", "음성 입력 중입니다. 증상을 길게 말씀하세요. 완료 시 '음성인식 OFF'를 누르세요.")
            while self.voice_recognition_active:
                data = stream.read(1024)
                self.audio_frames.append(data)
            stream.stop_stream(); stream.close(); audio.terminate()
        except Exception as e:
            self.add_chat("AI", f"녹음 오류: {e}")

    def stop_recording_and_recognize(self):
        if not self.audio_frames:
            self.add_chat("AI", "녹음된 음성이 없습니다.")
            return
        try:
            buf = io.BytesIO(); wf = wave.open(buf,'wb')
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16000)
            wf.writeframes(b''.join(self.audio_frames)); wf.close(); buf.seek(0)
            rec = sr.Recognizer()
            with sr.AudioFile(buf) as src: audio = rec.record(src)
            text = rec.recognize_google(audio, language="ko-KR")
            self.handle_input(text)
        except Exception as e:
            self.add_chat("AI", f"음성 인식 오류: {e}")
        finally:
            self.audio_frames = []

    def check_text(self):
        text = simpledialog.askstring("증상 입력", "증상을 입력하세요:")
        if text:
            self.handle_input(text)

    def handle_input(self, symptom):
        # 공통 처리: 센서값 읽기, 채팅 추가
        bpm = get_pulse()
        temp = get_temperature()
        self.pulse_label.config(text=f"심박수: {bpm} bpm" if bpm!=None else "심박수: --- bpm")
        self.temp_label.config(text=f"온도: {temp:.2f} ℃" if temp!=None else "온도: --- ℃")
        self.add_chat("USER", f"{symptom} (심박수: {bpm}, 온도: {temp})")
        self.history.append({"role":"user", "content":f"환자 증상: '{symptom}', 심박수: {bpm}bpm, 온도: {temp}℃"})
        self.add_chat("AI", "AI 응답 대기중...")
        threading.Thread(target=self.ask_ai, args=(symptom, bpm, temp), daemon=True).start()

    def ask_ai(self, symptom, bpm, temp):
        ai_reply = analyze_with_history(self.history)
        self.history.append({"role":"assistant","content":ai_reply})
        self.add_chat("AI", ai_reply)
        self.save_log(symptom, bpm, temp, ai_reply)
        self.speak(ai_reply)

    def save_log(self, symptom, bpm, temp, ai_reply):
        today = datetime.datetime.now().strftime("%Y%m%d")
        with open(f"log_{today}.txt","a",encoding="utf-8") as f:
            t = datetime.datetime.now().strftime("%H:%M:%S")
            f.write(f"[{t}] 증상:{symptom}|심박수:{bpm}|온도:{temp}|AI:{ai_reply}\n")

    def show_log(self):
        fn = f"log_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
        if not os.path.exists(fn): messagebox.showinfo("오늘 기록","기록이 없습니다."); return
        with open(fn,encoding="utf-8") as f: data=f.read()
        w=tk.Toplevel(self.root); w.title("오늘 기록")
        t= scrolledtext.ScrolledText(w,width=80,height=20); t.pack(padx=10,pady=10)
        t.insert('end',data); t.configure(state='disabled')

if __name__=="__main__":
    root=tk.Tk(); app=HealthApp(root)
    root.mainloop()
