import socketio
import time
import threading
import handler, env

# 로거 정의
def Log(title, content):
    print(f"[ {title} ] >> {content}")

sio = socketio.Client()

# ===============================
# SECTION - Event Handler (접속 관련)
# ===============================
@sio.event
def connect():
    Log("Socket", "Connected to Server!")
    sio.emit("register", {"hardwareId": env.HARDWARE_ID})

@sio.event
def disconnect():
    Log("Socket", "Disconnected from Server")

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

# [확인됨] 기존 'command'가 'operate'로 변경됨
@sio.on("operate")
def onOperate(data):
    Log("onOperate", f"Received: {data}")
    # handler.py의 executeCommand 함수가 'START', 'PAUSE', 'FINISH'를 처리함
    handler.executeCommand(data)
    
    
    
@sio.on("upload")
def onUpload(data):
    Log("onUpload", "Background download started")
    # 스레드로 실행하여 소켓 연결 끊김 방지
    # TODO: Thread 중복 생성 확인
    t = threading.Thread(target=handler.downloadFile, args=(data,))
    t.start()
    


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
                sio.wait() # 연결 유지 (끊어지면 리턴됨)
        except Exception as e:
            Log("Retry", f"Connection failed: {e}")
            time.sleep(5) # 5초 후 재시도