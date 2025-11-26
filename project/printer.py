import requests
import os

class Printer:
    def __init__(self, url):
        self.url = url.rstrip('/')

    def upload_gcode(self, file_path):
        url = f"{self.url}/server/files/upload"
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/octet-stream")}
            res = requests.post(url, files=files)
        return res.status_code == 200

    def start_print(self, filename):
        url = f"{self.url}/printer/print/start?filename={filename}"
        res = requests.post(url)
        return res.status_code == 200
