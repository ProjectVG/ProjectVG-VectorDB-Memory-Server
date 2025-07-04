import requests

def insert_from_txt_file(txt_path):
    """외부 txt 파일의 각 줄을 메모리로 삽입"""
    print(f"[TXT 파일 삽입 테스트] 파일: {txt_path}")
    url = "http://localhost:5001/insert"
    success_count = 0
    total = 0
    try:
        with open(txt_path, encoding="utf-8") as f:
            for line in f:
                text = line.strip()
                if not text:
                    continue
                total += 1
                data = {"text": text, "metadata": {"source": "txt_file", "line": total}}
                try:
                    response = requests.post(url, json=data)
                    if response.status_code == 200:
                        success_count += 1
                        print(f"O {total}번 삽입 성공: {text[:30]}{'...' if len(text) > 30 else ''}")
                    else:
                        print(f"X {total}번 삽입 실패: {response.status_code}")
                except Exception as e:
                    print(f"X {total}번 삽입 에러: {e}")
    except FileNotFoundError:
        print(f"X 파일을 찾을 수 없습니다: {txt_path}")
    print(f"\n[TXT 삽입 결과] {success_count}/{total}개 성공")
    return success_count

if __name__ == "__main__":
    insert_from_txt_file("test/data/sample_data.txt") 