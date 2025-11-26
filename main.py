import socketio
import requests
import time
import json
import os
import threading

# ==========================================
# [사용자 수정 필요] 설정 변수
# ==========================================
HARDWARE_ID = "YOUR_HARDWARE_ID_HERE"      # 예: "pi-lab-101"
EXTERNAL_SERVER_URL = "YOUR_SERVER_URL"    # 예: "http://192.168.0.10:3000"

# [고정] 로컬 Moonraker API 주소 (Mainsail OS 기본값)
MOONRAKER_URL = "http://127.0.0.1:7125"
# ==========================================

sio = socketio.Client()

# --- [Moonraker(Klipper) 제어 함수들] ---

def moonraker_upload_and_print(file_content, filename="job.gcode"):
    upload_url = f"{MOONRAKER_URL}/server/files/upload"
    
    files = {'file': (filename, file_content)}
    data = {'root': 'gcodes', 'print': 'true'}
    
    try:
        print(f"[Moonraker] Uploading {filename} and starting print...")
        res = requests.post(upload_url, files=files, data=data)
        
        if res.status_code in [200, 201]:
            print(f"[Moonraker] Success: {res.json()}")
            return True
        else:
            print(f"[Moonraker] Error: {res.text}")
            return False
    except Exception as e:
        print(f"[Moonraker] Connection Error: {e}")
        return False

def get_printer_status():
    # Klipper 상태 조회 (노즐 온도, 베드 온도, 상태, 진행률)
    query_url = f"{MOONRAKER_URL}/printer/objects/query?extruder&heater_bed&print_stats&display_status"
    try:
        res = requests.get(query_url, timeout=2)
        if res.status_code == 200:
            return res.json().get('result', {}).get('status', {})
    except Exception:
        return None
    return None

# --- [Socket.IO 이벤트 핸들러] ---

@sio.event
def connect():
    print("Connected to server!")
    # [사용자 수정 필요] 서버 연결 시 인증 방식 확인 필요
    # 현재는 하드웨어 ID만 보내는 것으로 되어 있음
    sio.emit("register", {"hardwareId": HARDWARE_ID})

@sio.event
def disconnect():
    print("Disconnected from server.")

@sio.on("print")
def on_print(data):
    print("Print command received:", data)

    # [사용자 수정 필요] 웹 서버에서 보내주는 데이터의 Key 값이 "fileUrl"이 맞는지 확인 필요
    fileUrl = data.get("fileUrl") 
    
    if not fileUrl:
        print("No gcode file URL provided")
        return

    print(f"Downloading gcode from: {fileUrl}")
    
    try:
        response = requests.get(fileUrl)
        if response.status_code != 200:
            print("Failed to download file from web server")
            return
        
        gcode_content = response.content
        
        # 파일명 추출 (URL 구조에 따라 수정 필요할 수 있음)
        filename = fileUrl.split("/")[-1] if "/" in fileUrl else "web_job.gcode"
        if not filename.endswith(".gcode"): 
            filename += ".gcode"

        moonraker_upload_and_print(gcode_content, filename)

    except Exception as e:
        print(f"Error during print process: {e}")

@sio.on("test")
def on_test(data):
    print("Test signal received:", data)

# --- [백그라운드 상태 전송 스레드] ---

def status_reporter():
    while True:
        if sio.connected:
            status = get_printer_status()
            if status:
                # [사용자 수정 필요] 웹 서버가 원하는 JSON 포맷에 맞춰 키(Key) 이름을 수정해야 함
                payload = {
                    "hardwareId": HARDWARE_ID,
                    
                    # 예: 웹 서버가 "nozzle_temp"라는 키를 원하면 아래를 수정
                    "temp_nozzle": status.get('extruder', {}).get('temperature', 0),
                    "temp_bed": status.get('heater_bed', {}).get('temperature', 0),
                    
                    # 상태: printing, paused, standby 등
                    "state": status.get('print_stats', {}).get('state', 'unknown'),
                    
                    # 진행률: 0.0 ~ 1.0
                    "progress": status.get('display_status', {}).get('progress', 0)
                }
                
                # [사용자 수정 필요] 웹 서버가 받기로 한 이벤트 이름 확인 ("status_update"가 맞는지?)
                try:
                    sio.emit("status_update", payload) 
                except Exception as e:
                    print(f"Failed to emit status: {e}")
        
        time.sleep(2)

# --- [메인 실행 루프] ---

if __name__ == "__main__":
    t = threading.Thread(target=status_reporter, daemon=True)
    t.start()

    while True:
        try:
            if not sio.connected:
                # [사용자 수정 필요] EXTERNAL_SERVER_URL 변수가 채워져야 실행됨
                if EXTERNAL_SERVER_URL == "YOUR_SERVER_URL":
                    print("Error: EXTERNAL_SERVER_URL is not set.")
                    time.sleep(5)
                    continue

                print(f"Connecting to {EXTERNAL_SERVER_URL}...")
                sio.connect(EXTERNAL_SERVER_URL, transports=['websocket'])
                sio.wait()
        except Exception as e:
            print(f"Connection failed/lost, retrying in 3 sec... Error: {e}")
            time.sleep(3)