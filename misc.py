from datetime import datetime

def cur_time_hours():
    cur_time = datetime.utcnow()
    return cur_time.replace(minute=0, second=0, microsecond=0)
