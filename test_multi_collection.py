#!/usr/bin/env python3
"""
다중 컬렉션 Memory Server API 테스트
"""

import requests
import json
import time
from datetime import datetime, timezone

# 서버 설정
BASE_URL = "http://localhost:5602"
USER_ID = "test_user_001"

def test_auto_classification():
    """자동 분류 테스트"""
    print("\n=== 자동 분류 테스트 ===")
    
    test_cases = [
        # Episodic 메모리 테스트
        {
            "text": "오늘 아침에 커피를 마시면서 기분이 좋았어",
            "speaker": "user",
            "emotion": {
                "valence": "positive",
                "arousal": "medium",
                "labels": ["기쁨", "만족"],
                "intensity": 0.7
            },
            "context": {
                "location": "home",
                "time": "morning"
            },
            "expected_type": "episodic"
        },
        {
            "text": "어제 친구랑 영화를 보러 갔는데 너무 재밌었다",
            "speaker": "user", 
            "emotion": {
                "valence": "positive",
                "arousal": "high",
                "labels": ["즐거움", "흥미"],
                "intensity": 0.8
            },
            "expected_type": "episodic"
        },
        # Semantic 메모리 테스트
        {
            "text": "아빠의 생일은 3월 21일이다",
            "fact_type": "personal_fact",
            "expected_type": "semantic"
        },
        {
            "text": "파이썬은 객체지향 프로그래밍 언어입니다",
            "fact_type": "world_fact",
            "expected_type": "semantic"
        },
        {
            "text": "나는 커피보다 녹차를 더 좋아한다",
            "fact_type": "personal_fact",
            "expected_type": "semantic"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n테스트 {i+1}: {test_case['text']}")
        
        # 자동 분류로 메모리 삽입
        insert_data = {
            "text": test_case["text"],
            "user_id": USER_ID,
            "importance_score": 0.7,
            "source": "test_auto_classification"
        }
        
        # 타입별 특화 데이터 추가
        if "speaker" in test_case:
            insert_data["speaker"] = test_case["speaker"]
        if "emotion" in test_case:
            insert_data["emotion"] = test_case["emotion"]
        if "context" in test_case:
            insert_data["context"] = test_case["context"]
        if "fact_type" in test_case:
            insert_data["fact_type"] = test_case["fact_type"]
            
        response = requests.post(f"{BASE_URL}/api/memory", json=insert_data)
        
        if response.status_code == 200:
            result = response.json()
            predicted_type = result["memory_type"]
            confidence = result.get("classification_confidence", 0)
            explanation = result.get("classification_explanation", "")
            
            print(f"   예상: {test_case['expected_type']}")
            print(f"   예측: {predicted_type} (신뢰도: {confidence:.2f})")
            print(f"   설명: {explanation}")
            print(f"   ID: {result['id']}")
            
            if predicted_type == test_case["expected_type"]:
                print("   ✅ 분류 성공!")
            else:
                print("   ❌ 분류 실패")
        else:
            print(f"   오류: {response.status_code} - {response.text}")

def test_manual_classification():
    """수동 분류 테스트"""
    print("\n=== 수동 분류 테스트 ===")
    
    # Episodic 메모리 직접 삽입
    episodic_data = {
        "text": "방금 전에 비가 오기 시작했어",
        "user_id": USER_ID,
        "speaker": "user",
        "emotion": {
            "valence": "neutral",
            "arousal": "low",
            "labels": ["평온"],
            "intensity": 0.3
        },
        "context": {
            "location": "office",
            "weather": "rainy",
            "conversation_id": "conv_test_001"
        },
        "importance_score": 0.5,
        "source": "test_manual"
    }
    
    response = requests.post(f"{BASE_URL}/api/memory/episodic", json=episodic_data)
    if response.status_code == 200:
        result = response.json()
        print(f"Episodic 메모리 삽입 성공: {result['id']}")
    else:
        print(f"Episodic 메모리 삽입 실패: {response.status_code}")
    
    # Semantic 메모리 직접 삽입
    semantic_data = {
        "text": "우리 회사 주소는 서울시 강남구 테헤란로 123번길이다",
        "user_id": USER_ID,
        "fact_type": "personal_fact",
        "confidence_score": 1.0,
        "importance_score": 0.8,
        "source": "test_manual"
    }
    
    response = requests.post(f"{BASE_URL}/api/memory/semantic", json=semantic_data)
    if response.status_code == 200:
        result = response.json()
        print(f"Semantic 메모리 삽입 성공: {result['id']}")
    else:
        print(f"Semantic 메모리 삽입 실패: {response.status_code}")

def test_search():
    """검색 테스트"""
    print("\n=== 검색 테스트 ===")
    
    test_queries = [
        "커피",
        "생일",
        "파이썬",
        "영화",
        "비"
    ]
    
    for query in test_queries:
        print(f"\n쿼리: '{query}'")
        
        # 단일 컬렉션 검색 (Episodic)
        headers = {"X-User-ID": USER_ID}
        params = {"query": query, "limit": 3}
        
        response = requests.get(f"{BASE_URL}/api/memory/episodic/search", 
                               headers=headers, params=params)
        if response.status_code == 200:
            results = response.json()
            print(f"   Episodic 검색 결과: {len(results)}개")
            for i, result in enumerate(results):
                print(f"     {i+1}. {result['text'][:50]}... (점수: {result['score']:.3f})")
        
        # 단일 컬렉션 검색 (Semantic)  
        response = requests.get(f"{BASE_URL}/api/memory/semantic/search", 
                               headers=headers, params=params)
        if response.status_code == 200:
            results = response.json()
            print(f"   Semantic 검색 결과: {len(results)}개")
            for i, result in enumerate(results):
                print(f"     {i+1}. {result['text'][:50]}... (점수: {result['score']:.3f})")
        
        # 다중 컬렉션 통합 검색
        params.update({
            "episodic_weight": 1.0,
            "semantic_weight": 1.0
        })
        
        response = requests.get(f"{BASE_URL}/api/memory/search/multi", 
                               headers=headers, params=params)
        if response.status_code == 200:
            result = response.json()
            print(f"   통합 검색 결과: {result['total_results']}개")
            print(f"   컬렉션별 분포: {result['collection_stats']}")
            print(f"   검색 시간: {result['query_time_ms']:.1f}ms")
            
            for i, item in enumerate(result['results'][:3]):
                print(f"     {i+1}. [{item['memory_type']}] {item['text'][:40]}... (점수: {item['score']:.3f})")

def test_classification_api():
    """분류 API 테스트"""
    print("\n=== 분류 API 테스트 ===")
    
    test_texts = [
        "오늘 점심에 김치찌개를 먹었어",
        "파리는 프랑스의 수도이다", 
        "어제 친구와 통화했는데 기분이 좋아졌어",
        "내 취미는 독서와 영화감상이다"
    ]
    
    for text in test_texts:
        response = requests.post(f"{BASE_URL}/api/classify", 
                                params={"text": text})
        if response.status_code == 200:
            result = response.json()
            print(f"\n텍스트: {text}")
            print(f"분류: {result['predicted_type']} (신뢰도: {result['confidence']:.2f})")
            print(f"점수 - Episodic: {result['episodic_score']}, Semantic: {result['semantic_score']}")
            print(f"설명: {result['explanation']}")

def test_user_stats():
    """사용자 통계 테스트"""
    print("\n=== 사용자 통계 테스트 ===")
    
    response = requests.get(f"{BASE_URL}/api/user/{USER_ID}/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"사용자: {stats['user_id']}")
        print(f"전체 메모리 수: {stats['total_memories']}")
        print(f"Episodic 메모리: {stats['episodic_count']}")
        print(f"Semantic 메모리: {stats['semantic_count']}")
    else:
        print(f"통계 조회 실패: {response.status_code}")

def test_system_stats():
    """시스템 통계 테스트"""
    print("\n=== 시스템 통계 테스트 ===")
    
    response = requests.get(f"{BASE_URL}/api/system/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"전체 컬렉션: {stats['total_collections']}")
        print(f"전체 사용자: {stats['total_users']}")
        print(f"전체 메모리: {stats['total_memories']}")
        print(f"평균 쿼리 시간: {stats['avg_query_time_ms']:.1f}ms")
    else:
        print(f"시스템 통계 조회 실패: {response.status_code}")

def main():
    print("=== 다중 컬렉션 Memory Server API 테스트 시작 ===")
    print(f"서버 URL: {BASE_URL}")
    print(f"테스트 사용자: {USER_ID}")
    
    try:
        # 서버 연결 확인
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
            return
        
        print("✅ 서버 연결 확인")
        
        # 테스트 실행
        test_auto_classification()
        test_manual_classification()
        test_search()
        test_classification_api()
        test_user_stats()
        test_system_stats()
        
        print("\n=== 테스트 완료 ===")
        
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()