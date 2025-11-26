import requests

class WebAPI:
    def __init__(self, base_url, auth=None):
        self.base = base_url.rstrip('/')
        self.auth = auth or {}

    def _build_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.auth.get("token"):
            headers["Authorization"] = f"Bearer {self.auth['token']}"
        return headers

    def get_next_job(self, device_id):
        url = f"{self.base}/jobs/next?device={device_id}"
        res = requests.get(url, headers=self._build_headers())
        if res.status_code != 200:
            return None
        return res.json().get("result")

    def download_file(self, url, save_path):
        res = requests.get(url, stream=True)
        if res.status_code != 200:
            raise Exception("File download failed: " + url)

        with open(save_path, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)

        return save_path

    def report_status(self, device_id, data):
        url = f"{self.base}/devices/{device_id}/report"
        res = requests.post(url, json=data, headers=self._build_headers())
        return res.status_code == 200
