# 2가지 기억 유형 VectorDB 컬렉션 구축 계획

## 개요

이 문서는 현재 단일 컬렉션 기반의 벡터 데이터베이스를 2가지 핵심 기억 유형(Episodic, Semantic) 컬렉션으로 확장하는 계획을 제시합니다. 복잡성과 비용을 최적화하면서도 핵심 기능을 유지하는 효율적인 설계입니다.

## 설계 원칙

### 1. 단순화된 메모리 분류
- **Episodic Memory**: 시간·장소·감정이 포함된 경험 기억
- **Semantic Memory**: 시간에 독립적인 사실·지식·개인프로필 기억

### 2. 효율적인 사용자 분리
- Collection별 사용자 분리 ❌
- user_id 메타데이터 방식 ✅
- 장점: Collection 수 고정, 인덱스 공유, 관리 단순화

## 컬렉션 구조

```python
collections = {
    "episodic": "경험 기억",    # 대화, 사건, 감정이 포함된 시간별 경험
    "semantic": "지식 기억"     # 사실, 지식, 개인 프로필 정보
}
```

## 1. Episodic Memory (경험 기억)

### 정의
특정 시간·장소·사건 단위로 저장되는 개인 경험 기억

### 저장 대상
- 일상 대화 내용
- 감정 상태와 함께 기록된 사건
- 특정 시점의 경험과 맥락

### 데이터 스키마
```json
{
  "id": "uuid",
  "text": "오늘 너무 피곤해",
  "embedding": "...",
  "user_id": "user123",
  "timestamp": "2025-08-26T07:15:00Z",
  "speaker": "user | ai",
  "emotion": {
    "valence": "negative",
    "arousal": "high", 
    "labels": ["피곤함", "우울함"],
    "intensity": 0.8
  },
  "context": {
    "location": "home",
    "device": "mobile",
    "conversation_id": "conv_20250826_1"
  },
  "importance_score": 0.7,
  "source": "conversation",
  "links": ["uuid1", "uuid2"]
}
```

### 컬렉션 설정
- **벡터 차원**: 1536 (복잡한 경험과 감정 표현)
- **거리 함수**: COSINE
- **인덱스 설정**: {"m": 16, "ef_construct": 200}

### 검색 최적화
- 시간 기반 가중치 (최근 기억 우선)
- 감정 유형별 필터링
- 발화자별 검색 (user/ai)
- 연관 기억 그래프 탐색

## 2. Semantic Memory (지식 기억)

### 정의
시간·장소에 독립적인 사실과 지식 정보

### 저장 대상
- 개인 사실 정보 (생일, 취향, 직업 등)
- 일반 상식과 지식
- AI 페르소나 정보

### 데이터 스키마
```json
{
  "id": "uuid",
  "text": "아빠의 생일은 3월 21일이다",
  "embedding": "...",
  "user_id": "user123",
  "fact_type": "personal_fact | world_fact | ai_persona",
  "source": "user_profile | conversation | external_knowledge",
  "last_updated": "2025-08-26T07:15:00Z",
  "confidence_score": 1.0,
  "importance_score": 0.9
}
```

### 컬렉션 설정
- **벡터 차원**: 768 (의미적 관계 표현 최적화)
- **거리 함수**: DOT (지식 간 연관성 강조)
- **인덱스 설정**: {"m": 32, "ef_construct": 400}

### 검색 최적화
- 신뢰도 기반 가중치
- 지식 유형별 분류 검색
- 최신성 기반 우선순위
- 개인 프로필 관리

## 3. 시스템 아키텍처

### 3.1 설정 시스템

```python
from enum import Enum
from typing import Dict, Any

class MemoryType(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"

class CollectionConfig(BaseSettings):
    collections: Dict[str, Dict[str, Any]] = {
        "episodic": {
            "vector_dim": 1536,
            "distance": "COSINE",
            "metadata_schema": [
                "user_id", "timestamp", "speaker", "emotion", 
                "context", "importance_score", "source", "links"
            ],
            "index_params": {"m": 16, "ef_construct": 200}
        },
        "semantic": {
            "vector_dim": 768,
            "distance": "DOT",
            "metadata_schema": [
                "user_id", "fact_type", "source", "last_updated", 
                "confidence_score", "importance_score"
            ],
            "index_params": {"m": 32, "ef_construct": 400}
        }
    }
    
    default_collection: str = "semantic"
    auto_create_collections: bool = True
```

### 3.2 Repository 패턴

```python
class MultiCollectionQdrantRepository(VectorDBRepository):
    def __init__(self):
        self.qdrant = QdrantClient(host=db_config.qdrant_host, port=db_config.qdrant_port)
        self.collection_configs = CollectionConfig().collections
        
    def insert_memory(self, memory_data: dict, user_id: str, memory_type: MemoryType):
        """user_id를 메타데이터로 추가하여 저장"""
        collection_name = memory_type.value
        memory_data["user_id"] = user_id
        return self._insert_to_collection(collection_name, memory_data)
        
    def search_memory(self, query: str, user_id: str, memory_type: MemoryType, limit: int = 10):
        """user_id 필터링으로 사용자별 검색"""
        collection_name = memory_type.value
        filter_condition = {"user_id": user_id}
        return self._search_collection(collection_name, query, filter_condition, limit)
```

### 3.3 지능형 라우팅

