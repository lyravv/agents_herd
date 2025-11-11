import json
import os

def _safe_json(path):
    try:
        if os.path.exists(path):
            return json.dumps(json.load(open(path, encoding="utf-8")), ensure_ascii=False, indent=2)
    except Exception:
        return None
    return None

def _safe_text(path):
    try:
        if os.path.exists(path):
            return open(path, encoding="utf-8").read()
    except Exception:
        return None
    return None