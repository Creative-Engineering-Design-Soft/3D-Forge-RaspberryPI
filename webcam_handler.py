import cv2
import time
import base64
import threading
import env

class WebcamStreamer:
    def __init__(self, sio_instance):
        self.sio = sio_instance
        # 로컬 스트리밍 주소 (Crowsnest 기본값)
        self.url = "http://127.0.0.1:8080/?action=stream"
        
        self.is_running = False
        self.thread = None

    def start(self):
        """스트리밍 시작"""
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._stream_loop)
        self.thread.daemon = True  # 메인 앱 종료 시 같이 종료
        self.thread.start()
        print("[ Webcam ] >> Streaming Thread Started")

    def stop(self):
        """스트리밍 중지"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        print("[ Webcam ] >> Streaming Thread Stopped")

    def _stream_loop(self):
        """영상 캡처 및 소켓 전송 루프"""
        cap = cv2.VideoCapture(self.url)
        
        if not cap.isOpened():
            print("[ WebcamError ] >> Cannot open stream. Retrying in 5s...")
            time.sleep(5)
            self.is_running = False
            return

        while self.is_running:
            try:
                ret, frame = cap.read()

                if not ret:
                    print("[ Webcam ] >> Read error. Reconnecting...")
                    cap.release()
                    time.sleep(3)
                    cap = cv2.VideoCapture(self.url)
                    continue

                # 1. JPG 압축 (Quality: 60)
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
                result, buffer = cv2.imencode('.jpg', frame, encode_param)

                if result:
                    # 2. Base64 변환
                    b64_image = base64.b64encode(buffer).decode('utf-8')

                    # 3. [핵심] 소켓 전송 (이 부분입니다!)
                    if self.sio.connected:
                        self.sio.emit('stream', {
                            "hardwareId": env.HARDWARE_ID,
                            "image": b64_image
                        })
                
                # 전송 부하 조절 (약 10fps)
                time.sleep(0.1) 

            except Exception as e:
                print(f"[ WebcamError ] >> {e}")
                time.sleep(1)

        cap.release()