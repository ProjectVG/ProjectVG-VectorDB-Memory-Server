from datetime import datetime
import math
import re

def parse_iso_time(time_str: str) -> datetime:
    """ISO 형식의 시간 문자열을 datetime 객체로 변환."""
    if time_str.endswith('Z'):
        time_str = time_str[:-1] + '+00:00'
    
    # 마이크로초가 6자리 이상인 경우 처리
    pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d+)([+-]\d{2}:\d{2}|Z?)$'
    match = re.match(pattern, time_str)
    
    if match:
        base_time = match.group(1)
        microseconds = match.group(2)
        timezone = match.group(3)
        
        # 마이크로초를 6자리로 제한
        if len(microseconds) > 6:
            microseconds = microseconds[:6]
        elif len(microseconds) < 6:
            microseconds = microseconds.ljust(6, '0')
        
        # Z를 +00:00으로 변환
        if timezone == 'Z':
            timezone = '+00:00'
        
        formatted_time = f"{base_time}.{microseconds}{timezone}"
        return datetime.fromisoformat(formatted_time)
    
    return datetime.fromisoformat(time_str)

def calculate_time_weight(insert_time: datetime, reference_time: datetime, time_weight: float) -> float:
    """시간 가중치 계산."""
    if time_weight == 0.0:
        return 1.0
    time_diff = abs((reference_time - insert_time).total_seconds() / 86400)
    decay_factor = math.exp(-time_diff * time_weight)
    return decay_factor 