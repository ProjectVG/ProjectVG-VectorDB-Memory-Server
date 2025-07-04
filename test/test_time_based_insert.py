import requests
from datetime import datetime, timezone, timedelta

def test_time_based_insert():
    """시간 기반 삽입 테스트"""
    print("[시간 기반 삽입 테스트]")
    url = "http://localhost:5001/insert"
    success_count = 0
    base_time = datetime.now(timezone.utc)
    time_offsets = [
        (-7, "일주일 전"),
        (-3, "3일 전"),
        (-1, "하루 전"),
        (0, "현재"),
        (1, "내일")
    ]
    for days_offset, time_desc in time_offsets:
        timestamp = base_time + timedelta(days=days_offset)
        data = {
            "text": f"시간 테스트 문장 - {time_desc}에 작성된 내용입니다.",
            "metadata": {"category": "time_test", "time_desc": time_desc},
            "timestamp": timestamp.isoformat()
        }
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                success_count += 1
                print(f"O {time_desc} 삽입 성공: {timestamp.isoformat()}")
            else:
                print(f"X {time_desc} 삽입 실패: {response.status_code}")
        except Exception as e:
            print(f"X {time_desc} 삽입 에러: {e}")
    print(f"\n[시간 기반 삽입 결과] {success_count}/{len(time_offsets)}개 성공")
    return success_count

if __name__ == "__main__":
    test_time_based_insert() 