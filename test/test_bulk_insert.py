import requests

def test_bulk_insert():
    """대량 삽입 테스트"""
    print("[대량 삽입 테스트 (10개)]")
    url = "http://localhost:5001/insert"
    success_count = 0
    for i in range(1, 11):
        data = {
            "text": f"CLI 테스트 문장 {i}번입니다. 이것은 대량 삽입 테스트용입니다.",
            "metadata": {"test": "bulk", "index": i}
        }
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                success_count += 1
                print(f"O {i}번 삽입 성공")
            else:
                print(f"X {i}번 삽입 실패: {response.status_code}")
        except Exception as e:
            print(f"X {i}번 삽입 에러: {e}")
    print(f"\n[대량 삽입 결과] {success_count}/10개 성공")
    return success_count

if __name__ == "__main__":
    test_bulk_insert() 