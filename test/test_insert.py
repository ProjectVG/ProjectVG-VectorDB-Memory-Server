import requests

def test_insert():
    """삽입 테스트"""
    print("[삽입 API 테스트]")
    url = "http://localhost:5001/insert"
    data = {
        "text": "CLI 테스트 문장입니다.",
        "metadata": {"test": "cli", "source": "test_script"}
    }
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print("O 삽입 성공" if response.status_code == 200 else "X 삽입 실패")
        return response.status_code == 200
    except Exception as e:
        print(f"X 에러: {e}")
        return False

if __name__ == "__main__":
    test_insert() 