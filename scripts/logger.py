from datetime import datetime

LOG_FILE = '../data/log.txt'

def logger(message: str, type=None) -> None:
    """'type' defaults to message, set to 'a' for alert or 'e' for error"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            if type == 'a':
                f.write(f"[ALERT][{now}]: {message}\n")
            elif type == 'e':
                f.write(f"*[ERROR]*[{now}]: {message}\n")
            else:
                f.write(f"[{now}]: {message}\n")

    except Exception as e:
        print(f"Logging error: {e}")