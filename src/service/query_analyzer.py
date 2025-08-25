from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import re
from dataclasses import dataclass

@dataclass
class QueryIntent:
    """쿼리 의도 분석 결과"""
    original_query: str
    intent_type: str  # "question", "statement", "command"
    extracted_keywords: List[str]
    time_references: List[Dict]  # 시간 관련 참조
    entities: List[Dict]  # 개체명 (사람, 장소, 물건 등)
    action_type: str  # "search", "recall", "compare", "summarize"
    context: Dict  # 추가 컨텍스트 정보

class QueryAnalyzer:
    """LLM 기반 쿼리 분석기"""
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
        self.time_patterns = {
            "어제": -1,
            "오늘": 0,
            "내일": 1,
            "지난주": -7,
            "이번주": 0,
            "다음주": 7,
            "지난달": -30,
            "이번달": 0,
            "다음달": 30
        }
    
    def analyze_query(self, query: str) -> QueryIntent:
        """쿼리 분석 및 의도 추출"""
        # 1. 기본 키워드 추출
        keywords = self._extract_keywords(query)
        
        # 2. 시간 참조 분석
        time_refs = self._analyze_time_references(query)
        
        # 3. 의도 타입 분석
        intent_type = self._analyze_intent_type(query)
        
        # 4. 액션 타입 분석
        action_type = self._analyze_action_type(query)
        
        # 5. 개체명 추출
        entities = self._extract_entities(query)
        
        # 6. 컨텍스트 분석
        context = self._analyze_context(query)
        
        return QueryIntent(
            original_query=query,
            intent_type=intent_type,
            extracted_keywords=keywords,
            time_references=time_refs,
            entities=entities,
            action_type=action_type,
            context=context
        )
    
    def _extract_keywords(self, query: str) -> List[str]:
        """키워드 추출"""
        # 간단한 키워드 추출 (실제로는 LLM 사용)
        stop_words = ["이", "가", "을", "를", "의", "에", "로", "와", "과", "도", "는", "을", "를", "어", "지", "나", "요", "다"]
        words = re.findall(r'\w+', query)
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        return keywords
    
    def _analyze_time_references(self, query: str) -> List[Dict]:
        """시간 참조 분석"""
        time_refs = []
        current_date = datetime.now(timezone.utc)
        
        for pattern, days_offset in self.time_patterns.items():
            if pattern in query:
                target_date = current_date + timedelta(days=days_offset)
                time_refs.append({
                    "pattern": pattern,
                    "target_date": target_date,
                    "days_offset": days_offset,
                    "date_range": self._get_date_range(target_date, days_offset)
                })
        
        # 구체적인 날짜 패턴 분석
        date_patterns = [
            r'(\d{1,2})월\s*(\d{1,2})일',
            r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',
            r'(\d{1,2})일\s*전',
            r'(\d{1,2})주\s*전'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, query)
            for match in matches:
                if len(match) == 2:  # 월일
                    month, day = int(match[0]), int(match[1])
                    target_date = current_date.replace(month=month, day=day)
                elif len(match) == 3:  # 년월일
                    year, month, day = int(match[0]), int(match[1]), int(match[2])
                    target_date = datetime(year, month, day, tzinfo=timezone.utc)
                elif "일 전" in query:
                    days = int(match[0])
                    target_date = current_date - timedelta(days=days)
                elif "주 전" in query:
                    weeks = int(match[0])
                    target_date = current_date - timedelta(weeks=weeks)
                
                time_refs.append({
                    "pattern": match,
                    "target_date": target_date,
                    "date_range": self._get_date_range(target_date, 0)
                })
        
        return time_refs
    
    def _get_date_range(self, target_date: datetime, days_offset: int) -> Tuple[datetime, datetime]:
        """날짜 범위 계산"""
        if days_offset == 0:
            # 특정 날짜
            start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            # 기간
            start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=abs(days_offset))
        
        return start_date, end_date
    
    def _analyze_intent_type(self, query: str) -> str:
        """의도 타입 분석"""
        question_patterns = ["뭐", "어떤", "언제", "어디", "누가", "왜", "어떻게", "몇", "?"]
        command_patterns = ["해줘", "해주세요", "해봐", "해보세요", "찾아", "검색해"]
        
        for pattern in question_patterns:
            if pattern in query:
                return "question"
        
        for pattern in command_patterns:
            if pattern in query:
                return "command"
        
        return "statement"
    
    def _analyze_action_type(self, query: str) -> str:
        """액션 타입 분석"""
        if any(word in query for word in ["뭐", "어떤", "무엇"]):
            return "recall"
        elif any(word in query for word in ["비교", "차이", "다른"]):
            return "compare"
        elif any(word in query for word in ["요약", "정리", "개요"]):
            return "summarize"
        else:
            return "search"
    
    def _extract_entities(self, query: str) -> List[Dict]:
        """개체명 추출"""
        entities = []
        
        # 음식 관련
        food_keywords = ["피자", "햄버거", "치킨", "라면", "밥", "김치", "고기", "생선"]
        for food in food_keywords:
            if food in query:
                entities.append({
                    "type": "food",
                    "value": food,
                    "category": "meal"
                })
        
        # 장소 관련
        place_keywords = ["집", "회사", "학교", "카페", "레스토랑", "영화관", "병원"]
        for place in place_keywords:
            if place in query:
                entities.append({
                    "type": "place",
                    "value": place,
                    "category": "location"
                })
        
        # 사람 관련
        person_keywords = ["친구", "가족", "동료", "선생님", "의사"]
        for person in person_keywords:
            if person in query:
                entities.append({
                    "type": "person",
                    "value": person,
                    "category": "relationship"
                })
        
        return entities
    
    def _analyze_context(self, query: str) -> Dict:
        """컨텍스트 분석"""
        context = {
            "temporal_context": None,
            "spatial_context": None,
            "emotional_context": None,
            "social_context": None
        }
        
        # 시간적 컨텍스트
        if any(word in query for word in ["어제", "오늘", "내일"]):
            context["temporal_context"] = "recent"
        elif any(word in query for word in ["지난주", "이번주"]):
            context["temporal_context"] = "weekly"
        elif any(word in query for word in ["지난달", "이번달"]):
            context["temporal_context"] = "monthly"
        
        # 공간적 컨텍스트
        if any(word in query for word in ["집", "회사", "학교"]):
            context["spatial_context"] = "specific_location"
        
        # 감정적 컨텍스트
        emotional_words = ["좋았", "싫었", "맛있", "재미있", "힘들었"]
        for word in emotional_words:
            if word in query:
                context["emotional_context"] = "emotional"
                break
        
        # 사회적 컨텍스트
        social_words = ["친구", "가족", "동료", "함께"]
        for word in social_words:
            if word in query:
                context["social_context"] = "social"
                break
        
        return context 