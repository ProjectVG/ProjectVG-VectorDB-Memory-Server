import re
from typing import Dict, Any
from src.config.settings import MemoryType
from src.models.memory_point import MemoryPoint

class MemoryClassifier:
    """메모리 타입 자동 분류 및 라우팅 시스템"""
    
    def __init__(self):
        # 시간 표현 패턴
        self.temporal_patterns = [
            r'\b(오늘|어제|내일|지금|현재|방금|아까|나중에)\b',
            r'\b(\d{1,2}시|\d{1,2}분|아침|점심|저녁|밤)\b',
            r'\b(월요일|화요일|수요일|목요일|금요일|토요일|일요일)\b',
            r'\b(\d{4}년|\d{1,2}월|\d{1,2}일)\b',
            r'\b(최근|이전|전에|후에|동안|때)\b'
        ]
        
        # 감정 표현 패턴
        self.emotional_patterns = [
            r'\b(기쁘|행복|즐거|신나|좋|만족|감사)\w*\b',
            r'\b(슬프|우울|힘들|아프|괴로|답답|속상)\w*\b',
            r'\b(화나|짜증|분노|열받|빡치|스트레스)\w*\b',
            r'\b(불안|걱정|두려|무서|긴장|초조)\w*\b',
            r'\b(피곤|지치|힘들|컨디션|몸살|아프)\w*\b',
            r'\b(재밌|웃겨|놀라|신기|대박|와)\w*\b'
        ]
        
        # 대화 표현 패턴
        self.conversation_patterns = [
            r'\b(말했|얘기했|대화했|이야기했|물어봤|답했)\w*\b',
            r'\b(~라고|~다고|~냐고|~니까|~거든|~잖아)\b',
            r'\b(\?|\!|\.{2,}|ㅋㅋ|ㅎㅎ|ㅠㅠ|ㅜㅜ)\b'
        ]
        
        # 사실/지식 표현 패턴
        self.factual_patterns = [
            r'\b(은|는|이다|다|이었|였|입니다|됩니다)\b',
            r'\b(정보|사실|지식|개념|정의|설명)\b',
            r'\b(명사|동사|형용사|부사|문법|규칙)\b',
            r'\b(역사|과학|수학|기술|정치|경제)\b',
            r'\b(\d+%|\d+개|\d+명|\d+원|\d+kg|\d+cm)\b'
        ]
        
        # 개인 프로필 패턴
        self.profile_patterns = [
            r'\b(생일|나이|직업|취미|좋아하|싫어하|전공)\w*\b',
            r'\b(살고|거주|주소|집|가족|부모|형제|자매)\w*\b',
            r'\b(이름|성격|특징|습관|버릇|취향)\w*\b',
            r'\b(전화|연락|메일|SNS|계정)\w*\b'
        ]

    def determine_memory_type(self, content: str, context: Dict[str, Any] = None) -> MemoryType:
        """AI 기반 메모리 타입 자동 분류"""
        content_lower = content.lower()
        context = context or {}
        
        # 점수 계산
        episodic_score = 0
        semantic_score = 0
        
        # 1. 시간 표현 검사
        temporal_matches = sum(1 for pattern in self.temporal_patterns if re.search(pattern, content))
        if temporal_matches > 0:
            episodic_score += temporal_matches * 2
            
        # 2. 감정 표현 검사
        emotional_matches = sum(1 for pattern in self.emotional_patterns if re.search(pattern, content))
        if emotional_matches > 0:
            episodic_score += emotional_matches * 3
            
        # 3. 대화 표현 검사
        conversation_matches = sum(1 for pattern in self.conversation_patterns if re.search(pattern, content))
        if conversation_matches > 0:
            episodic_score += conversation_matches * 2
            
        # 4. 사실/지식 표현 검사
        factual_matches = sum(1 for pattern in self.factual_patterns if re.search(pattern, content))
        if factual_matches > 0:
            semantic_score += factual_matches * 2
            
        # 5. 개인 프로필 검사
        profile_matches = sum(1 for pattern in self.profile_patterns if re.search(pattern, content))
        if profile_matches > 0:
            semantic_score += profile_matches * 3
            
        # 6. 컨텍스트 정보 활용
        if context:
            # 대화 맥락이 있으면 episodic 가중치 증가
            if context.get("conversation_id") or context.get("speaker"):
                episodic_score += 2
                
            # 감정 정보가 있으면 episodic 가중치 증가
            if context.get("emotion"):
                episodic_score += 3
                
            # 명시적으로 사실 타입이 지정되면 semantic
            if context.get("fact_type"):
                semantic_score += 5
        
        # 7. 특수 케이스 처리
        # 질문 형태는 대부분 episodic (대화 맥락)
        if re.search(r'\?|뭐|어떻|언제|어디|왜|누구|어느', content):
            episodic_score += 2
            
        # 단정적 서술은 semantic 경향
        if re.search(r'이다$|다$|입니다$|됩니다$', content):
            semantic_score += 1
            
        # 8. 길이 기반 판단 (매우 짧은 텍스트는 episodic 경향)
        if len(content) < 10:
            episodic_score += 1
            
        # 9. 최종 분류
        if episodic_score > semantic_score:
            return MemoryType.EPISODIC
        elif semantic_score > episodic_score:
            return MemoryType.SEMANTIC
        else:
            # 동점인 경우 기본값은 semantic (더 일반적)
            return MemoryType.SEMANTIC
    
    def route_to_collection(self, memory_point: MemoryPoint, user_id: str) -> str:
        """메모리를 적절한 컬렉션으로 라우팅"""
        content = memory_point.metadata.get("text", "")
        context = memory_point.metadata
        
        memory_type = self.determine_memory_type(content, context)
        return memory_type.value
    
    def classify_with_confidence(self, content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """분류 결과와 신뢰도를 함께 반환"""
        context = context or {}
        
        # 각 타입별 점수 계산
        scores = {
            MemoryType.EPISODIC: 0,
            MemoryType.SEMANTIC: 0
        }
        
        # 점수 계산 로직 (위와 동일)
        content_lower = content.lower()
        
        # 시간 표현
        temporal_matches = sum(1 for pattern in self.temporal_patterns if re.search(pattern, content))
        scores[MemoryType.EPISODIC] += temporal_matches * 2
        
        # 감정 표현
        emotional_matches = sum(1 for pattern in self.emotional_patterns if re.search(pattern, content))
        scores[MemoryType.EPISODIC] += emotional_matches * 3
        
        # 대화 표현
        conversation_matches = sum(1 for pattern in self.conversation_patterns if re.search(pattern, content))
        scores[MemoryType.EPISODIC] += conversation_matches * 2
        
        # 사실/지식 표현
        factual_matches = sum(1 for pattern in self.factual_patterns if re.search(pattern, content))
        scores[MemoryType.SEMANTIC] += factual_matches * 2
        
        # 개인 프로필
        profile_matches = sum(1 for pattern in self.profile_patterns if re.search(pattern, content))
        scores[MemoryType.SEMANTIC] += profile_matches * 3
        
        # 최종 분류
        predicted_type = max(scores, key=scores.get)
        total_score = sum(scores.values())
        confidence = scores[predicted_type] / max(total_score, 1)
        
        return {
            "predicted_type": predicted_type,
            "confidence": confidence,
            "scores": scores,
            "features": {
                "temporal_matches": temporal_matches,
                "emotional_matches": emotional_matches,
                "conversation_matches": conversation_matches,
                "factual_matches": factual_matches,
                "profile_matches": profile_matches
            }
        }
    
    def get_classification_explanation(self, content: str, context: Dict[str, Any] = None) -> str:
        """분류 이유를 텍스트로 설명"""
        result = self.classify_with_confidence(content, context)
        features = result["features"]
        predicted_type = result["predicted_type"]
        confidence = result["confidence"]
        
        reasons = []
        
        if features["temporal_matches"] > 0:
            reasons.append(f"시간 표현 {features['temporal_matches']}개")
        if features["emotional_matches"] > 0:
            reasons.append(f"감정 표현 {features['emotional_matches']}개")
        if features["conversation_matches"] > 0:
            reasons.append(f"대화 표현 {features['conversation_matches']}개")
        if features["factual_matches"] > 0:
            reasons.append(f"사실/지식 표현 {features['factual_matches']}개")
        if features["profile_matches"] > 0:
            reasons.append(f"개인 프로필 표현 {features['profile_matches']}개")
        
        reason_text = ", ".join(reasons) if reasons else "기본 규칙"
        
        return (f"{predicted_type.value} 타입으로 분류 "
                f"(신뢰도: {confidence:.2f}) - {reason_text} 감지")