from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
import json

router = APIRouter(tags=["Help & Documentation"])

@router.get("/help", response_class=HTMLResponse, summary="도움말 페이지")
async def help_page():
    """Memory Server 사용 가이드 HTML 페이지"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Memory Server API 도움말</title>
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px;
                line-height: 1.6;
                color: #333;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 30px;
            }
            .section {
                background: #f8f9fa;
                padding: 25px;
                margin: 20px 0;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }
            .endpoint {
                background: white;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
                border: 1px solid #e9ecef;
            }
            .method {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                margin-right: 10px;
            }
            .get { background: #e7f3ff; color: #0066cc; }
            .post { background: #e8f5e8; color: #00aa00; }
            .delete { background: #ffe6e6; color: #cc0000; }
            pre {
                background: #f1f3f4;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
                font-size: 14px;
            }
            .memory-type {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                margin: 5px;
            }
            .episodic { background: #fff3cd; color: #856404; }
            .semantic { background: #d1ecf1; color: #0c5460; }
            ul li { margin: 8px 0; }
            .quick-start {
                background: #e8f5e8;
                border-left-color: #28a745;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🧠 Memory Server API</h1>
            <p>인간의 기억 구조를 모방한 지능형 벡터 데이터베이스</p>
        </div>

        <div class="section quick-start">
            <h2>🚀 빠른 시작</h2>
            <h3>1. 메모리 삽입 (자동 분류)</h3>
            <pre>curl -X POST http://localhost:5602/api/memory \\
  -H "Content-Type: application/json" \\
  -d '{
    "text": "오늘 아침에 맛있는 커피를 마셨어",
    "user_id": "user123"
  }'</pre>
            
            <h3>2. 메모리 검색</h3>
            <pre>curl "http://localhost:5602/api/memory/search/multi?query=커피" \\
  -H "X-User-ID: user123"</pre>
        </div>

        <div class="section">
            <h2>🧠 메모리 타입</h2>
            <div style="margin: 20px 0;">
                <span class="memory-type episodic">Episodic Memory</span>
                <span class="memory-type semantic">Semantic Memory</span>
            </div>
            
            <h3>Episodic Memory (경험 기억)</h3>
            <ul>
                <li><strong>정의</strong>: 시간·장소·감정이 포함된 개인 경험</li>
                <li><strong>예시</strong>: "어제 친구와 영화를 봤어", "오늘 기분이 좋아"</li>
                <li><strong>특징</strong>: speaker, emotion, context, links 필드 활용</li>
            </ul>
            
            <h3>Semantic Memory (지식 기억)</h3>
            <ul>
                <li><strong>정의</strong>: 시간에 독립적인 사실과 지식</li>
                <li><strong>예시</strong>: "내 생일은 3월 15일이다", "파이썬은 프로그래밍 언어다"</li>
                <li><strong>특징</strong>: fact_type, confidence_score 필드 활용</li>
            </ul>
        </div>

        <div class="section">
            <h2>📝 주요 API 엔드포인트</h2>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <strong>/api/memory</strong>
                <p>AI 자동 분류로 메모리 삽입</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <strong>/api/memory/{memory_type}</strong>
                <p>특정 타입(episodic/semantic)으로 메모리 삽입</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong>/api/memory/{memory_type}/search</strong>
                <p>특정 메모리 타입에서 검색 (Headers: X-User-ID)</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong>/api/memory/search/multi</strong>
                <p>다중 타입 통합 검색 (가중치 지원)</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <strong>/api/classify</strong>
                <p>텍스트 메모리 타입 분류 (삽입 전 미리보기)</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong>/api/user/{user_id}/stats</strong>
                <p>사용자 메모리 통계</p>
            </div>
        </div>

        <div class="section">
            <h2>💡 사용 팁</h2>
            <h3>검색 최적화</h3>
            <ul>
                <li><strong>가중치 조정</strong>: episodic_weight=1.2, semantic_weight=0.8</li>
                <li><strong>유사도 임계값</strong>: similarity_threshold=0.7 (정확한 매칭)</li>
                <li><strong>구체적 쿼리</strong>: "커피" → "아침에 마신 커피"</li>
            </ul>
            
            <h3>메모리 분류 개선</h3>
            <ul>
                <li><strong>컨텍스트 제공</strong>: emotion, context 필드 활용</li>
                <li><strong>타입 힌트</strong>: fact_type, speaker 필드 명시</li>
                <li><strong>분류 확인</strong>: /api/classify로 미리 테스트</li>
            </ul>
        </div>

        <div class="section">
            <h2>📚 추가 리소스</h2>
            <ul>
                <li><a href="/docs" target="_blank">📖 Swagger API 문서</a></li>
                <li><a href="/redoc" target="_blank">📋 ReDoc 문서</a></li>
                <li><a href="/health" target="_blank">💚 서버 상태 확인</a></li>
                <li><a href="/system/info" target="_blank">ℹ️ 시스템 정보</a></li>
            </ul>
        </div>

        <div class="section">
            <h2>🔧 개발자 정보</h2>
            <ul>
                <li><strong>서버 포트</strong>: 5602</li>
                <li><strong>벡터 DB</strong>: Qdrant (포트 6333)</li>
                <li><strong>임베딩</strong>: SentenceTransformer / OpenAI</li>
                <li><strong>로그</strong>: logs/app.log</li>
            </ul>
        </div>

        <div style="text-align: center; margin-top: 40px; color: #666;">
            <p>Memory Server v2.0 | Built with FastAPI & Qdrant</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/help/examples", summary="API 사용 예제")
async def api_examples():
    """다양한 API 사용 예제를 JSON으로 제공"""
    examples = {
        "memory_insertion": {
            "auto_classify": {
                "description": "AI 자동 분류로 메모리 삽입",
                "method": "POST",
                "url": "/api/memory",
                "body": {
                    "text": "오늘 점심에 맛있는 파스타를 먹었어",
                    "user_id": "user123",
                    "speaker": "user",
                    "emotion": {
                        "valence": "positive",
                        "intensity": 0.7
                    }
                },
                "curl": "curl -X POST http://localhost:5602/api/memory -H 'Content-Type: application/json' -d '{\"text\": \"오늘 점심에 맛있는 파스타를 먹었어\", \"user_id\": \"user123\"}'"
            },
            "episodic_manual": {
                "description": "Episodic 메모리 직접 삽입",
                "method": "POST", 
                "url": "/api/memory/episodic",
                "body": {
                    "text": "어제 동료와 프로젝트 회의를 했어",
                    "user_id": "user123",
                    "speaker": "user",
                    "context": {
                        "location": "office",
                        "participants": ["김팀장", "이대리"]
                    }
                }
            },
            "semantic_manual": {
                "description": "Semantic 메모리 직접 삽입",
                "method": "POST",
                "url": "/api/memory/semantic", 
                "body": {
                    "text": "내 취미는 독서와 영화감상이다",
                    "user_id": "user123",
                    "fact_type": "personal_fact",
                    "confidence_score": 1.0
                }
            }
        },
        "memory_search": {
            "single_type": {
                "description": "단일 타입 검색",
                "method": "GET",
                "url": "/api/memory/episodic/search?query=파스타&limit=5",
                "headers": {"X-User-ID": "user123"},
                "curl": "curl 'http://localhost:5602/api/memory/episodic/search?query=파스타&limit=5' -H 'X-User-ID: user123'"
            },
            "multi_type": {
                "description": "다중 타입 통합 검색",
                "method": "GET",
                "url": "/api/memory/search/multi?query=취미&episodic_weight=1.2&semantic_weight=0.8",
                "headers": {"X-User-ID": "user123"},
                "curl": "curl 'http://localhost:5602/api/memory/search/multi?query=취미&episodic_weight=1.2' -H 'X-User-ID: user123'"
            }
        },
        "classification": {
            "text_classify": {
                "description": "텍스트 분류 미리보기",
                "method": "POST",
                "url": "/api/classify?text=오늘 기분이 좋아",
                "curl": "curl -X POST 'http://localhost:5602/api/classify?text=오늘 기분이 좋아'"
            }
        },
        "management": {
            "user_stats": {
                "description": "사용자 메모리 통계",
                "method": "GET",
                "url": "/api/user/user123/stats",
                "curl": "curl http://localhost:5602/api/user/user123/stats"
            },
            "system_stats": {
                "description": "시스템 전체 통계",
                "method": "GET", 
                "url": "/api/system/stats",
                "curl": "curl http://localhost:5602/api/system/stats"
            },
            "delete_memories": {
                "description": "사용자 메모리 삭제",
                "method": "DELETE",
                "url": "/api/user/user123/memories?memory_type=episodic",
                "curl": "curl -X DELETE 'http://localhost:5602/api/user/user123/memories?memory_type=episodic'"
            }
        }
    }
    
    return JSONResponse(content=examples)

@router.get("/help/fields", summary="메모리 타입별 필드 가이드")
async def field_guide():
    """메모리 타입별 사용 가능한 필드와 설명"""
    guide = {
        "common_fields": {
            "description": "모든 메모리 타입에서 사용 가능한 공통 필드",
            "fields": {
                "text": {
                    "type": "string",
                    "required": True,
                    "description": "저장할 텍스트 내용"
                },
                "user_id": {
                    "type": "string", 
                    "required": True,
                    "description": "사용자 ID (영문자, 숫자, _, - 만 가능)"
                },
                "timestamp": {
                    "type": "string",
                    "required": False,
                    "description": "ISO 형식 타임스탬프 (자동 생성 가능)"
                },
                "importance_score": {
                    "type": "float",
                    "required": False,
                    "default": 0.5,
                    "range": "0.0 - 1.0",
                    "description": "메모리 중요도 점수"
                },
                "source": {
                    "type": "string",
                    "required": False,
                    "default": "conversation",
                    "description": "메모리 생성 출처"
                }
            }
        },
        "episodic_fields": {
            "description": "Episodic Memory 전용 필드 (개인 경험, 대화, 감정)",
            "fields": {
                "speaker": {
                    "type": "string",
                    "options": ["user", "ai"],
                    "description": "발화자 구분"
                },
                "emotion": {
                    "type": "object",
                    "description": "감정 정보 객체",
                    "properties": {
                        "valence": {
                            "type": "string",
                            "options": ["positive", "negative", "neutral"],
                            "description": "감정 극성"
                        },
                        "arousal": {
                            "type": "string", 
                            "options": ["high", "medium", "low"],
                            "description": "감정 각성도"
                        },
                        "labels": {
                            "type": "array",
                            "description": "구체적 감정 라벨 목록"
                        },
                        "intensity": {
                            "type": "float",
                            "range": "0.0 - 1.0",
                            "description": "감정 강도"
                        }
                    }
                },
                "context": {
                    "type": "object",
                    "description": "상황 정보 객체",
                    "properties": {
                        "location": "위치 정보",
                        "conversation_id": "대화 세션 ID",
                        "device": "사용 기기",
                        "participants": "참여자 목록"
                    }
                },
                "links": {
                    "type": "array",
                    "description": "연관된 다른 메모리 ID 목록"
                }
            }
        },
        "semantic_fields": {
            "description": "Semantic Memory 전용 필드 (사실, 지식, 프로필)",
            "fields": {
                "fact_type": {
                    "type": "string",
                    "options": ["personal_fact", "world_fact", "ai_persona"],
                    "description": "사실 정보 유형"
                },
                "confidence_score": {
                    "type": "float",
                    "range": "0.0 - 1.0",
                    "default": 1.0,
                    "description": "정보의 신뢰도"
                }
            }
        },
        "usage_examples": {
            "episodic_example": {
                "text": "어제 친구와 카페에서 수다를 떨었어",
                "user_id": "user123",
                "speaker": "user",
                "emotion": {
                    "valence": "positive",
                    "arousal": "medium",
                    "labels": ["즐거움", "편안함"],
                    "intensity": 0.7
                },
                "context": {
                    "location": "cafe",
                    "participants": ["친구A"],
                    "activity": "chatting"
                }
            },
            "semantic_example": {
                "text": "서울의 인구는 약 970만명이다",
                "user_id": "user123", 
                "fact_type": "world_fact",
                "confidence_score": 0.9,
                "importance_score": 0.4
            }
        }
    }
    
    return JSONResponse(content=guide)