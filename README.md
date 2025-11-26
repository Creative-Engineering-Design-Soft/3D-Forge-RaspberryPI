🖨️ Klipper - Web Server Bridge Client
이 프로젝트는 라즈베리파이 4(Mainsail OS)에서 동작하는 Python 기반의 미들웨어입니다.

외부 웹 서버와 Socket.IO로 통신하며, 웹의 명령을 받아 로컬 Klipper(Moonraker)를 제어합니다.

---

## 📋 Features

- **🔌 Auto Connection:** 부팅 시 외부 소켓 서버에 자동 접속 및 재연결(Retry) 로직 내장
- **📥 Remote Printing:** 웹에서 전송한 G-code URL을 다운로드 후 Moonraker API로 즉시 업로드 및 출력
- **📡 Real-time Monitoring:** Klipper의 상태(온도, 진행률, 상태값)를 2초 주기로 웹 서버에 전송
- **🧵 Multi-threading:** 소켓 수신 대기(Blocking)와 상태 전송(Non-blocking)을 병렬 처리

---

## 🏗️ System Architecture

```mermaid
graph LR
    Web[External Web Server] -- "Socket.IO (Command)" --> Pi[Bridge Agent (RPi 4)]
    Pi -- "Socket.IO (Status)" --> Web
    Pi -- "HTTP API (Upload/Query)" --> Moon[Moonraker (Locahost:7125)]
    Moon -- "Control" --> Klipper[Klipper Firmware]
```

---

## 🛠️ Installation

### 1. Prerequisites
이 프로젝트는 **Mainsail OS**가 설치된 **Raspberry Pi 4** 환경을 기준으로 합니다.

```bash
# 시스템 패키지 업데이트
sudo apt update
sudo apt install python3-pip -y
```

### 2. Dependencies
**주의:** Socket.IO 서버와의 호환성을 위해 `python-socketio` 클라이언트 **6.0.0** 버전을 사용합니다.

```bash
# Python 라이브러리 설치
pip3 install requests "python-socketio[client]==6.0.0"
```

### 3. Setup Project
```bash
# 프로젝트 디렉토리 생성 및 코드 다운로드
mkdir -p ~/printer_bridge
# (main.py 파일을 해당 폴더에 위치시키세요)
```

---

## ⚙️ Configuration

`main.py` 파일 상단의 설정 변수를 환경에 맞게 수정해야 합니다.

```python
# main.py

# 라즈베리파이 식별 ID (웹 서버 등록용)
HARDWARE_ID = "pi-lab-101"

# 외부 웹 서버 주소 (Socket.IO 서버)
EXTERNAL_SERVER_URL = "http://YOUR_SERVER_IP:3000"

# Moonraker API 주소 (기본값 유지)
MOONRAKER_URL = "http://127.0.0.1:7125"
```

---

## 🚀 Auto-Start (Systemd)

라즈베리파이 전원 인가 시 프로그램이 자동으로 실행되도록 서비스로 등록합니다.

### 1. 서비스 파일 생성
```bash
sudo nano /etc/systemd/system/printer-bridge.service
```

### 2. 서비스 내용 작성
```ini
[Unit]
Description=Klipper to External Web Socket Bridge
After=network-online.target moonraker.service
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/printer_bridge
ExecStart=/usr/bin/python3 /home/pi/printer_bridge/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 3. 활성화 및 시작
```bash
sudo systemctl daemon-reload
sudo systemctl enable printer-bridge.service
sudo systemctl start printer-bridge.service
```

---

## 📡 API Spec (Socket Events)

### 📥 Receive (Web → Pi)

| Event Name | Data Payload | Description |
|:---:|:---|:---|
| `print` | `{ "fileUrl": "http://..." }` | 해당 URL의 G-code를 다운로드 후 출력 시작 |
| `test` | `Any` | 연결 테스트용 이벤트 |

### 📤 Send (Pi → Web)

| Event Name | Data Payload | Frequency |
|:---:|:---|:---|
| `register` | `{ "hardwareId": "..." }` | 소켓 연결 직후 1회 전송 |
| `status_update` | `{ "temp_nozzle": float, "temp_bed": float, "state": string, "progress": float }` | 2초마다 주기적 전송 |

---
