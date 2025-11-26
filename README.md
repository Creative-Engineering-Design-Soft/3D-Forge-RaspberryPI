# 창의적공학설계 - 3차원 대장간 - 라즈베리파이 임베디드

# Raspberry Pi Klipper Print Agent

이 프로그램은 외부 웹 서버와 주기적으로 HTTP 통신을 수행하여  
새로운 출력 작업을 감지하고, G-code를 다운로드하여 Klipper(Moonraker)로 전송해 출력합니다.  
또한 라즈베리파이의 장치 정보를 서버로 보고하는 기능까지 확장할 수 있도록 설계되었습니다.

---

# 📁 프로젝트 구조

project/
├── main.py # 전체 실행 루프 및 폴링 관리
├── config.py # config.json 로딩 및 설정 객체 제공
├── web_api.py # 외부 웹 서버와 HTTP API 통신 처리
├── printer.py # Moonraker(Klipper)와 통신
├── sensor.py # 온습도/카메라 등 확장 센서 처리 (기본은 빈 구조)
├── utils.py # 공용 기능
├── config.json # 설정 파일
└── README.md # 설명 문서


{
  "api_base_url": "http://your-web-server:3000",
  "poll_interval_seconds": 5,
  "moonraker_url": "http://127.0.0.1:7125",
  "gcode_save_dir": "/home/pi/printer_data/gcodes",
  "report_interval_seconds": 10,
  "device_id": "raspi-001",
  "auth": {
    "token": "",
    "username": "",
    "password": ""
  }
}

🔍 필드 설명

항목	설명

api_base_url	외부 웹 API 서버 주소

poll_interval_seconds	작업을 확인하는 주기(초)

moonraker_url	Klipper Moonraker API 주소

gcode_save_dir	G-code 다운로드 저장 경로

report_interval_seconds	장치 상태 보고 주기

device_id	서버에서 해당 장치를 식별하는 ID

auth.token	Bearer Token 인증용

auth.username/password	Basic Auth가 필요한 경우 사용






# Raspberry Pi Print Agent - 설치 및 임베디드 설정

## 라즈베리파이에 필요한 설치

1. 시스템 업데이트
sudo apt update
sudo apt upgrade -y

sudo apt install python3 python3-pip -y
pip3 install requests
mkdir -p /home/pi/print-agent
# 여기로 코드와 config.json 복사

## 임베디드 실행 설정
sudo nano /etc/systemd/system/print-agent.service

### 다음 내용 입력
[Unit]
Description=Raspberry Pi Print Agent
After=network-online.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/print-agent/main.py
WorkingDirectory=/home/pi/print-agent
Restart=always
User=pi

[Install]
WantedBy=multi-user.target


### 활성화
sudo systemctl daemon-reload
sudo systemctl enable print-agent
sudo systemctl start print-agent


### 상태 확인
sudo systemctl status print-agent

### 재시작
udo systemctl restart print-agent
