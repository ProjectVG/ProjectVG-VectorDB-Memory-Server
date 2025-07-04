import subprocess
import sys

def run_test_script(script_name, desc):
    print("\n" + "="*60)
    print(f"[{desc}] 실행 중...")
    result = subprocess.run([sys.executable, script_name], cwd="test")
    if result.returncode == 0:
        print(f"O {script_name} 실행 완료")
    else:
        print(f"X {script_name} 실행 실패 (코드: {result.returncode})")

def main():
    menu = [
        ("삽입 테스트", "test_insert.py"),
        ("검색 테스트", "test_search.py"),
        ("시간 기반 삽입 테스트", "test_time_based_insert.py"),
        ("시간 가중치 검색 테스트", "test_time_weighted_search.py"),
        ("기준 시간 기반 검색 테스트", "test_reference_time_search.py"),
        ("새로운 엔드포인트 테스트", "test_new_endpoints.py"),
        ("대량 삽입 테스트", "test_bulk_insert.py"),
        ("TXT 파일 삽입 테스트", "test_insert_from_txt_file.py"),
    ]
    print("메모리 서버 전체 테스트 실행")
    print("=" * 60)
    for desc, script in menu:
        run_test_script(script, desc)
    print("\n" + "="*60)
    print("전체 테스트 완료!")

if __name__ == "__main__":
    main() 