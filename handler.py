import env
import requests
import os

def Log(title, content):
    print(f"[ {title} ] >> {content}")


# --- [내부 유틸] Moonraker API 호출 함수 ---
def _klipper_get(endpoint):
    try:
        url = f"{env.MOONRAKER_URL}{endpoint}"
        res = requests.get(url, timeout=2)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        Log("KlipperError", f"GET failed: {e}")
    return None

def _klipper_upload_and_print(filepath, filename):
    """
    로컬에 다운받은 파일을 Moonraker로 전송하고 출력을 시작함
    """
    url = f"{env.MOONRAKER_URL}/server/files/upload"
    try:
        with open(filepath, 'rb') as f:
            # print='true' 옵션을 주면 업로드 후 즉시 출력 시작
            files = {'file': (filename, f)}
            data = {'root': 'gcodes', 'print': 'true'}
            
            res = requests.post(url, files=files, data=data)
            if res.status_code in [200, 201]:
                Log("Klipper", f"Upload & Print Success: {filename}")
                return True
            else:
                Log("Klipper", f"Upload Failed: {res.text}")
    except Exception as e:
        Log("Klipper", f"Connection Error: {e}")
    return False


# --- [메인 로직] ---

def getStatus(data):
    """
    Klipper에서 실제 상태값 조회
    """
    # 쿼리: 압출기(extruder), 베드(heater_bed), 출력상태(print_stats), 위치(toolhead)
    endpoint = "/printer/objects/query?extruder&heater_bed&print_stats&toolhead"
    res = _klipper_get(endpoint)
    
    # 기본값 (연결 안 됐을 때)
    status_payload = {
        "hardwareId": env.HARDWARE_ID,
        "bedTemp": 0,
        "nozzleTemp": 0,
        "isPrinting": False,
        "state": "disconnected",
        "isConnected": False,
        "x": 0, "y": 0, "z": 0
    }

    if res and 'result' in res:
        klipper = res['result']['status']
        
        # 데이터 매핑
        status_payload.update({
            "bedTemp": klipper.get('heater_bed', {}).get('temperature', 0),
            "nozzleTemp": klipper.get('extruder', {}).get('temperature', 0),
            "state": klipper.get('print_stats', {}).get('state', 'standby'),
            "isPrinting": klipper.get('print_stats', {}).get('state') == "printing",
            "isConnected": True,
            "x": klipper.get('toolhead', {}).get('position', [0,0,0])[0],
            "y": klipper.get('toolhead', {}).get('position', [0,0,0])[1],
            "z": klipper.get('toolhead', {}).get('position', [0,0,0])[2],
        })
        
    return status_payload
    
def downloadFile(data):
    """
    1. 외부 웹에서 파일 다운로드 -> 'downloads' 폴더 저장
    2. Klipper로 업로드 및 출력 시작
    """
    # data 구조가 { "filepath": "/uploads/test.gcode" } 라고 가정
    filepath_server = data.get("filepath")
    if not filepath_server:
        Log("Handler", "Filepath not provided in data")
        return

    # URL 생성 (앞에 슬래시 처리 주의)
    if not filepath_server.startswith("/"):
        filepath_server = "/" + filepath_server
        
    file_url = env.SERVER_URL + filepath_server
    filename = os.path.basename(filepath_server)
    
    # 로컬 저장 경로
    local_dir = "downloads"
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, filename)

    Log("Download", f"Start: {file_url}")

    try:
        # 1. 파일 다운로드
        response = requests.get(file_url)
        if response.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(response.content)
            Log("Download", f"Saved to {local_path}")
            
            # 2. Klipper로 전송 및 출력 시작
            _klipper_upload_and_print(local_path, filename)
            
        else:
            Log("DownloadError", f"HTTP Status: {response.status_code}")

    except Exception as e:
        Log("Exception", f"Download process failed: {e}")