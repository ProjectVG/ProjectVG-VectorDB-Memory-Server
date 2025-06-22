# Memmory Server

FastAPI와 Qdrant를 사용한 벡터 검색 서버입니다.

## Docker 실행 방법

### 1. 서비스 시작
```bash
docker-compose up --build
```

### 2. 백그라운드에서 실행
```bash
docker-compose up -d --build
```

### 3. 서비스 중지
```bash
docker-compose down
```

## 서비스 정보

- **FastAPI 서버**: http://localhost:5001
- **Qdrant 데이터베이스**: http://localhost:6333
- **API 문서**: http://localhost:5001/docs

## API 엔드포인트

### 텍스트 삽입
```bash
POST /insert
Content-Type: application/json

{
  "text": "삽입할 텍스트",
  "metadata": {"key": "value"}
}
```

### 텍스트 검색
```bash
POST /search
Content-Type: application/json

{
  "query": "검색할 텍스트",
  "top_k": 3
}
```

## 환경 변수

- `QDRANT_HOST`: Qdrant 서버 호스트 (기본값: localhost)
- `QDRANT_PORT`: Qdrant 서버 포트 (기본값: 6333)

## 데이터 저장

Qdrant 데이터는 Docker 볼륨 `qdrant_data`에 저장되어 컨테이너가 재시작되어도 유지됩니다. 