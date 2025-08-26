#!/usr/bin/env python3
"""
종합적인 V2 메모리 서버 테스트
계획서 기반으로 모든 기능을 테스트합니다.
"""

import asyncio
import aiohttp
import json
import time
import random
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
import sys

class ComprehensiveMemoryServerTest:
    def __init__(self, base_url: str = "http://localhost:5602"):
        self.base_url = base_url
        self.test_user_id = f"test_user_{int(time.time())}"
        self.session = None
        self.test_results = []
        
    async def create_session(self):
        """HTTP 세션 생성"""
        self.session = aiohttp.ClientSession()
        
    async def close_session(self):
        """HTTP 세션 종료"""
        if self.session:
            await self.session.close()
            
    def log_result(self, test_name: str, success: bool, message: str = "", data: Any = None):
        """테스트 결과 로깅"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {test_name}: {message}")
        if not success and data:
            print(f"   Error details: {data}")
    
    async def test_health_check(self):
        """서버 상태 확인"""
        try:
            async with self.session.get(f"{self.base_url}/api/v1/system/status") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result("Health Check", True, f"Server is healthy: {data.get('status')}")
                    return True
                else:
                    self.log_result("Health Check", False, f"Status code: {response.status}")
                    return False
        except Exception as e:
            self.log_result("Health Check", False, f"Connection error: {str(e)}")
            return False
    
    async def test_episodic_memory_insertion(self):
        """Episodic 메모리 삽입 테스트"""
        test_data = [
            {
                "text": "오늘 친구와 카페에서 커피를 마셨어. 정말 즐거웠다.",
                "speaker": "user",
                "emotion": {
                    "valence": "positive",
                    "arousal": "medium",
                    "labels": ["즐거움", "만족"],
                    "intensity": 0.8
                },
                "context": {
                    "location": "cafe",
                    "activity": "coffee_chat",
                    "companions": ["friend"]
                }
            },
            {
                "text": "어제 영화를 봤는데 너무 무서웠어. 잠을 못 잘 정도였다.",
                "speaker": "user", 
                "emotion": {
                    "valence": "negative",
                    "arousal": "high",
                    "labels": ["무서움", "불안"],
                    "intensity": 0.9
                }
            },
            {
                "text": "방금 엄마한테 전화가 왔어. 고향에서 잘 지내고 계시는 것 같다.",
                "speaker": "user",
                "emotion": {
                    "valence": "positive",
                    "arousal": "low", 
                    "labels": ["그리움", "안도"],
                    "intensity": 0.6
                }
            }
        ]
        
        inserted_ids = []
        for i, data in enumerate(test_data):
            try:
                payload = {
                    "text": data["text"],
                    "user_id": self.test_user_id,
                    "speaker": data["speaker"],
                    "emotion": data["emotion"],
                    "context": data.get("context"),
                    "importance_score": 0.8,
                    "source": "test"
                }
                
                async with self.session.post(
                    f"{self.base_url}/api/memory/episodic",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        inserted_ids.append(result["id"])
                        self.log_result(f"Episodic Insert {i+1}", True, 
                                      f"ID: {result['id']}, Type: {result['memory_type']}")
                    else:
                        error_data = await response.text()
                        self.log_result(f"Episodic Insert {i+1}", False, 
                                      f"Status: {response.status}", error_data)
                        
            except Exception as e:
                self.log_result(f"Episodic Insert {i+1}", False, f"Exception: {str(e)}")
        
        return inserted_ids
    
    async def test_semantic_memory_insertion(self):
        """Semantic 메모리 삽입 테스트"""
        test_data = [
            {
                "text": "내 생일은 1990년 3월 15일이다.",
                "fact_type": "personal_fact",
                "confidence_score": 1.0
            },
            {
                "text": "파리는 프랑스의 수도이다.",
                "fact_type": "world_fact", 
                "confidence_score": 1.0
            },
            {
                "text": "나는 개발자로 일하고 있다.",
                "fact_type": "personal_fact",
                "confidence_score": 0.9
            },
            {
                "text": "Python은 객체지향 프로그래밍 언어다.",
                "fact_type": "world_fact",
                "confidence_score": 1.0
            }
        ]
        
        inserted_ids = []
        for i, data in enumerate(test_data):
            try:
                payload = {
                    "text": data["text"],
                    "user_id": self.test_user_id,
                    "fact_type": data["fact_type"],
                    "confidence_score": data["confidence_score"],
                    "importance_score": 0.7,
                    "source": "test"
                }
                
                async with self.session.post(
                    f"{self.base_url}/api/memory/semantic",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        inserted_ids.append(result["id"])
                        self.log_result(f"Semantic Insert {i+1}", True,
                                      f"ID: {result['id']}, Type: {result['memory_type']}")
                    else:
                        error_data = await response.text()
                        self.log_result(f"Semantic Insert {i+1}", False,
                                      f"Status: {response.status}", error_data)
                        
            except Exception as e:
                self.log_result(f"Semantic Insert {i+1}", False, f"Exception: {str(e)}")
        
        return inserted_ids
    
    async def test_auto_classification(self):
        """AI 자동 분류 테스트"""
        test_cases = [
            {"text": "어제 비가 많이 왔어. 우산 없이 나가서 흠뻑 젖었다.", "expected": "episodic"},
            {"text": "서울의 인구는 약 960만명이다.", "expected": "semantic"},
            {"text": "방금 친구에게서 연락이 왔는데, 결혼한다는 소식이었어!", "expected": "episodic"},
            {"text": "내가 좋아하는 음식은 파스타와 피자다.", "expected": "semantic"},
            {"text": "오늘 아침에 일어나보니 눈이 많이 쌓여있었어.", "expected": "episodic"}
        ]
        
        for i, case in enumerate(test_cases):
            try:
                payload = {
                    "text": case["text"],
                    "user_id": self.test_user_id,
                    "importance_score": 0.6,
                    "source": "auto_classification_test"
                }
                
                async with self.session.post(
                    f"{self.base_url}/api/memory",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        classified_type = result["memory_type"]
                        confidence = result.get("classification_confidence", 0.0)
                        explanation = result.get("classification_explanation", "")
                        
                        success = classified_type == case["expected"]
                        self.log_result(f"Auto Classification {i+1}", success,
                                      f"Text: '{case['text'][:30]}...' -> {classified_type} (confidence: {confidence:.2f})")
                        if not success:
                            print(f"   Expected: {case['expected']}, Got: {classified_type}")
                            print(f"   Explanation: {explanation}")
                    else:
                        error_data = await response.text()
                        self.log_result(f"Auto Classification {i+1}", False,
                                      f"Status: {response.status}", error_data)
                        
            except Exception as e:
                self.log_result(f"Auto Classification {i+1}", False, f"Exception: {str(e)}")
    
    async def test_memory_search(self):
        """메모리 검색 테스트"""
        search_tests = [
            {"type": "episodic", "query": "친구", "min_results": 1},
            {"type": "episodic", "query": "영화", "min_results": 1},
            {"type": "semantic", "query": "생일", "min_results": 1},
            {"type": "semantic", "query": "파리", "min_results": 1}
        ]
        
        for test in search_tests:
            try:
                async with self.session.get(
                    f"{self.base_url}/api/memory/{test['type']}/search",
                    params={"query": test["query"], "limit": 10},
                    headers={"X-User-ID": self.test_user_id}
                ) as response:
                    if response.status == 200:
                        results = await response.json()
                        success = len(results) >= test["min_results"]
                        self.log_result(f"Search {test['type']} - {test['query']}", success,
                                      f"Found {len(results)} results (expected >= {test['min_results']})")
                        
                        # 결과 상세 정보 출력
                        for i, result in enumerate(results[:2]):  # 처음 2개만 출력
                            print(f"   Result {i+1}: {result['text'][:50]}... (score: {result['score']:.3f})")
                    else:
                        error_data = await response.text()
                        self.log_result(f"Search {test['type']} - {test['query']}", False,
                                      f"Status: {response.status}", error_data)
                        
            except Exception as e:
                self.log_result(f"Search {test['type']} - {test['query']}", False, f"Exception: {str(e)}")
    
    async def test_multi_collection_search(self):
        """다중 컬렉션 검색 테스트"""
        search_queries = ["친구", "생일", "영화", "파리"]
        
        for query in search_queries:
            try:
                params = {
                    "query": query,
                    "limit": 10,
                    "episodic_weight": 1.2,
                    "semantic_weight": 0.8
                }
                
                async with self.session.get(
                    f"{self.base_url}/api/memory/search/multi",
                    params=params,
                    headers={"X-User-ID": self.test_user_id}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        total_results = result["total_results"]
                        collection_stats = result["collection_stats"]
                        query_time = result["query_time_ms"]
                        
                        self.log_result(f"Multi Search - {query}", True,
                                      f"Found {total_results} results in {query_time:.2f}ms")
                        print(f"   Collection stats: {collection_stats}")
                        
                        # 결과 타입별 분포 확인
                        if result["results"]:
                            types_count = {}
                            for res in result["results"]:
                                mem_type = res["memory_type"]
                                types_count[mem_type] = types_count.get(mem_type, 0) + 1
                            print(f"   Type distribution: {types_count}")
                    else:
                        error_data = await response.text()
                        self.log_result(f"Multi Search - {query}", False,
                                      f"Status: {response.status}", error_data)
                        
            except Exception as e:
                self.log_result(f"Multi Search - {query}", False, f"Exception: {str(e)}")
    
    async def test_user_statistics(self):
        """사용자 통계 테스트"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/user/{self.test_user_id}/stats"
            ) as response:
                if response.status == 200:
                    stats = await response.json()
                    self.log_result("User Statistics", True,
                                  f"Total: {stats['total_memories']}, "
                                  f"Episodic: {stats['episodic_count']}, "
                                  f"Semantic: {stats['semantic_count']}")
                    print(f"   Daily average: {stats.get('daily_average', 0):.2f}")
                    print(f"   Most active day: {stats.get('most_active_day', 'N/A')}")
                else:
                    error_data = await response.text()
                    self.log_result("User Statistics", False,
                                  f"Status: {response.status}", error_data)
                    
        except Exception as e:
            self.log_result("User Statistics", False, f"Exception: {str(e)}")
    
    async def test_system_statistics(self):
        """시스템 통계 테스트"""
        try:
            async with self.session.get(f"{self.base_url}/api/system/stats") as response:
                if response.status == 200:
                    stats = await response.json()
                    self.log_result("System Statistics", True,
                                  f"Collections: {stats['total_collections']}, "
                                  f"Users: {stats['total_users']}, "
                                  f"Memories: {stats['total_memories']}")
                    
                    # 컬렉션별 통계 출력
                    for collection in stats.get('collections', []):
                        print(f"   Collection {collection['name']}: "
                              f"{collection['total_points']} points, "
                              f"{collection['user_count']} users")
                else:
                    error_data = await response.text()
                    self.log_result("System Statistics", False,
                                  f"Status: {response.status}", error_data)
                    
        except Exception as e:
            self.log_result("System Statistics", False, f"Exception: {str(e)}")
    
    async def test_classification_api(self):
        """분류 API 테스트"""
        test_texts = [
            "오늘 점심에 친구와 만났어",
            "AI는 인공지능을 의미한다",
            "어제 영화관에서 액션 영화를 봤는데 정말 재밌었어",
            "내 취미는 독서와 영화감상이다"
        ]
        
        for i, text in enumerate(test_texts):
            try:
                params = {"text": text}
                
                async with self.session.post(
                    f"{self.base_url}/api/classify",
                    params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        predicted_type = result["predicted_type"]
                        confidence = result["confidence"]
                        explanation = result["explanation"]
                        
                        self.log_result(f"Classification API {i+1}", True,
                                      f"'{text[:30]}...' -> {predicted_type} ({confidence:.2f})")
                        print(f"   Explanation: {explanation}")
                    else:
                        error_data = await response.text()
                        self.log_result(f"Classification API {i+1}", False,
                                      f"Status: {response.status}", error_data)
                        
            except Exception as e:
                self.log_result(f"Classification API {i+1}", False, f"Exception: {str(e)}")
    
    async def test_collection_management(self):
        """컬렉션 관리 테스트"""
        # 현재는 초기화만 테스트 (실제 운영에서는 위험할 수 있음)
        try:
            # 컬렉션 상태 확인을 위한 시스템 통계 호출
            async with self.session.get(f"{self.base_url}/api/system/stats") as response:
                if response.status == 200:
                    stats = await response.json()
                    self.log_result("Collection Status Check", True,
                                  f"Found {stats['total_collections']} collections")
                    
                    for collection in stats.get('collections', []):
                        print(f"   {collection['name']}: {collection['total_points']} points")
                else:
                    self.log_result("Collection Status Check", False, f"Status: {response.status}")
                    
        except Exception as e:
            self.log_result("Collection Status Check", False, f"Exception: {str(e)}")
    
    def generate_test_report(self):
        """테스트 결과 리포트 생성"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST REPORT")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests")
        print("="*80)
        
        if failed_tests > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print(f"\nTest completed at {datetime.now().isoformat()}")
        print(f"Test user ID: {self.test_user_id}")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": passed_tests/total_tests if total_tests > 0 else 0,
            "details": self.test_results
        }
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("Starting Comprehensive Memory Server V2 Tests...")
        print(f"Test User ID: {self.test_user_id}")
        print(f"Server URL: {self.base_url}")
        print("-" * 80)
        
        await self.create_session()
        
        try:
            # 1. 기본 연결 테스트
            if not await self.test_health_check():
                print("Server is not accessible. Aborting tests.")
                return self.generate_test_report()
            
            # 2. 메모리 삽입 테스트
            print("\nTesting Memory Insertion...")
            await self.test_episodic_memory_insertion()
            await self.test_semantic_memory_insertion()
            
            # 3. 자동 분류 테스트
            print("\nTesting Auto Classification...")
            await self.test_auto_classification()
            
            # 4. 검색 테스트
            print("\nTesting Memory Search...")
            await self.test_memory_search()
            await self.test_multi_collection_search()
            
            # 5. 통계 테스트
            print("\nTesting Statistics...")
            await self.test_user_statistics()
            await self.test_system_statistics()
            
            # 6. API 테스트
            print("\nTesting APIs...")
            await self.test_classification_api()
            await self.test_collection_management()
            
        finally:
            await self.close_session()
        
        return self.generate_test_report()

async def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5602"
    
    tester = ComprehensiveMemoryServerTest(base_url)
    report = await tester.run_all_tests()
    
    # 테스트 결과를 파일로 저장
    os.makedirs("test_reports", exist_ok=True)
    report_filename = f"test_reports/test_report_{int(time.time())}.json"
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed report saved to: {report_filename}")
    
    # 실패한 테스트가 있으면 종료 코드 1 반환
    if report["failed"] > 0:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())