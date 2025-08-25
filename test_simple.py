import requests
import json

def test_search():
    """검색 테스트"""
    print("[검색 API 테스트]")
    url = "http://localhost:5602/search"
    data = {
        "query": "테스트",
        "top_k": 5
    }
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print("O 검색 성공" if response.status_code == 200 else "X 검색 실패")
        return response.status_code == 200
    except Exception as e:
        print(f"X 에러: {e}")
        return False

if __name__ == "__main__":
    test_search() 