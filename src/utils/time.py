from datetime import datetime
import math

def parse_iso_time(time_str: str) -> datetime:
    """ISO 형식의 시간 문자열을 datetime 객체로 변환."""
    if time_str.endswith('Z'):
        time_str = time_str[:-1] + '+00:00'
    return datetime.fromisoformat(time_str)

def calculate_time_weight(insert_time: datetime, reference_time: datetime, time_weight: float) -> float:
    """시간 가중치 계산."""
    if time_weight == 0.0:
        return 1.0
    time_diff = abs((reference_time - insert_time).total_seconds() / 86400)
    decay_factor = math.exp(-time_diff * time_weight)
    return decay_factor 