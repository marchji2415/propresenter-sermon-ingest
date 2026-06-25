def info(message): print(f"[INFO] {message}", flush=True)
def ok(message): print(f"[OK] {message}", flush=True)
def warn(message): print(f"[WARN] {message}", flush=True)
def error(message): print(f"[ERROR] {message}", flush=True)
def debug(message, enabled=False):
    if enabled:
        print(f"[DEBUG] {message}", flush=True)
