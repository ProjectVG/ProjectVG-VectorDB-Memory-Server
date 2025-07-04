import requests

def test_new_endpoints():
    """새로운 엔드포인트 테스트"""
    print("[새로운 엔드포인트 테스트]")
    # 현재 시간 조회
    try:
        response = requests.get("http://localhost:5001/time")
        if response.status_code == 200:
            time_data = response.json()
            print(f"O 현재 시간: {time_data['current_time']}")
        else:
            print(f"X 시간 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"X 시간 조회 에러: {e}")
    # 통계 조회
    try:
        response = requests.get("http://localhost:5001/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"O 컬렉션 통계: {stats}")
        else:
            print(f"X 통계 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"X 통계 조회 에러: {e}")

if __name__ == "__main__":
    test_new_endpoints() 