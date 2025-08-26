"""
메모리 분류 서비스
- 단일 책임: 메모리 분류만 담당
- 비즈니스 로직을 분류기에서 서비스로 이동
"""
from typing import Dict, Any, List
from src.config.settings import MemoryType
from src.service.memory_classifier import MemoryClassifier


class MemoryClassificationService:
    """메모리 분류 비즈니스 로직 서비스"""
    
    def __init__(self):
        self.classifier = MemoryClassifier()
    
    def classify_memory(self, text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """메모리 자동 분류"""
        metadata = metadata or {}
        
        # 기본 분류 실행
        classification = self.classifier.classify_with_confidence(text, metadata)
        
        # 비즈니스 로직 적용
        refined_classification = self._apply_business_rules(text, metadata, classification)
        
        return {
            "predicted_type": refined_classification["type"],
            "confidence": refined_classification["confidence"],
            "explanation": self._generate_explanation(refined_classification),
            "features": classification["features"],
            "business_rules_applied": refined_classification.get("rules_applied", [])
        }
    
    def _apply_business_rules(self, text: str, metadata: Dict[str, Any], 
                            classification: Dict[str, Any]) -> Dict[str, Any]:
        """비즈니스 규칙 적용"""
        predicted_type = classification["predicted_type"]
        confidence = classification["confidence"]
        rules_applied = []
        
        # 규칙 1: 매우 짧은 텍스트 (3단어 이하)는 대부분 Episodic
        if len(text.split()) <= 3 and confidence < 0.7:
            predicted_type = MemoryType.EPISODIC
            confidence = max(confidence, 0.7)
            rules_applied.append("short_text_rule")
        
        # 규칙 2: 명시적 사실 타입 메타데이터가 있으면 Semantic 강제
        if metadata.get("fact_type"):
            predicted_type = MemoryType.SEMANTIC
            confidence = 0.95
            rules_applied.append("explicit_fact_type")
        
        # 규칙 3: 대화 ID나 화자 정보가 있으면 Episodic 가중치 증가
        if metadata.get("conversation_id") or metadata.get("speaker"):
            if predicted_type == MemoryType.EPISODIC:
                confidence = min(confidence + 0.2, 1.0)
            else:
                # Semantic에서 Episodic으로 재분류 고려
                if confidence < 0.8:
                    predicted_type = MemoryType.EPISODIC
                    confidence = 0.75
            rules_applied.append("conversation_context")
        
        # 규칙 4: 감정 정보가 강하게 포함된 경우 Episodic
        emotion_score = classification["features"].get("emotional_matches", 0)
        if emotion_score >= 2 and predicted_type == MemoryType.SEMANTIC:
            if confidence < 0.8:
                predicted_type = MemoryType.EPISODIC
                confidence = 0.8
            rules_applied.append("high_emotion_rule")
        
        # 규칙 5: 개인 프로필 정보는 확실히 Semantic
        profile_score = classification["features"].get("profile_matches", 0)
        if profile_score >= 2:
            predicted_type = MemoryType.SEMANTIC
            confidence = min(confidence + 0.3, 1.0)
            rules_applied.append("profile_information")
        
        return {
            "type": predicted_type,
            "confidence": confidence,
            "rules_applied": rules_applied,
            "original_classification": classification["predicted_type"]
        }
    
    def _generate_explanation(self, classification: Dict[str, Any]) -> str:
        """분류 설명 생성"""
        type_name = classification["type"].value
        confidence = classification["confidence"]
        rules = classification.get("rules_applied", [])
        
        explanation = f"{type_name} 메모리로 분류됨 (신뢰도: {confidence:.2f})"
        
        if rules:
            rule_descriptions = {
                "short_text_rule": "짧은 텍스트 규칙 적용",
                "explicit_fact_type": "명시적 사실 타입 지정",
                "conversation_context": "대화 맥락 정보 고려",
                "high_emotion_rule": "강한 감정 표현 감지",
                "profile_information": "개인 프로필 정보 감지"
            }
            
            applied_rules = [rule_descriptions.get(rule, rule) for rule in rules]
            explanation += f" - {', '.join(applied_rules)}"
        
        return explanation
    
    def batch_classify(self, texts: List[str], metadata_list: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """배치 분류"""
        if metadata_list is None:
            metadata_list = [{}] * len(texts)
        
        return [
            self.classify_memory(text, metadata) 
            for text, metadata in zip(texts, metadata_list)
        ]
    
    def get_classification_confidence_threshold(self) -> float:
        """분류 신뢰도 임계값 반환"""
        return 0.6  # 60% 이상 신뢰도에서 자동 분류 수용
    
    def should_request_manual_classification(self, classification: Dict[str, Any]) -> bool:
        """수동 분류 요청 여부 판단"""
        return classification["confidence"] < self.get_classification_confidence_threshold()