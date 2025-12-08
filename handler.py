import env
import requests
import os
import datetime
import re
import klipper_handler as mr

# ===============================
#  설정 및 전역 변수
# ===============================
OPERATOR = ['START', 'PAUSE', 'FINISH']
current_op = OPERATOR[0]

latest_filename = None
is_downloading = False


# ===============================
# LOG
# ===============================
def Log(title, content):
    print(f"[ {title} ] >> {content}")
    try:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_dir = os.path.dirname(os.path.abspath(__file__))

        if ("Stop" in title or "STOP" in str(content) or "CANCEL" in str(content)
            or "FORCE" in str(content) or "Action" in title):

            if ("Action" not in title or
                ("Canceled" in str(content) or
                 "Finished" in str(content) or
                 "Paused" in str(content))):
                log_path = os.path.join(current_dir, "stop_log.txt")
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}] [ {title} ] >> {content}\n")

        if "Upload" in title or "Download" in title:
            log_path = os.path.join(current_dir, "upload_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [ {title} ] >> {content}\n")
    except:
        pass


# ===============================
#  PRINTER STATUS
# ===============================
def getStatus(data):
    printer_status = mr.getPrinterStatus()
    return {
        "hardwareId": env.HARDWARE_ID,
        "bedTemp": printer_status.get("bedTemp", 0),
        "nozzleTemp": printer_status.get("nozzleTemp", 0),
        "isPrinting": printer_status.get("isPrinting", 0),
        "isConnected": printer_status.get("isConnected", 0),
        "percent": printer_status.get("percent", 0),
        "x": printer_status.get("x", 0),
        "y": printer_status.get("y", 0),
        "z": printer_status.get("z", 0),
        "status": current_op
    }


# ===============================
# GOOGLE DRIVE DOWNLOADER
# ===============================
def download_from_google_drive(url, dst_path):
    Log("GDrive", f"Detected Google Drive: {url}")

    session = requests.Session()

    # 1. 파일 ID 추출
    match = re.search(r"/d/([^/]+)", url)
    if not match:
        Log("GDriveError", "File ID not found")
        return None

    file_id = match.group(1)
    Log("GDrive", f"File ID: {file_id}")

    base = "https://drive.google.com/uc?export=download"

    # 2. 첫 요청 (토큰 확인 목적)
    response = session.get(base, params={"id": file_id}, stream=True)

    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value
            break

    # 3. confirm 토큰이 있으면 다시 요청
    if token:
        Log("GDrive", f"Confirm token: {token}")
        response = session.get(base, params={"id": file_id, "confirm": token}, stream=True)

    # 4. 다운로드 저장
    try:
        with open(dst_path, "wb") as f:
            for chunk in response.iter_content(32768):
                if chunk:
                    f.write(chunk)
        Log("GDrive", f"Saved: {dst_path}")
        return dst_path
    except Exception as e:
        Log("GDriveError", str(e))
        return None


# ===============================
# COMMAND
# ===============================
def executeCommand(data):
    global latest_filename, current_op

    raw_op = data.get("operator") or data.get("operater")
    current_op = raw_op

    if not raw_op:
        Log("CommandError", "No operator provided")
        return

    op = raw_op.upper()

    if op not in OPERATOR:
        Log("CommandError", f"Unknown operator: {raw_op}")
        return

    Log("Command", f"Processing Operator: {op}")

    if op == 'START':
        if latest_filename:
            mr.startPrint(latest_filename)
            Log("Action", f"Starting file: {latest_filename}")
        else:
            Log("Error", "No file ready to print.")

    elif op == 'PAUSE':
        mr.sendGcode("PAUSE")
        Log("Action", "Paused Print")

    elif op == 'FINISH':
        mr.stopPrint()
        Log("Action", "Canceled/Finished Print")


# ===============================
# FILE DOWNLOAD (MAIN)
# ===============================
def downloadFile(data):
    global latest_filename, is_downloading

    if is_downloading:
        Log("Warning", "Download already in progress.")
        return

    filepath = data.get("filepath")
    if not filepath:
        Log("Error", "Filepath not found")
        return

    is_downloading = True

    # -------------------------------
    # 1) 절대 URL인지 확인 (핵심 FIX)
    # -------------------------------
    if filepath.startswith("http://") or filepath.startswith("https://"):
        file_url = filepath
    else:
        base = env.SERVER_URL.rstrip('/')
        endpoint = filepath.replace("\\", "/").lstrip('/')
        file_url = f"{base}/{endpoint}"

    filename = os.path.basename(filepath)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(current_dir, "downloads")
    save_path = os.path.join(save_dir, filename)
    os.makedirs(save_dir, exist_ok=True)

    try:
        Log("Download", f"Requesting: {file_url}")

        response = requests.get(file_url, timeout=30)

        if response.status_code != 200:
            Log("DownloadError", f"Request failed: {response.status_code}")
            return

        final_content = None

        # -------------------------------
        # 2) JSON인지 판별 (서버에서 링크 제공시)
        # -------------------------------
        try:
            json_data = response.json()

            if isinstance(json_data, dict) and "result" in json_data and "filePath" in json_data["result"]:
                real_url = json_data["result"]["filePath"]
                Log("Download", f"Redirect URL: {real_url}")

                # Google Drive 링크면 전용 다운로더 사용
                if "drive.google.com" in real_url:
                    saved = download_from_google_drive(real_url, save_path)
                    if not saved:
                        Log("DownloadError", "Google Drive download failed")
                        return
                else:
                    r2 = requests.get(real_url, allow_redirects=True, timeout=60)
                    if r2.status_code == 200:
                        final_content = r2.content
                    else:
                        Log("DownloadError", f"Real download failed: {r2.status_code}")
                        return

        except ValueError:
            # JSON이 아니면 바로 파일
            final_content = response.content

        # -------------------------------
        # 3) 파일 저장
        # -------------------------------
        if final_content:
            with open(save_path, "wb") as f:
                f.write(final_content)
            Log("Download", f"Saved ({len(final_content)} bytes)")

        # -------------------------------
        # 4) Moonraker 업로드
        # -------------------------------
        uploaded_name = mr.uploadFile(save_path)
        if uploaded_name:
            latest_filename = uploaded_name
            Log("Ready", f"Standby for print: {latest_filename}")

    except Exception as e:
        Log("Exception", f"Download failed: {e}")

    finally:
        is_downloading = False


# ===============================
# GCODE PASS-THROUGH
# ===============================
def handleTunnel(data):
    cmd = None
    if isinstance(data, str):
        cmd = data
    elif isinstance(data, dict):
        cmd = data.get("script") or data.get("cmd")

    if cmd:
        mr.sendGcode(cmd)
        Log("Tunnel", f"Sent: {cmd}")
    else:
        Log("TunnelError", "Invalid data")

