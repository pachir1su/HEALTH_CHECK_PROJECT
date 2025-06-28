# sensor_reader.py

import random

def get_pulse():
    """
    실제 센서가 없을 때는 랜덤값 반환.
    실제 아두이노/심박수 센서 연결 코드로 교체 가능.
    """
    return random.randint(60, 140)
