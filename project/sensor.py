# 센서 확장용 구조만 남겨둠
# 실제 센서가 추가되면 여기서 값 읽어서 report로 전달

def get_sensor_data():
    return {
        "temperature": None,
        "humidity": None,
        "camera": None,
    }
