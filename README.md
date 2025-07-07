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

## 환경 변수 설정

### 1. 환경변수 파일 생성
```bash
cp env.example .env
```

### 2. 환경변수 수정
`.env` 파일을 열어 필요한 값들을 수정하세요:

#### Qdrant 설정
- `QDRANT_HOST`: Qdrant 서버 호스트 (기본값: localhost)
- `QDRANT_PORT`: Qdrant 서버 포트 (기본값: 6333)
- `COLLECTION_NAME`: 벡터 컬렉션 이름 (기본값: my_vectors)

#### 임베딩 서비스 설정
- `EMBEDDING_TYPE`: 임베딩 서비스 타입
  - `sentence_transformer`: 로컬 SentenceTransformer 모델 사용 (기본값)
  - `openai`: OpenAI 임베딩 API 사용
- `MODEL_NAME`: SentenceTransformer 모델명 (기본값: sentence-transformers/all-MiniLM-L6-v2)

#### OpenAI 설정 (EMBEDDING_TYPE=openai일 때)
- `OPENAI_API_KEY`: OpenAI API 키 (필수)
- `OPENAI_MODEL_NAME`: OpenAI 임베딩 모델명 (기본값: text-embedding-ada-002)

#### 애플리케이션 설정
- `PORT`: FastAPI 서버 포트 (기본값: 5001)
- `LOG_LEVEL`: 로그 레벨 (기본값: INFO)
- `DEBUG`: 개발 모드 (기본값: False)

## 데이터 저장

Qdrant 데이터는 Docker 볼륨 `qdrant_data`에 저장되어 컨테이너가 재시작되어도 유지됩니다. 