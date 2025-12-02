import socketio
import time
import threading
import handler, env
# [필수] 같은 폴더에 webcam_handler.py가 있어야 합니다.
from webcam_handler import WebcamStreamer

# 로거 정의
def Log(title, content):
    print(f"[ {title} ] >> {content}")

sio = socketio.Client()

# [추가] 웹캠 스트리머 인스턴스 생성 (sio 객체를 넘겨줍니다)
streamer = WebcamStreamer(sio)

# [추가] 다운로드 스레드를 관리할 전역 변수
download_thread = None

# ===============================
# SECTION - Event Handler (접속 관련)
# ===============================
@sio.event
def connect():
    Log("Socket", "Connected to Server!")
    sio.emit("register", {"hardwareId": env.HARDWARE_ID})
    
    # [추가] 서버에 연결되면 웹캠 스트리밍 스레드도 시작합니다.
    streamer.start()

@sio.event
def disconnect():
    Log("Socket", "Disconnected from Server")
    
    # [추가] 서버와 연결이 끊기면 웹캠 스레드도 멈춥니다. (CPU/네트워크 절약)
    streamer.stop()

@sio.event
def connect_error(data):
    Log("SocketError", f"Connection Error: {data}")


# ===============================
# SECTION - Custom Handler (기능 관련)
# ===============================

@sio.on("test")
def onTest(data):
    Log("onTest", data)

@sio.on("status")
def onStatus(data):
    # 상태 요청이 오면 즉시 응답
    sio.emit("status", handler.getStatus(data))

@sio.on("operate")
def onOperate(data):
    Log("onOperate", f"Received: {data}")
    # handler.py의 executeCommand 함수가 'START', 'PAUSE', 'FINISH'를 처리함
    handler.executeCommand(data)
    
    
@sio.on("upload")
def onUpload(data):
    global download_thread
    Log("onUpload", "Request received")

    # 1. [안전장치] 이미 다운로드 중인 스레드가 살아있다면 요청 무시
    if download_thread and download_thread.is_alive():
        Log("Warning", "Download is already in progress! Request ignored.")
        return

    Log("onUpload", "Starting background download...")

    # 2. 스레드 생성 및 실행
    download_thread = threading.Thread(target=handler.downloadFile, args=(data,))
    
    # [중요] 데몬 스레드 설정: 메인 프로그램(app.py)이 꺼지면 다운로드도 강제 종료됨 (좀비 방지)
    download_thread.daemon = True 
    
    download_thread.start()


# ===============================
# SECTION - Main Loop
# ===============================
if __name__ == "__main__":
    Log("Init", f"ServerURL: {env.SERVER_URL}")
    Log("Init", f"HardwareID: {env.HARDWARE_ID}")

    while True:
        try:
            if not sio.connected:
                sio.connect(env.SERVER_URL, transports=['websocket'])
                sio.wait() # 연결 유지 (끊어지면 아래 코드로 넘어감)
        except Exception as e:
            Log("Retry", f"Connection failed: {e}")
            
            # [추가] 예기치 않게 연결 루프가 깨졌을 때도 웹캠을 확실히 끕니다.
            streamer.stop()
            
            time.sleep(5) # 5초 후 재시도