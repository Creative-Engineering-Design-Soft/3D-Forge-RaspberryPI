import json
import os

class Config:
    def __init__(self, path="config.json"):
        self.path = path
        self.data = None
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Config file not found: {self.path}")

        with open(self.path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def get(self, key, default=None):
        return self.data.get(key, default)
