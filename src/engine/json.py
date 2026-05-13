import json


class JsonFile:
    @staticmethod
    def read(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                return data
        except FileNotFoundError:
            msg = "File not found"
        except json.JSONDecodeError as e:
            msg = "Invalid JSON:", e

        return None

    @staticmethod
    def write(path, data):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except FileNotFoundError:
            msg = "File not found"
        except json.JSONDecodeError as e:
            msg = "Invalid JSON:", e
