import requests
import os
import json
import datetime

MOONRAKER_URL = "http://localhost:7125"

def mr_get(endpoint):
    return requests.get(f"{MOONRAKER_URL}{endpoint}", timeout=5).json()

def mr_post(endpoint, data=None):
    response = requests.post(f"{MOONRAKER_URL}{endpoint}", json=data, timeout=5)
    
    if response.status_code != 200:
        print(f"[ API Error ] >> {endpoint} Failed! Status: {response.status_code}, Body: {response.text}")
    
    return response.json()

def Log(title, content):
    # 1. 기본적으로 콘솔(PM2 로그)에는 무조건 출력
    print(f"[ {title} ] >> {content}")

    # 2. 'Stop', 'Cancel', 'FORCE' 같은 단어가 포함된 경우에만 파일로 저장
    if "Stop" in title or "STOP" in str(content) or "CANCEL" in str(content) or "FORCE" in str(content):
        try:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # 'stop_log.txt' 파일에 이어쓰기(append) 모드로 저장
            with open("stop_log.txt", "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [ {title} ] >> {content}\n")
        except Exception:
            pass # 파일 저장 실패해도 서버는 멈추지 않게 함


# ===============================
#  Klipper 상태 가져오기
# ===============================
def getPrinterStatus():
    try:
        r = mr_get("/printer/objects/query?heater_bed&extruder&toolhead&print_stats&display_status")
        status = r["result"]["status"]

        bed = status["heater_bed"]["temperature"]
        nozzle = status["extruder"]["temperature"]

        pos = status["toolhead"]["position"]
        x, y, z = pos[0], pos[1], pos[2]

        printing = 1 if status["print_stats"]["state"] == "printing" else 0

        progress_float = status.get("display_status", {}).get("progress", 0)
        progress_percent = (progress_float * 100)

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
        Log("KlipperStatusError", e)
        return {
            "bedTemp": 0,
            "nozzleTemp": 0,
            "percent": 0,
            "x": 0, "y": 0, "z": 0,
            "isPrinting": 0,
            "isConnected": 0
        }


# ===============================
#  파일 업로드 (출력은 안 함) - 수정됨
# ===============================
def uploadFile(local_path):
    try:
        filename = os.path.basename(local_path)
        url = f"{MOONRAKER_URL}/server/files/upload"
        
        with open(local_path, "rb") as f:
            files = {"file": (filename, f, "application/octet-stream")}
            requests.post(url, files=files)

        Log("Upload", f"Uploaded ready: {filename}")
        return filename # 파일명을 반환해서 handler가 기억하게 함
    except Exception as e:
        Log("UploadError", e)
        return None

# ===============================
#  파일명으로 출력 시작 - 신규 추가
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
#  프린트 중지/취소
# ===============================
#def stopPrint():
#    mr_post("/printer/print/cancel")
#    Log("Print", "Canceled")

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