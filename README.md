# Memory Server V2 - 다중 컬렉션 아키텍처

## 개요

Memory Server V2는 인간의 기억 구조를 모방한 2가지 핵심 기억 유형(Episodic, Semantic)을 지원하는 벡터 데이터베이스 기반 메모리 서버입니다.

## 주요 변경사항

### V1 → V2 업그레이드
- **단일 컬렉션** → **2가지 특화 컬렉션** (Episodic, Semantic)
- **수동 분류** → **AI 기반 자동 분류**
- **기본 검색** → **지능형 하이브리드 검색**
- **단순 메타데이터** → **타입별 특화 스키마**

## 메모리 타입

### 1. Episodic Memory (경험 기억)
- **정의**: 시간·장소·사건 중심의 개인 경험 기억
- **저장 대상**: 일상 대화, 감정 상태, 특정 시점의 경험
- **컬렉션 설정**: 1536차원, COSINE 거리함수
- **특화 필드**: speaker, emotion, context, links

```json
{
  "id": "uuid",
  "text": "오늘 너무 피곤해",
  "user_id": "user123",
  "timestamp": "2025-08-26T07:15:00Z",
  "speaker": "user",
  "emotion": {
    "valence": "negative",
    "arousal": "high",
    "labels": ["피곤함"],
    "intensity": 0.8
  },
  "context": {
    "location": "home",
    "conversation_id": "conv_001"
  }
}
```

### 2. Semantic Memory (지식 기억)
- **정의**: 시간·장소에 독립적인 사실과 지식 정보
- **저장 대상**: 개인 프로필, 일반 상식, AI 페르소나 정보
- **컬렉션 설정**: 768차원, DOT 거리함수
- **특화 필드**: fact_type, confidence_score, last_updated

```json
{
  "id": "uuid",
  "text": "아빠의 생일은 3월 21일이다",
  "user_id": "user123",
  "fact_type": "personal_fact",
  "confidence_score": 1.0,
  "last_updated": "2025-08-26T07:15:00Z"
}
```

## API 엔드포인트

### V2 API (새로운 다중 컬렉션 API)

#### 메모리 삽입
```bash
# 자동 분류 삽입
POST /v2/memory
{
  "text": "오늘 커피가 맛있었어",
  "user_id": "user123",
  "speaker": "user",
  "emotion": {"valence": "positive", "intensity": 0.7}
}

# 수동 타입 지정 삽입
POST /v2/memory/episodic
POST /v2/memory/semantic
```

#### 검색
```bash
# 단일 컬렉션 검색
GET /v2/memory/episodic/search?query=커피&limit=5
GET /v2/memory/semantic/search?query=생일&limit=5

# 다중 컬렉션 통합 검색
GET /v2/memory/search/multi?query=커피&episodic_weight=1.2&semantic_weight=0.8
```

#### 분류 및 통계
```bash
# 텍스트 분류
POST /v2/classify?text=오늘 기분이 좋아

# 사용자 통계
GET /v2/user/{user_id}/stats

# 시스템 통계
GET /v2/system/stats
```

### V1 API (기존 호환성 유지)
기존 V1 API는 그대로 유지되며, 내부적으로 V2 시스템을 통해 처리됩니다.

```bash
POST /insert    # 기존 삽입 API
POST /search    # 기존 검색 API
```

## 자동 분류 시스템

### 분류 규칙
Memory Router는 다음 패턴을 분석하여 자동 분류합니다:

#### Episodic 분류 신호
- **시간 표현**: "오늘", "어제", "지금", "아까"
- **감정 표현**: "기쁘다", "슬프다", "화나다", "피곤해"
- **대화 표현**: "말했다", "물어봤다", "~라고", "~냐고"
- **경험 표현**: 특정 시점의 개인적 경험

#### Semantic 분류 신호  
- **사실 표현**: "~이다", "~입니다", "~됩니다"
- **지식 표현**: "정보", "사실", "개념", "정의"
- **프로필 표현**: "생일", "취미", "직업", "좋아하다"
- **객관 표현**: 시간에 독립적인 사실들

### 분류 신뢰도
- 신뢰도 0.7 이상: 높은 확신도로 분류
- 신뢰도 0.3-0.7: 보통 확신도 (추가 컨텍스트 활용)
- 신뢰도 0.3 이하: 낮은 확신도 (기본값 semantic 사용)

