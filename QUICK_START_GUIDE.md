# Memory Server 빠른 시작 가이드

## 🚀 5분 안에 시작하기

### 1. 서버 실행
```bash
# Docker로 실행 (권장)
docker-compose up --build

# 또는 직접 실행
python app.py
```

### 2. 기본 사용법

#### ✨ 메모리 자동 저장
```bash
# AI가 자동으로 타입을 분류해서 저장
curl -X POST http://localhost:5602/api/memory \
  -H "Content-Type: application/json" \
  -d '{
    "text": "오늘 아침에 맛있는 커피를 마셨어",
    "user_id": "me"
  }'
```

#### 🔍 메모리 검색
```bash
# 모든 메모리에서 검색
curl "http://localhost:5602/api/memory/search/multi?query=커피" \
  -H "X-User-ID: me"
```

#### 🧠 분류 미리보기
```bash
# 저장하기 전에 어떤 타입인지 확인
curl -X POST "http://localhost:5602/api/classify?text=오늘 기분이 좋아"
```

### 3. 브라우저에서 확인
- **도움말**: http://localhost:5602/help
- **API 문서**: http://localhost:5602/docs
- **서버 상태**: http://localhost:5602/health

## 🧠 메모리 타입 이해하기

### Episodic Memory (경험 기억) 
**"그때 무엇을 했나?"**
- 개인 경험, 대화, 감정이 포함된 기억
- 예: "어제 친구와 영화를 봤어", "지금 기분이 좋아"

### Semantic Memory (지식 기억)
**"무엇을 알고 있나?"**  
- 사실, 지식, 개인 정보 등 시간에 독립적인 기억
- 예: "내 생일은 3월 15일", "파이썬은 프로그래밍 언어다"

## 📝 실용적인 사용 예제

### 대화형 AI 시스템
```python
import requests

# 사용자 발언 저장
def save_user_message(user_id, message):
    return requests.post("http://localhost:5602/api/memory", json={
        "text": message,
        "user_id": user_id,
        "speaker": "user"
    })

# AI 응답 저장
def save_ai_response(user_id, response):
    return requests.post("http://localhost:5602/api/memory", json={
        "text": response, 
        "user_id": user_id,
        "speaker": "ai"
    })

# 관련 기억 검색
def search_memories(user_id, query):
    return requests.get(f"http://localhost:5602/api/memory/search/multi", 
                       params={"query": query},
                       headers={"X-User-ID": user_id})
```

### 개인 일기 시스템
```bash
# 오늘의 경험 저장
curl -X POST http://localhost:5602/api/memory \
  -H "Content-Type: application/json" \
  -d '{
    "text": "오늘 새로운 카페에서 공부했는데 분위기가 너무 좋았어",
    "user_id": "diary_user",
    "emotion": {
      "valence": "positive",
      "intensity": 0.8,
      "labels": ["만족", "편안"]
    },
    "context": {
      "location": "new_cafe",
      "activity": "studying"
    }
  }'

# 과거 경험 찾기
curl "http://localhost:5602/api/memory/episodic/search?query=카페" \
  -H "X-User-ID: diary_user"
```

### 개인 지식베이스
```bash
# 새로운 지식 저장
curl -X POST http://localhost:5602/api/memory/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "text": "FastAPI는 Python 기반의 고성능 웹 프레임워크다",
    "user_id": "developer",
    "fact_type": "world_fact",
    "confidence_score": 1.0
  }'

# 지식 검색
curl "http://localhost:5602/api/memory/semantic/search?query=FastAPI" \
  -H "X-User-ID: developer"
```

## 🔧 고급 사용법

### 검색 최적화
```bash
# 가중치로 특정 타입 우선하기
curl "http://localhost:5602/api/memory/search/multi?query=프로젝트&episodic_weight=0.3&semantic_weight=1.5" \
  -H "X-User-ID: user123"

# 유사도 임계값으로 정확도 높이기  
curl "http://localhost:5602/api/memory/search/multi?query=커피&similarity_threshold=0.7" \
  -H "X-User-ID: user123"
```

### 감정 정보 활용
```bash
curl -X POST http://localhost:5602/api/memory \
  -H "Content-Type: application/json" \
  -d '{
    "text": "팀 프로젝트가 성공적으로 끝났어!",
    "user_id": "worker",
    "emotion": {
      "valence": "positive",
      "arousal": "high", 
      "labels": ["성취감", "기쁨"],
      "intensity": 0.9
    },
    "context": {
      "location": "office",
      "project": "team_project_alpha"
    }
  }'
```

## 📊 메모리 관리

### 내 메모리 현황 확인
```bash
curl http://localhost:5602/api/user/me/stats
```

### 특정 타입 메모리만 삭제
```bash
# Episodic 메모리만 삭제
curl -X DELETE "http://localhost:5602/api/user/me/memories?memory_type=episodic"
```

### 시스템 상태 확인
```bash
curl http://localhost:5602/api/system/stats
```

## 🎯 유용한 팁

### 1. 자동 분류 정확도 높이기
- **감정 표현**: "기쁘다", "슬프다", "화나다" → Episodic
- **시간 표현**: "오늘", "어제", "지금" → Episodic  
- **사실 표현**: "~이다", "~입니다" → Semantic
- **컨텍스트 제공**: speaker, emotion, context 필드 활용

### 2. 검색 품질 개선
- **구체적 쿼리**: "음식" → "점심에 먹은 파스타"
- **가중치 조정**: 원하는 타입에 높은 가중치 부여
- **분류 미리보기**: `/api/classify`로 검색 전 확인

### 3. 성능 최적화
- **배치 처리**: 대량 삽입시 적절한 간격 유지
- **캐시 활용**: 동일한 쿼리는 자동 캐시됨
- **임계값 설정**: 필요한 정확도에 맞춰 similarity_threshold 조정

## 🚨 문제 해결

### 서버 연결 안됨
```bash
# 서버 상태 확인
curl http://localhost:5602/health

# Docker 컨테이너 상태 확인
docker-compose ps

# 로그 확인
tail -f logs/app.log
```

### 검색 결과가 이상함
```bash
# 분류 결과 확인
curl -X POST "http://localhost:5602/api/classify?text=YOUR_TEXT"

# 사용자 메모리 현황 확인
curl http://localhost:5602/api/user/YOUR_USER_ID/stats
```

### 분류가 잘못됨
```bash
# 수동으로 특정 타입 지정
curl -X POST http://localhost:5602/api/memory/episodic \
  -d '{"text": "YOUR_TEXT", "user_id": "YOUR_ID"}'
```

## 🔗 더 많은 정보

- **상세 API 문서**: [docs/API_GUIDE.md](docs/API_GUIDE.md)
- **웹 기반 도움말**: http://localhost:5602/help
- **Swagger 문서**: http://localhost:5602/docs
- **필드 가이드**: http://localhost:5602/help/fields
- **사용 예제**: http://localhost:5602/help/examples

---

**🎉 축하합니다!** 이제 Memory Server의 기본 사용법을 알게 되었습니다. 더 자세한 내용은 위의 링크들을 참고하세요.