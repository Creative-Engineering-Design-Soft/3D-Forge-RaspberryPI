import time
import os
from config import Config
from web_api import WebAPI
from printer import Printer
from sensor import get_sensor_data
from utils import ensure_dir

def main():
    cfg = Config()

    api = WebAPI(
        cfg.get("api_base_url"),
        cfg.get("auth")
    )

    printer = Printer(cfg.get("moonraker_url"))
    device_id = cfg.get("device_id")
    gcode_dir = cfg.get("gcode_save_dir")
    poll_interval = cfg.get("poll_interval_seconds", 5)
    report_interval = cfg.get("report_interval_seconds", 10)

    ensure_dir(gcode_dir)

    last_report = 0

    print("Print Agent Started. Polling...")

    while True:
        # 1. 폴링
        job = api.get_next_job(device_id)
        if job:
            print(f"Job detected: {job['id']}")

            filename = f"{job['id']}.gcode"
            save_path = os.path.join(gcode_dir, filename)

            # G-code 다운로드
            api.download_file(job["filePath"], save_path)
            print("Downloaded:", save_path)

            # 업로드
            if printer.upload_gcode(save_path):
                print("Uploaded to Klipper.")

                # 출력 시작
                if printer.start_print(filename):
                    print("Print started.")

        # 2. 장치 상태 보고
        if time.time() - last_report >= report_interval:
            device_report = {
                "device": device_id,
                "sensors": get_sensor_data(),
                "status": "online"
            }
            api.report_status(device_id, device_report)
            last_report = time.time()

        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
