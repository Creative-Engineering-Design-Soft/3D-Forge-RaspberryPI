import socketio
import time
import handler
import env

sio = socketio.Client()

def Log(title, content):
    print(f"[ {title} ] >> {content}")

# SECTION - Event Handler
@sio.event
def connect():
    Log("EventHandler", "Connected to Web Server!")
    sio.emit("register", {"hardwareId": env.HARDWARE_ID})

@sio.event
def disconnect():
    Log("EventHandler", "Disconnected from Web Server")

# SECTION - Custom Handler
@sio.on("test")
def onTest(data):
    Log("onTest", data)

@sio.on("status")
def onStatus(data):
    # 서버가 'status'를 요청하면 handler에서 현재 상태를 읽어서 응답
    status_data = handler.getStatus(data)
    sio.emit("status", status_data)
    # Log("onStatus", f"Sent: {status_data.get('state')}")

@sio.on("command")
def onCommand(data):
    # 프린터 일시정지, 취소 등의 명령이 오면 여기에 handler 함수 추가 가능
    Log("onCommand", f"Received: {data}")
    
@sio.on("upload")
def onUpload(data):
    # data 예시: { "filepath": "/uploads/model.gcode" }
    Log("onUpload", "Request received")
    handler.downloadFile(data)
    
# SECTION - Main
if __name__ == "__main__":
    Log("Init", f"ServerURL='{env.SERVER_URL}'")
    Log("Init", f"HardwareID='{env.HARDWARE_ID}'")

    while True: # 자동 재연결 루프
        try:
            if not sio.connected:
                sio.connect(env.SERVER_URL, transports=['websocket'])
                sio.wait()
        except Exception as e:
            Log("Connection", f"Reconnecting in 3 sec... ({e})")
            time.sleep(3)