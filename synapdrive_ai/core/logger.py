# synapdrive_ai/core/logger.py

import time

class SynapLogger:
    """
    A simple, modular logger for tracking internal system operations
    with timestamps and severity levels.
    """

    def __init__(self):
        self.log_entries = []

    def log(self, message, level="INFO"):
        entry = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            "level": level.upper(),
            "message": message
        }
        self.log_entries.append(entry)
        print(f"[{entry['timestamp']}] [{entry['level']}] {entry['message']}")

    def info(self, message):
        self.log(message, level="INFO")

    def warning(self, message):
        self.log(message, level="WARNING")

    def error(self, message):
        self.log(message, level="ERROR")

    def get_logs(self, level_filter=None):
        if level_filter:
            return [entry for entry in self.log_entries if entry["level"] == level_filter.upper()]
        return self.log_entries

    def clear(self):
        self.log_entries.clear()
