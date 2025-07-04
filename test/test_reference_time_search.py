import requests
from datetime import datetime, timezone, timedelta

def test_reference_time_search():
    """기준 시간 기반 검색 테스트"""
    print("[기준 시간 기반 검색 테스트]")
    url = "http://localhost:5001/search"
    past_reference = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    data = {
        "query": "시간 테스트",
        "top_k": 3,
        "time_weight": 0.5,
        "reference_time": past_reference
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            results = response.json()
            print(f"O 기준 시간: {past_reference}")
            print(f"O 검색 결과 ({len(results)}개):")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['text']}")
                print(f"     최종점수: {result['final_score']:.4f}")
                print(f"     시간: {result['timestamp']}")
        else:
            print(f"X 검색 실패: {response.status_code}")
    except Exception as e:
        print(f"X 검색 에러: {e}")

if __name__ == "__main__":
    test_reference_time_search() 