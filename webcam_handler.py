import cv2
import time
import base64
import threading
import env

class WebcamStreamer:
    def __init__(self, sio_instance):
        self.sio = sio_instance
        self.url = "http://127.0.0.1:8080/?action=stream"
        self.is_running = False
        self.thread = None

    def start(self):
        """스트리밍 스레드 시작"""
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._stream_loop)
        self.thread.daemon = True  # 메인 프로그램 종료 시 같이 종료됨
        self.thread.start()
        print("[ Webcam ] >> Streaming Thread Started")

    def stop(self):
        """스트리밍 중지"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        print("[ Webcam ] >> Streaming Thread Stopped")

    def _stream_loop(self):
        """실제 영상을 캡처해서 소켓으로 보내는 루프"""
        cap = cv2.VideoCapture(self.url)
        
        # 연결 실패 시 재시도 로직
        if not cap.isOpened():
            print("[ WebcamError ] >> Cannot open stream. Retrying in 5s...")
            time.sleep(5)
            self.is_running = False # 루프 종료 후 재시작 유도 (또는 여기서 재귀)
            return

        while self.is_running:
            try:
                ret, frame = cap.read()
                if not ret:
                    print("[ Webcam ] >> Read error. Reconnecting...")
                    cap.release()
                    time.sleep(2)
                    cap = cv2.VideoCapture(self.url)
                    continue

                # 1. 이미지 리사이징 (전송량 최적화: 640x480 or 480x320)
                # frame = cv2.resize(frame, (640, 480))

                # 2. JPG 인코딩 (화질 70% 설정)
                _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                
                # 3. Base64 인코딩 (웹에서 바로 보여주기 위함)
                # bytes로 보내고 싶다면 b64encode 부분을 빼고 buffer.tobytes()만 쓰면 됩니다.
                b64_image = base64.b64encode(buffer).decode('utf-8')

                # 4. 소켓 전송 (이벤트명: 'stream')
                # 하드웨어 ID를 같이 보낼 수도 있고, 데이터만 보낼 수도 있음
                if self.sio.connected:
                    self.sio.emit('stream', {
                        "hardwareId": env.HARDWARE_ID,
                        "image": b64_image
                    })
                
                # 5. 프레임 제한 (약 15fps = 0.066s, 10fps = 0.1s)
                # 서버 부하를 줄이기 위해 sleep 필수
                time.sleep(0.1) 

            except Exception as e:
                print(f"[ WebcamError ] >> {e}")
                time.sleep(1)

        cap.release()