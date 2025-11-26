🖨️ Klipper - Web Server Bridge Client
이 프로젝트는 라즈베리파이 4(Mainsail OS)에서 동작하는 Python 기반의 미들웨어입니다.

외부 웹 서버와 Socket.IO로 통신하며, 웹의 명령을 받아 로컬 Klipper(Moonraker)를 제어합니다.

📌 환경 (Environment)
H/W: Raspberry Pi 4 Model B

OS: Mainsail OS (based on Raspberry Pi OS Lite)

F/W: Klipper & Moonraker

Language: Python 3.x

🚀 설치 및 설정 (Installation)
1. 시스템 패키지 업데이트 및 Pip 설치
SSH로 라즈베리파이에 접속한 후 다음 명령어를 실행하여 패키지 리스트를 갱신합니다.

Bash

sudo apt update
sudo apt install python3-pip -y
2. Python 필수 라이브러리 설치
Socket.IO 통신과 HTTP 요청(Moonraker API)을 위해 필요한 라이브러리를 설치합니다. (Mainsail OS 가상환경을 건드리지 않기 위해 전역 혹은 사용자 레벨에 설치합니다.)

Bash

# requests: HTTP 요청용
# python-socketio[client]: Socket.IO 클라이언트 (websocket-client 포함) (pip or pip3)
pip install "python-socketio[client]<6.0.0"
3. 프로젝트 파일 생성
홈 디렉토리(~)에 프로젝트 폴더를 만들고 스크립트를 작성합니다.

Bash

mkdir -p ~/printer_bridge
nano ~/printer_bridge/main.py
main.py 파일 내부에 작성된 Python 코드를 붙여넣고 저장합니다 (Ctrl+X, Y, Enter).

주의: 코드 내 EXTERNAL_SERVER_URL과 HARDWARE_ID가 올바르게 설정되었는지 확인하세요.

⚙️ 자동 실행 등록 (Systemd Service)
전원이 켜질 때 프로그램이 자동으로 실행되고, 에러로 종료되더라도 다시 시작되도록 systemd 서비스를 등록합니다.

1. 서비스 파일 생성
Bash

sudo nano /etc/systemd/system/printer-bridge.service
2. 서비스 내용 작성
아래 내용을 복사하여 붙여넣습니다. (사용자명이 pi가 아닌 경우 User 항목 수정 필요)

Ini, TOML

[Unit]
Description=Klipper to External Web Socket Bridge
# 네트워크와 Moonraker가 준비된 후 실행
After=network-online.target moonraker.service
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/printer_bridge
ExecStart=/usr/bin/python3 /home/pi/printer_bridge/main.py
# 프로세스가 죽으면 5초 후 자동 재시작
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
3. 서비스 활성화 및 시작
Bash

# 데몬 리로드 (새로 만든 서비스 인식)
sudo systemctl daemon-reload

# 부팅 시 자동 실행 등록
sudo systemctl enable printer-bridge.service

# 서비스 즉시 시작
sudo systemctl start printer-bridge.service
🛠️ 관리 및 로그 확인 (Management)
프로그램이 정상적으로 돌고 있는지 확인하거나 로그를 볼 때 사용합니다.

상태 확인:

Bash

sudo systemctl status printer-bridge.service
실시간 로그 확인 (디버깅용): Python 코드의 print() 출력 내용을 실시간으로 볼 수 있습니다.

Bash

journalctl -u printer-bridge.service -f
서비스 중지/재시작:

Bash

sudo systemctl stop printer-bridge.service
sudo systemctl restart printer-bridge.service