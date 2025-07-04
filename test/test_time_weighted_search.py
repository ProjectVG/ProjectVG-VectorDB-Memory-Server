import requests

def test_time_weighted_search():
    """시간 가중치 검색 테스트"""
    print("[시간 가중치 검색 테스트]")
    url = "http://localhost:5001/search"
    time_weights = [0.0, 0.3, 0.7, 1.0]
    for weight in time_weights:
        print(f"\n--- 시간 가중치: {weight} ---")
        data = {
            "query": "시간 테스트",
            "top_k": 3,
            "time_weight": weight
        }
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                results = response.json()
                print(f"O 검색 결과 ({len(results)}개):")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result['text']}")
                    print(f"     유사도: {result['similarity_score']:.4f}")
                    print(f"     시간가중치: {result['time_weight']:.4f}")
                    print(f"     최종점수: {result['final_score']:.4f}")
                    print(f"     시간: {result['timestamp']}")
            else:
                print(f"X 검색 실패: {response.status_code}")
        except Exception as e:
            print(f"X 검색 에러: {e}")

if __name__ == "__main__":
    test_time_weighted_search() 