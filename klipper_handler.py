import requests
import os
import json
import datetime # [필수] 날짜 기록용

MOONRAKER_URL = "http://localhost:7125"

# [수정] timeout을 5초로 넉넉하게 설정 (네트워크 지연 대비)
def mr_get(endpoint):
    return requests.get(f"{MOONRAKER_URL}{endpoint}", timeout=5).json()

def mr_post(endpoint, data=None):
    return requests.post(f"{MOONRAKER_URL}{endpoint}", json=data, timeout=5).json()

# [수정] 로그 함수 업그레이드 (파일 저장 기능 추가)
def Log(title, content):
    # 1. 기본 콘솔 출력
    print(f"[ {title} ] >> {content}")

    try:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_dir = os.path.dirname(os.path.abspath(__file__)) # 현재 파일 위치 기준

        # 2. 정지/취소 로그 저장 (stop_log.txt)
        if "Stop" in title or "STOP" in str(content) or "CANCEL" in str(content) or "FORCE" in str(content):
            log_path = os.path.join(current_dir, "stop_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [ {title} ] >> {content}\n")

        # 3. [신규] 업로드 관련 로그 저장 (upload_log.txt)
        if "Upload" in title:
            log_path = os.path.join(current_dir, "upload_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [ {title} ] >> {content}\n")

    except Exception:
        pass # 파일 저장 실패해도 서버는 멈추지 않음


# ===============================
#  Klipper 상태 가져오기
# ===============================
def getPrinterStatus():
    try:
        # [수정] 쿼리 타임아웃도 적용됨 (mr_get 내부에서 처리)
        r = mr_get("/printer/objects/query?heater_bed&extruder&toolhead&print_stats&display_status")
        status = r["result"]["status"]

        bed = status["heater_bed"]["temperature"]
        nozzle = status["extruder"]["temperature"]

        pos = status["toolhead"]["position"]
        x, y, z = pos[0], pos[1], pos[2]

        printing = 1 if status["print_stats"]["state"] == "printing" else 0

        progress_float = status.get("display_status", {}).get("progress", 0)
        progress_percent = int(progress_float * 100)

        return {
            "bedTemp": bed,
            "nozzleTemp": nozzle,
            "percent": progress_percent,
            "x": x,
            "y": y,
            "z": z,
            "isPrinting": printing,
            "isConnected": 1,
        }
    except Exception as e:
        Log("KlipperStatusError", f"Connection Lost: {e}")
        return {
            "bedTemp": 0,
            "nozzleTemp": 0,
            "percent": 0,
            "x": 0, "y": 0, "z": 0,
            "isPrinting": 0,
            "isConnected": 0
        }


# ===============================
#  파일 업로드 (수정됨)
# ===============================
def uploadFile(local_path):
    try:
        filename = os.path.basename(local_path)
        url = f"{MOONRAKER_URL}/server/files/upload"
        
        with open(local_path, "rb") as f:
            files = {"file": (filename, f, "application/octet-stream")}
            # 파일 업로드 등 큰 작업은 시간을 넉넉하게 (30초)
            response = requests.post(url, files=files, timeout=30)
            
            # 응답 코드 확인
            if response.status_code == 201: # 201 Created
                Log("Upload", f"Uploaded ready: {filename}")
                return filename
            else:
                Log("UploadError", f"Failed with status code: {response.status_code}, response: {response.text}")
                return None

    except Exception as e:
        Log("UploadError", e)
        return None

# ===============================
#  파일명으로 출력 시작
# ===============================
def startPrint(filename):
    try:
        mr_post("/printer/print/start", {"filename": filename})
        Log("Print", f"Print Start: {filename}")
    except Exception as e:
        Log("StartError", e)
        

# ===============================
#  개별 GCODE 명령 전송
# ===============================
def sendGcode(cmd: str):
    try:
        mr_post("/printer/gcode/script", {"script": cmd})
        Log("GCODE", f"Executed: {cmd}")
    except Exception as e:
        Log("GcodeError", e)


# ===============================
#  프린트 중지/취소 (수정됨)
# ===============================
def stopPrint():
    try:
        Log("Print", "Attempting to STOP...")
        
        res1 = mr_post("/printer/gcode/script", {"script": "CANCEL_PRINT"})
        Log("Debug", f"CANCEL_PRINT Result: {res1}")

        res2 = mr_post("/printer/gcode/script", {"script": "SDCARD_RESET_FILE"})
        Log("Debug", f"SDCARD_RESET Result: {res2}")


        Log("Print", "Sent FORCE STOP commands")
    except Exception as e:
        Log("StopError", e)