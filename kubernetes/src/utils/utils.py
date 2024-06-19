from datetime import datetime


def datetime_to_str(d: datetime) -> str:
    return d.strftime('%Y-%m-%d %H:%M:%S.%f')
