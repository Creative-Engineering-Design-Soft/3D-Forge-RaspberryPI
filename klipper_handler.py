import requests
import os
import json

MOONRAKER_URL = "http://localhost:7125"

def mr_get(endpoint):
    return requests.get(f"{MOONRAKER_URL}{endpoint}").json()

def mr_post(endpoint, data=None):
    return requests.post(f"{MOONRAKER_URL}{endpoint}", json=data).json()

def Log(title, content):
    print(f"[ {title} ] >> {content}")


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
def stopPrint():
    mr_post("/printer/print/cancel")
    Log("Print", "Canceled")
