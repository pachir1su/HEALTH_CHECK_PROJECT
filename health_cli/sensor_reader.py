import serial
import time
import random

def read_sensors(timeout=3):
    if not initialize_sensor():
        return None, None

    bpm, temp = None, None
    start = time.time()

    while time.time() - start < timeout:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("BPM:"):
                bpm = int(line.split("BPM:")[1])
            elif line.startswith("TEMP:"):
                temp = float(line.split("TEMP:")[1])
            if bpm is not None and temp is not None:
                return bpm, temp
        except Exception as e:
            continue

    return None, None


# --- 설정 값 ---
SERIAL_PORT = 'COM12'   # Windows 예시 → Raspberry Pi: '/dev/ttyACM0'
BAUD_RATE = 9600

ser = None

def initialize_sensor():
    global ser
    if ser and ser.is_open:
        return True
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        time.sleep(2)
        print(f"✅ 센서 연결 성공: {SERIAL_PORT}")
        return True
    except Exception as e:
        print(f"❌ 센서 연결 실패: {e}")
        ser = None
        return False

def read_sensors(timeout=5):
    """BPM과 TEMP를 함께 읽어서 반환합니다."""
    if not initialize_sensor():
        return get_simulated_data("센서 미연결")
    bpm = None
    temp = None
    start = time.time()
    while True:
        if time.time() - start > timeout:
            break
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith("BPM:"):
            try:
                bpm = int(line.split("BPM:")[1])
            except ValueError:
                pass
        elif line.startswith("TEMP:"):
            val = line.split("TEMP:")[1]
            if val != "ERR":
          
                try:
                    temp = float(val)
                    
                except ValueError:
                    pass
        if bpm is not None and temp is not None:
            break
    return bpm, temp

def get_pulse():
    """심박수(BPM)만 반환합니다."""
    bpm, _ = read_sensors()
    return bpm

def get_temperature():
    """온도(TEMP)만 반환합니다."""
    _, temp = read_sensors()
    return temp 

def get_simulated_data(reason=""):
    print(f"⚠️ 시뮬레이트 데이터 사용 (사유: {reason})")
    return random.randint(60, 100), round(random.uniform(34.5, 42.0), 2)

def close_sensor():
    global ser
    if ser and ser.is_open:
        ser.close()
        print("🔌 센서 연결 종료")