```python
class IntelligentMemoryRouter:
    def determine_memory_type(self, content: str, context: Dict) -> MemoryType:
        """AI 기반 메모리 타입 자동 분류"""
        # 시간 표현, 감정, 경험적 내용 → Episodic
        # 사실, 정의, 지식 → Semantic
        pass
        
    def route_to_collection(self, memory_point: MemoryPoint, user_id: str) -> str:
        """메모리를 적절한 컬렉션으로 라우팅"""
        memory_type = self.determine_memory_type(memory_point.text, memory_point.context)
        return memory_type.value
```

## 4. API 설계

### 4.1 새로운 엔드포인트

```python
@router.post("/memory/{collection_type}")
async def insert_memory_by_type(
    collection_type: MemoryType, 
    request: MemoryRequest, 
    user_id: str = Header(...)
):
    """컬렉션별 메모리 삽입 + user_id 메타데이터 추가"""
    pass

@router.get("/memory/{collection_type}/search")
async def search_memory_by_type(
    collection_type: MemoryType, 
    query: str, 
    user_id: str = Header(...),
    limit: int = 10
):
    """컬렉션별 검색 + user_id 필터링"""
    pass

@router.get("/memory/search/multi")
async def multi_collection_search(
    query: str,
    user_id: str = Header(...),
    collections: List[MemoryType] = Query(default=[MemoryType.EPISODIC, MemoryType.SEMANTIC]),
    weights: Optional[Dict[str, float]] = None
):
    """다중 컬렉션 통합 검색"""
    pass
```

### 4.2 하이브리드 검색

```python
def hybrid_search(query: str, user_id: str, collection_weights: Dict[MemoryType, float]):
    """가중치 기반 다중 컬렉션 검색"""
    results = {}
    for collection_type, weight in collection_weights.items():
        collection_results = search_in_collection(query, user_id, collection_type)
        results[collection_type] = [(r, r.score * weight) for r in collection_results]
    
    return merge_and_rank_results(results)
```

## 5. 구현 단계

### Phase 1: 설정 시스템 확장 (1-2일)
1. CollectionConfig 클래스 구현
2. MemoryType enum 정의
3. 환경 변수 기반 설정 지원

### Phase 2: Repository 패턴 확장 (2-3일)
1. MultiCollectionQdrantRepository 구현
2. user_id 메타데이터 처리 로직
3. 컬렉션별 최적화된 검색

### Phase 3: Service Layer 구현 (2-3일)
1. IntelligentMemoryRouter 구현
2. 하이브리드 검색 알고리즘
3. 결과 통합 및 랭킹

### Phase 4: API 확장 (1-2일)
1. 새로운 엔드포인트 구현
2. 기존 API와의 호환성 유지
3. 문서화 및 테스트

## 6. 마이그레이션 전략

### 6.1 점진적 마이그레이션
1. **병렬 구축**: 기존 시스템과 새 시스템 동시 운영
2. **신규 데이터**: 새 시스템으로 라우팅
3. **기존 데이터**: AI 기반 자동 분류 후 이주
4. **단계적 전환**: 검증 후 구 시스템 폐기

### 6.2 데이터 분류 규칙
```python
def classify_existing_data(text: str, metadata: dict) -> MemoryType:
    """기존 데이터 자동 분류"""
    # 시간 표현 포함 → Episodic
    if has_temporal_expression(text):
        return MemoryType.EPISODIC
    
    # 감정 표현 포함 → Episodic  
    if has_emotional_content(text):
        return MemoryType.EPISODIC
    
    # 사실/정의 표현 → Semantic
    if is_factual_content(text):
        return MemoryType.SEMANTIC
    
    # 기본값: Semantic
    return MemoryType.SEMANTIC
```

## 7. 성능 최적화

### 7.1 인덱싱 최적화
- 컬렉션별 맞춤 인덱스 파라미터
- user_id 필드 보조 인덱스
- 메타데이터 필드별 선택적 인덱싱

### 7.2 캐싱 전략
- 자주 검색되는 사용자 쿼리 캐싱
- 컬렉션별 통계 정보 캐싱
- 임베딩 벡터 캐싱

### 7.3 배치 처리
- 대량 삽입 시 배치 모드
- 컬렉션별 병렬 검색
- 결과 병합 최적화

## 8. 모니터링

### 8.1 핵심 지표
- 컬렉션별 사용량 분포
- 사용자별 데이터 증가율
- 검색 성능 및 정확도
- 메모리 타입 분류 정확도

### 8.2 관리 도구
- 컬렉션 상태 대시보드
- 사용자별 데이터 통계
- 자동 분류 결과 검증 도구

## 9. 결론

### 주요 장점
- **단순화**: 5개 → 2개 컬렉션으로 관리 복잡도 대폭 감소
- **비용 효율성**: Collection 수 최소화로 리소스 절약
- **확장성**: user_id 메타데이터 방식으로 사용자 수 제한 없음
- **성능**: 컬렉션별 최적화된 인덱스와 검색 알고리즘

### 예상 효과
- 개발 기간: 5-8일 (기존 8-12일 대비 단축)
- 운영 비용: 60% 절감 (컬렉션 수 감소)
- 관리 복잡도: 70% 감소
- 검색 품질: 핵심 기능 유지하면서 단순화

이 설계는 복잡성과 비용을 최적화하면서도 인간의 기억 구조를 효과적으로 모방하는 실용적인 솔루션입니다.