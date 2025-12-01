import env
import requests
import os
import klipper_handler as mr

# ===============================
#  설정 및 전역 변수
# ===============================
OPERATOR = ['START', 'PAUSE', 'FINISH']

# 가장 최근에 다운로드(업로드)된 파일명을 기억하는 변수
latest_filename = None 

# 다운로드 중인지 확인하는 깃발 변수
is_downloading = False  

def Log(title, content):
    print(f"[ {title} ] >> {content}")


# ===============================
#  SECTION 1 - 상태 요청 처리
# ===============================
def getStatus(data):
    printer_status = mr.getPrinterStatus()
    return {
        "hardwareId": env.HARDWARE_ID,
        "bedTemp": printer_status["bedTemp"],
        "nozzleTemp": printer_status["nozzleTemp"],
        "isPrinting": printer_status["isPrinting"],
        "isConnected": printer_status["isConnected"],
        "x": printer_status["x"],
        "y": printer_status["y"],
        "z": printer_status["z"]
    }


# ===============================
#  SECTION 2 - 명령어 실행 (로직 수정됨)
# ===============================
def executeCommand(data):
    global latest_filename
    
    # 1. 데이터에서 operator 꺼내기
    raw_op = data.get("operator") # 예: "start", "START", "pause" ...
    if not raw_op:
        Log("CommandError", "No operator provided")
        return

    # 2. 대소문자 무시를 위해 대문자로 변환
    op = raw_op.upper()

    # 3. 유효한 명령어인지 리스트(OPERATOR)에서 확인
    if op not in OPERATOR:
        Log("CommandError", f"Unknown operator: {raw_op}")
        return

    Log("Command", f"Processing Operator: {op}")

    # --- [START] 시작 / 재개 ---
    if op == 'START':
        # 현재 프린터 상태 확인 (일시정지 중이면 RESUME, 아니면 파일 시작)
        status = mr.getPrinterStatus()
        
        # (주의: getPrinterStatus에 'state' 키가 없다면 klipper_handler 수정 필요. 
        #  보통 출력중이면 isPrinting=1 이므로 그것으로 판단 가능하나, 
        #  정확한 PAUSE 구분을 위해선 Moonraker state를 가져오는 게 좋음.
        #  일단은 "출력중이 아닐 때만 시작"하는 로직으로 구현합니다.)

        if latest_filename:
            mr.startPrint(latest_filename)
            Log("Action", f"Starting file: {latest_filename}")
        else:
            Log("Error", "No file ready to print. Please upload first.")

    # --- [PAUSE] 일시정지 ---
    elif op == 'PAUSE':
        mr.sendGcode("PAUSE")
        Log("Action", "Paused Print")

    # --- [FINISH] 강제 종료 (취소) ---
    elif op == 'FINISH':
        mr.stopPrint()
        Log("Action", "Canceled/Finished Print")


# ===============================
#  SECTION 3 - 파일 다운로드 (업로드만 함)
# ===============================
def downloadFile(data):
    global latest_filename 
    global is_downloading  # 전역 변수 사용

    # 1. [안전장치] 이미 누군가 다운로드 중이라면? -> 즉시 종료
    if is_downloading:
        Log("Warning", "Download already in progress. Request ignored.")
        return

    filepath = data.get("filepath")
    if not filepath:
        Log("Error", "Filepath not found")
        return

    # 2. 다운로드 시작 표시 (팻말 걸기)
    is_downloading = True 

    # URL 및 경로 설정 (기존과 동일)
    base_url = env.SERVER_URL.rstrip('/')
    endpoint = filepath.replace("\\", "/").lstrip('/')
    file_url = f"{base_url}/{endpoint}"
    
    filename = os.path.basename(filepath)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(current_dir, "downloads")
    save_path = os.path.join(save_dir, filename)
    os.makedirs(save_dir, exist_ok=True)

    try:
        Log("Download", f"Start downloading: {filename}")
        
        # 3. [안전장치] timeout=30 추가
        # 30초 동안 응답 없으면 에러 내고 강제 종료 (좀비 방지)
        response = requests.get(file_url, timeout=30) 
        
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            Log("Download", "Download Completed")

            uploaded_name = mr.uploadFile(save_path)
            if uploaded_name:
                latest_filename = uploaded_name
                Log("Ready", f"Standby for print: {latest_filename}")
        else:
            Log("DownloadError", f"Status Code: {response.status_code}")

    except Exception as e:
        Log("Exception", f"Download failed: {e}")

    finally:
        # 4. [필수] 작업이 성공하든 실패하든 무조건 팻말 내리기
        is_downloading = False