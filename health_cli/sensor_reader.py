# sensor_reader.py

import serial
import time
import random

# --- 설정 값 ---
SERIAL_PORT = 'COM11'  # 예시: Windows
BAUD_RATE = 9600      # 통신 속도

# 시리얼 객체를 전역으로 관리하여 연결을 유지
ser = None

def initialize_sensor():
    """
    시리얼 포트 연결을 시도하고, 실패 시 None을 반환.
    프로그램 시작 시 한 번만 호출하는 것이 효율적입니다.
    """
    global ser
    if ser and ser.is_open:
        return True
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        time.sleep(2)  # 아두이노가 리셋되고 안정화될 때까지 잠시 대기
        print(f"✅ 센서 연결 성공: {SERIAL_PORT}")
        return True
    except serial.SerialException as e:
        print(f"❌ 센서 연결 실패: {e}")
        print("    - 아두이노가 올바른 포트에 연결되었는지 확인하세요.")
        print("    - sensor_reader.py의 SERIAL_PORT 변수를 수정해야 할 수 있습니다.")
        ser = None
        return False

def get_pulse():
    """
    연결된 아두이노로부터 심박수 값을 읽어 정수로 반환합니다.
    연결 실패 또는 데이터 읽기 오류 시, 시뮬레이션된 랜덤 값을 반환합니다.
    """
    global ser
    if ser is None or not ser.is_open:
        # 센서 연결이 안 되어 있을 경우, 랜덤 값으로 대체
        return get_simulated_pulse("센서 미연결")

    try:
        # 아두이노에서 "Pulse: 75"와 같은 형식으로 데이터가 온다고 가정
        # 또는 숫자만 올 수도 있음. 아두이노 코드에 맞춰야 함.
        line = ser.readline().decode('utf-8').strip()
        
        if line:
            # 숫자만 넘어오는 경우
            pulse_value = int(line)
            return pulse_value
        else:
            # 데이터가 들어오지 않는 경우 (타임아웃 등)
            return get_simulated_pulse("데이터 없음")
            
    except (ValueError, TypeError):
        # "Pulse: 75" 처럼 텍스트가 섞여 있거나, 잘못된 값이 들어올 경우
        # 이 부분은 아두이노에서 보내는 데이터 형식에 따라 커스터마이징이 필요합니다.
        return get_simulated_pulse("데이터 파싱 오류")
    except serial.SerialException:
        # 읽는 도중 연결이 끊겼을 경우
        ser.close()
        ser = None
        return get_simulated_pulse("연결 끊김")

def get_simulated_pulse(reason=""):
    """시뮬레이션된 랜덤 심박수 값을 반환하고 이유를 출력합니다."""
    print(f"⚠️  실제 센서 값 대신 랜덤 값을 사용합니다. (사유: {reason})")
    return random.randint(60, 150)

def close_sensor():
    """프로그램 종료 시 시리얼 포트를 닫습니다."""
    global ser
    if ser and ser.is_open:
        ser.close()
        print("🔌 센서 연결이 종료되었습니다.")

# 이 파일을 직접 실행하여 센서 연결을 테스트할 수 있음.
if __name__ == '__main__':
    if initialize_sensor():
        try:
            for i in range(10):
                pulse = get_pulse()
                print(f"측정된 심박수: {pulse} bpm")
                time.sleep(1)
        finally:
            close_sensor()
    else:
        print("테스트를 위해 랜덤 값을 사용합니다.")
        for i in range(5):
            pulse = get_pulse()
            print(f"측정된 심박수 (랜덤): {pulse} bpm")
            time.sleep(1)