## 검색 전략

### 1. 단일 컬렉션 검색
특정 메모리 타입에서만 검색하여 정확도 향상

### 2. 하이브리드 검색
```python
# 가중치 기반 통합 검색
episodic_results = search_episodic(query) * episodic_weight
semantic_results = search_semantic(query) * semantic_weight
final_results = merge_and_rank(episodic_results, semantic_results)
```

### 3. 지능형 가중치
쿼리 분석을 통해 자동으로 가중치를 조정:
- Episodic 성향 쿼리 → Episodic 가중치 증가
- Semantic 성향 쿼리 → Semantic 가중치 증가

## 설치 및 실행

### 1. 기본 설정
```bash
# 환경 변수 복사
cp env.example .env

# 의존성 설치
pip install -r requirements.txt
```

### 2. 실행
```bash
# Docker 실행 (권장)
docker-compose up --build

# 직접 실행
python app.py
```

### 3. 테스트
```bash
# V2 다중 컬렉션 테스트
python test_multi_collection.py

# 기존 테스트
python test_simple.py
```

## 설정

### 환경 변수
```bash
# Qdrant 설정
QDRANT_HOST=localhost
QDRANT_PORT=6333

# 서버 설정
SERVER_PORT=5602
SERVER_HOST=0.0.0.0

# 임베딩 설정
EMBEDDING_TYPE=sentence_transformer  # or "openai"
OPENAI_API_KEY=your_api_key_here     # OpenAI 사용시
```

### 컬렉션 설정
```python
# src/config/settings.py
class CollectionConfig:
    collections = {
        "episodic": {
            "vector_dim": 1536,
            "distance": "COSINE",
            "metadata_schema": [
                "user_id", "timestamp", "speaker", 
                "emotion", "context", "importance_score"
            ]
        },
        "semantic": {
            "vector_dim": 768,
            "distance": "DOT",
            "metadata_schema": [
                "user_id", "fact_type", "confidence_score",
                "last_updated", "importance_score"
            ]
        }
    }
```

## 마이그레이션

### V1에서 V2로 마이그레이션
1. **기존 데이터 백업**
2. **자동 분류 실행**: 기존 메모리를 AI로 분류
3. **점진적 이주**: 새로운 컬렉션으로 데이터 이동
4. **검증**: 분류 정확도 확인 및 수동 보정

```bash
# 마이그레이션 도구 (개발 예정)
python scripts/migrate_v1_to_v2.py --backup --classify --verify
```

## 성능 최적화

### 1. 인덱싱
- 컬렉션별 맞춤 인덱스 파라미터
- user_id 필드 보조 인덱스 자동 생성
- 메타데이터 필드별 선택적 인덱싱

### 2. 캐싱  
- 자주 검색되는 쿼리 결과 캐싱
- 임베딩 벡터 캐싱
- 컬렉션별 통계 캐싱

### 3. 배치 처리
- 대량 삽입 시 배치 모드 지원
- 컬렉션별 병렬 검색
- 결과 병합 최적화

## 모니터링

### 핵심 지표
- 컬렉션별 사용량 분포
- 분류 정확도 및 신뢰도
- 검색 성능 및 응답 시간
- 사용자별 메모리 증가율

### 관리 도구
- 실시간 대시보드 (개발 예정)
- 분류 결과 검증 도구
- 성능 모니터링 시스템

## 개발 로드맵

### 현재 완료 (V2.0)
- ✅ 2가지 메모리 타입 컬렉션
- ✅ AI 기반 자동 분류
- ✅ 다중 컬렉션 검색
- ✅ 타입별 특화 스키마
- ✅ 기존 API 호환성

### 향후 계획 (V2.1+)
- 🔄 실시간 대시보드
- 🔄 마이그레이션 도구
- 🔄 성능 최적화
- 🔄 고급 분류 모델 적용
- 🔄 시간 기반 메모리 가중치

## 지원

### 문제 해결
- 로그 파일: `logs/app.log`
- 디버그 모드: `LOG_LEVEL=DEBUG`
- 컬렉션 상태 확인: `GET /v2/system/stats`

### 연락처
- 문의: Memory Server 개발팀
- 문서: `/docs` 엔드포인트 (FastAPI 자동 문서)

---

**Memory Server V2**는 인간의 기억 구조를 모방하여 더 지능적이고 효율적인 메모리 관리를 제공합니다.