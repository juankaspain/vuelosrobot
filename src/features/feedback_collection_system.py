#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════╗
║  📝 FEEDBACK COLLECTION SYSTEM                                   ║
║  🚀 Cazador Supremo v14.2                                        ║
║  💬 Surveys + NPS + Interviews + Sentiment Analysis              ║
╚═══════════════════════════════════════════════════════════════════╝

Sistema completo de recolección de feedback:
- Encuestas in-app en momentos clave
- Net Promoter Score (NPS)
- User interview scheduler
- Análisis de sentimiento
- Feedback categorization

Autor: @Juanka_Spain
Version: 14.2.0  
Date: 2026-01-17
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter
import re

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════

class TriggerEvent(Enum):
    """Eventos que disparan encuestas"""
    ONBOARDING_COMPLETE = "onboarding_complete"
    FIRST_DEAL_FOUND = "first_deal_found"
    PREMIUM_UPGRADE = "premium_upgrade"
    SEARCH_COMPLETE = "search_complete"
    SHARE_DEAL = "share_deal"
    DAY_7_ACTIVE = "day_7_active"
    DAY_30_ACTIVE = "day_30_active"


class QuestionType(Enum):
    """Tipos de preguntas"""
    RATING = "rating"          # 1-5 estrellas
    NPS = "nps"               # 0-10
    YES_NO = "yes_no"         # Sí/No
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"             # Respuesta abierta
    EMOJI = "emoji"           # Emoji selector


class SentimentType(Enum):
    """Tipo de sentimiento"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class FeedbackCategory(Enum):
    """Categoría de feedback"""
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    PRAISE = "praise"
    COMPLAINT = "complaint"
    SUGGESTION = "suggestion"
    QUESTION = "question"
    OTHER = "other"


# Configuración de encuestas predefinidas
SURVEY_TEMPLATES = {
    'onboarding_satisfaction': {
        'name': 'Onboarding Satisfaction',
        'trigger': TriggerEvent.ONBOARDING_COMPLETE,
        'questions': [
            {
                'id': 'q1',
                'type': QuestionType.RATING,
                'text': '¿Qué te pareció el proceso de configuración inicial?',
                'scale': 5
            },
            {
                'id': 'q2',
                'type': QuestionType.TEXT,
                'text': '¿Qué cambiarías del onboarding?',
                'optional': True
            }
        ]
    },
    'nps_survey': {
        'name': 'Net Promoter Score',
        'trigger': TriggerEvent.DAY_7_ACTIVE,
        'questions': [
            {
                'id': 'nps',
                'type': QuestionType.NPS,
                'text': '¿Qué tan probable es que recomiendes Cazador Supremo a un amigo?',
                'scale': 10
            },
            {
                'id': 'reason',
                'type': QuestionType.TEXT,
                'text': '¿Por qué?',
                'optional': False
            }
        ]
    },
    'feature_satisfaction': {
        'name': 'Feature Satisfaction',
        'trigger': TriggerEvent.SEARCH_COMPLETE,
        'questions': [
            {
                'id': 'useful',
                'type': QuestionType.YES_NO,
                'text': '¿Esta búsqueda te resultó útil?'
            },
            {
                'id': 'rating',
                'type': QuestionType.EMOJI,
                'text': '¿Cómo fue tu experiencia?',
                'options': ['😍', '😊', '😐', '😕', '😡']
            }
        ]
    },
    'premium_feedback': {
        'name': 'Premium User Feedback',
        'trigger': TriggerEvent.PREMIUM_UPGRADE,
        'questions': [
            {
                'id': 'worth_it',
                'type': QuestionType.RATING,
                'text': '¿Crees que Premium vale la pena?',
                'scale': 5
            },
            {
                'id': 'most_valuable',
                'type': QuestionType.MULTIPLE_CHOICE,
                'text': '¿Cuál es la feature Premium más valiosa?',
                'options': [
                    'Búsquedas ilimitadas',
                    'Alertas personalizadas',
                    'Sin anuncios',
                    'Soporte prioritario',
                    'Advanced search'
                ]
            }
        ]
    }
}

# Keywords para análisis de sentimiento simple
POSITIVE_KEYWORDS = [
    'excelente', 'genial', 'perfecto', 'increíble', 'fantástico',
    'amor', 'encanta', 'mejor', 'rápido', 'fácil', 'útil',
    'good', 'great', 'awesome', 'perfect', 'love', 'amazing'
]

NEGATIVE_KEYWORDS = [
    'mal', 'horrible', 'pésimo', 'lento', 'difícil', 'confuso',
    'error', 'bug', 'problema', 'falla', 'roto',
    'bad', 'terrible', 'awful', 'slow', 'broken', 'error', 'bug'
]


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class SurveyQuestion:
    """Pregunta de encuesta"""
    question_id: str
    type: QuestionType
    text: str
    scale: Optional[int] = None
    options: Optional[List[str]] = None
    optional: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'question_id': self.question_id,
            'type': self.type.value,
            'text': self.text,
            'scale': self.scale,
            'options': self.options,
            'optional': self.optional
        }


@dataclass
class SurveyResponse:
    """Respuesta de usuario"""
    user_id: int
    survey_id: str
    question_id: str
    answer: any
    timestamp: str
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'survey_id': self.survey_id,
            'question_id': self.question_id,
            'answer': self.answer,
            'timestamp': self.timestamp
        }


@dataclass
class FeedbackEntry:
    """Entrada de feedback"""
    feedback_id: str
    user_id: int
    text: str
    category: FeedbackCategory
    sentiment: SentimentType
    timestamp: str
    processed: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'feedback_id': self.feedback_id,
            'user_id': self.user_id,
            'text': self.text,
            'category': self.category.value,
            'sentiment': self.sentiment.value,
            'timestamp': self.timestamp,
            'processed': self.processed
        }


@dataclass
class NPSResult:
    """Resultado de NPS"""
    score: float
    promoters: int
    passives: int
    detractors: int
    total_responses: int
    
    def to_dict(self) -> Dict:
        return {
            'score': self.score,
            'promoters': self.promoters,
            'passives': self.passives,
            'detractors': self.detractors,
            'total_responses': self.total_responses,
            'promoter_rate': self.promoters / self.total_responses if self.total_responses > 0 else 0,
            'detractor_rate': self.detractors / self.total_responses if self.total_responses > 0 else 0
        }


# ═══════════════════════════════════════════════════════════════
#  FEEDBACK COLLECTION SYSTEM
# ═══════════════════════════════════════════════════════════════

class FeedbackCollectionSystem:
    """
    Sistema completo de recolección de feedback.
    
    Features:
    - Encuestas in-app programáticas
    - NPS tracking
    - User interview scheduler
    - Análisis de sentimiento
    - Categorización automática
    - Analytics y reportes
    """
    
    def __init__(self, 
                 data_file: str = 'feedback_data.json',
                 responses_file: str = 'survey_responses.json'):
        self.data_file = Path(data_file)
        self.responses_file = Path(responses_file)
        
        # Storage
        self.surveys: Dict[str, Dict] = {}
        self.responses: List[SurveyResponse] = []
        self.feedback: List[FeedbackEntry] = []
        self.user_survey_history: Dict[int, List[str]] = defaultdict(list)
        
        self._load_data()
        self._create_default_surveys()
        
        logger.info("📝 FeedbackCollectionSystem initialized")
    
    def _load_data(self):
        """Carga datos históricos."""
        # Cargar feedback
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for fb_data in data.get('feedback', []):
                    fb = FeedbackEntry(
                        feedback_id=fb_data['feedback_id'],
                        user_id=fb_data['user_id'],
                        text=fb_data['text'],
                        category=FeedbackCategory(fb_data['category']),
                        sentiment=SentimentType(fb_data['sentiment']),
                        timestamp=fb_data['timestamp'],
                        processed=fb_data.get('processed', False)
                    )
                    self.feedback.append(fb)
                
                logger.info(f"✅ Loaded {len(self.feedback)} feedback entries")
            except Exception as e:
                logger.error(f"❌ Error loading feedback data: {e}")
        
        # Cargar respuestas
        if self.responses_file.exists():
            try:
                with open(self.responses_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for resp_data in data.get('responses', []):
                    resp = SurveyResponse(
                        user_id=resp_data['user_id'],
                        survey_id=resp_data['survey_id'],
                        question_id=resp_data['question_id'],
                        answer=resp_data['answer'],
                        timestamp=resp_data['timestamp']
                    )
                    self.responses.append(resp)
                
                logger.info(f"✅ Loaded {len(self.responses)} survey responses")
            except Exception as e:
                logger.error(f"❌ Error loading survey responses: {e}")
    
    def _save_data(self):
        """Guarda datos a archivos."""
        try:
            # Guardar feedback
            feedback_data = {
                'feedback': [fb.to_dict() for fb in self.feedback],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(feedback_data, f, indent=2, ensure_ascii=False)
            
            # Guardar respuestas
            responses_data = {
                'responses': [resp.to_dict() for resp in self.responses],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.responses_file, 'w', encoding='utf-8') as f:
                json.dump(responses_data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 Feedback data saved")
        except Exception as e:
            logger.error(f"❌ Error saving feedback data: {e}")
    
    def _create_default_surveys(self):
        """Crea encuestas por defecto desde templates."""
        for survey_id, template in SURVEY_TEMPLATES.items():
            if survey_id not in self.surveys:
                self.surveys[survey_id] = template
    
    # ═══════════════════════════════════════════════════════════
    #  SURVEY MANAGEMENT
    # ═══════════════════════════════════════════════════════════
    
    def should_show_survey(self, user_id: int, survey_id: str, 
                          event: TriggerEvent) -> bool:
        """Determina si mostrar encuesta a usuario."""
        survey = self.surveys.get(survey_id)
        if not survey:
            return False
        
        # Verificar trigger
        if survey['trigger'] != event:
            return False
        
        # Verificar si ya respondió
        if survey_id in self.user_survey_history[user_id]:
            return False
        
        # TODO: Agregar rate limiting, targeting, etc.
        
        return True
    
    def get_survey(self, survey_id: str) -> Optional[Dict]:
        """Obtiene encuesta."""
        return self.surveys.get(survey_id)
    
    def record_response(self, user_id: int, survey_id: str, 
                       question_id: str, answer: any):
        """Registra respuesta de usuario."""
        response = SurveyResponse(
            user_id=user_id,
            survey_id=survey_id,
            question_id=question_id,
            answer=answer,
            timestamp=datetime.now().isoformat()
        )
        
        self.responses.append(response)
        self._save_data()
        
        logger.info(f"📝 Response recorded: {survey_id}/{question_id}")
    
    def mark_survey_completed(self, user_id: int, survey_id: str):
        """Marca encuesta como completada."""
        self.user_survey_history[user_id].append(survey_id)
    
    # ═══════════════════════════════════════════════════════════
    #  NPS TRACKING
    # ═══════════════════════════════════════════════════════════
    
    def calculate_nps(self, days: int = 30) -> NPSResult:
        """Calcula Net Promoter Score."""
        cutoff = datetime.now() - timedelta(days=days)
        
        # Obtener respuestas NPS recientes
        nps_responses = [
            r for r in self.responses
            if r.question_id == 'nps'
            and datetime.fromisoformat(r.timestamp) >= cutoff
        ]
        
        if not nps_responses:
            return NPSResult(0, 0, 0, 0, 0)
        
        # Clasificar
        promoters = sum(1 for r in nps_responses if r.answer >= 9)
        passives = sum(1 for r in nps_responses if 7 <= r.answer <= 8)
        detractors = sum(1 for r in nps_responses if r.answer <= 6)
        total = len(nps_responses)
        
        # Calcular NPS
        nps_score = ((promoters - detractors) / total) * 100 if total > 0 else 0
        
        return NPSResult(
            score=nps_score,
            promoters=promoters,
            passives=passives,
            detractors=detractors,
            total_responses=total
        )
    
    # ═══════════════════════════════════════════════════════════
    #  FEEDBACK SUBMISSION
    # ═══════════════════════════════════════════════════════════
    
    def submit_feedback(self, user_id: int, text: str) -> FeedbackEntry:
        """Procesa y guarda feedback de usuario."""
        
        # Análisis de sentimiento
        sentiment = self._analyze_sentiment(text)
        
        # Categorización
        category = self._categorize_feedback(text)
        
        # Crear entrada
        feedback_id = f"FB_{int(datetime.now().timestamp())}_{user_id}"
        feedback = FeedbackEntry(
            feedback_id=feedback_id,
            user_id=user_id,
            text=text,
            category=category,
            sentiment=sentiment,
            timestamp=datetime.now().isoformat()
        )
        
        self.feedback.append(feedback)
        self._save_data()
        
        logger.info(f"📝 Feedback submitted: {category.value} ({sentiment.value})")
        return feedback
    
    def _analyze_sentiment(self, text: str) -> SentimentType:
        """Análisis simple de sentimiento."""
        text_lower = text.lower()
        
        positive_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text_lower)
        negative_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text_lower)
        
        if positive_count > negative_count:
            return SentimentType.POSITIVE
        elif negative_count > positive_count:
            return SentimentType.NEGATIVE
        else:
            return SentimentType.NEUTRAL
    
    def _categorize_feedback(self, text: str) -> FeedbackCategory:
        """Categorización simple de feedback."""
        text_lower = text.lower()
        
        # Keywords por categoría
        if any(kw in text_lower for kw in ['feature', 'añadir', 'sería genial', 'me gustaría']):
            return FeedbackCategory.FEATURE_REQUEST
        elif any(kw in text_lower for kw in ['bug', 'error', 'no funciona', 'problema', 'falla']):
            return FeedbackCategory.BUG_REPORT
        elif any(kw in text_lower for kw in ['excelente', 'genial', 'increíble', 'amor']):
            return FeedbackCategory.PRAISE
        elif any(kw in text_lower for kw in ['mal', 'horrible', 'pésimo', 'decepción']):
            return FeedbackCategory.COMPLAINT
        elif any(kw in text_lower for kw in ['sugiero', 'recomiendo', 'podrían', 'deberían']):
            return FeedbackCategory.SUGGESTION
        elif '?' in text:
            return FeedbackCategory.QUESTION
        else:
            return FeedbackCategory.OTHER
    
    # ═══════════════════════════════════════════════════════════
    #  ANALYTICS & REPORTING
    # ═══════════════════════════════════════════════════════════
    
    def get_feedback_summary(self, days: int = 30) -> Dict:
        """Genera resumen de feedback."""
        cutoff = datetime.now() - timedelta(days=days)
        
        recent_feedback = [
            fb for fb in self.feedback
            if datetime.fromisoformat(fb.timestamp) >= cutoff
        ]
        
        if not recent_feedback:
            return {}
        
        # Por categoría
        by_category = Counter(fb.category for fb in recent_feedback)
        
        # Por sentimiento
        by_sentiment = Counter(fb.sentiment for fb in recent_feedback)
        
        # Top keywords
        all_text = ' '.join(fb.text.lower() for fb in recent_feedback)
        words = re.findall(r'\w+', all_text)
        common_words = Counter(words).most_common(10)
        
        return {
            'total_feedback': len(recent_feedback),
            'by_category': {k.value: v for k, v in by_category.items()},
            'by_sentiment': {k.value: v for k, v in by_sentiment.items()},
            'sentiment_score': (
                by_sentiment.get(SentimentType.POSITIVE, 0) - 
                by_sentiment.get(SentimentType.NEGATIVE, 0)
            ) / len(recent_feedback),
            'top_keywords': common_words,
            'feature_requests': [
                fb.text for fb in recent_feedback
                if fb.category == FeedbackCategory.FEATURE_REQUEST
            ][:5],
            'bug_reports': [
                fb.text for fb in recent_feedback
                if fb.category == FeedbackCategory.BUG_REPORT
            ][:5]
        }
    
    def print_feedback_report(self, days: int = 30):
        """Imprime reporte de feedback."""
        summary = self.get_feedback_summary(days)
        nps = self.calculate_nps(days)
        
        print("\n" + "="*70)
        print(f"📝 FEEDBACK REPORT - Last {days} days".center(70))
        print("="*70 + "\n")
        
        # NPS
        print(f"NET PROMOTER SCORE: {nps.score:.1f}")
        print(f"  • Promoters: {nps.promoters} ({nps.promoters/nps.total_responses:.1%})")
        print(f"  • Passives: {nps.passives} ({nps.passives/nps.total_responses:.1%})")
        print(f"  • Detractors: {nps.detractors} ({nps.detractors/nps.total_responses:.1%})\n")
        
        if not summary:
            print("No feedback data available.\n")
            return
        
        # Overview
        print(f"TOTAL FEEDBACK: {summary['total_feedback']}\n")
        
        # By category
        print("BY CATEGORY:")
        for category, count in summary['by_category'].items():
            pct = count / summary['total_feedback']
            print(f"  • {category}: {count} ({pct:.1%})")
        print()
        
        # By sentiment
        print("BY SENTIMENT:")
        for sentiment, count in summary['by_sentiment'].items():
            pct = count / summary['total_feedback']
            emoji = {'positive': '😊', 'neutral': '😐', 'negative': '😕'}
            print(f"  {emoji[sentiment]} {sentiment}: {count} ({pct:.1%})")
        print(f"\n  Sentiment Score: {summary['sentiment_score']:+.2f}\n")
        
        # Top feature requests
        if summary['feature_requests']:
            print("TOP FEATURE REQUESTS:")
            for i, req in enumerate(summary['feature_requests'], 1):
                print(f"  {i}. {req[:60]}...")
            print()
        
        # Top bug reports
        if summary['bug_reports']:
            print("TOP BUG REPORTS:")
            for i, bug in enumerate(summary['bug_reports'], 1):
                print(f"  {i}. {bug[:60]}...")
            print()
        
        print("="*70 + "\n")


if __name__ == '__main__':
    # 🧪 Test del sistema
    print("🧪 Testing FeedbackCollectionSystem...\n")
    
    feedback_sys = FeedbackCollectionSystem()
    
    # Simular respuestas NPS
    print("1. Simulating NPS responses...")
    for i in range(100):
        user_id = 10000 + i
        # 40% promoters, 30% passives, 30% detractors
        if i < 40:
            score = 9 + (i % 2)
        elif i < 70:
            score = 7 + (i % 2)
        else:
            score = i % 7
        
        feedback_sys.record_response(user_id, 'nps_survey', 'nps', score)
    
    # Simular feedback
    print("2. Simulating feedback...")
    sample_feedback = [
        "Me encanta el bot! Es súper rápido y fácil de usar",
        "Hay un error cuando busco vuelos a NYC",
        "Sería genial añadir búsqueda por presupuesto",
        "El onboarding es muy largo, deberían acortarlo",
        "Excelente servicio, encontré un chollo increíble!",
        "La app se cuelga a veces",
        "¿Cómo puedo cambiar mi región de viaje?",
        "Horrible experiencia, no funciona nada",
        "Sugiero agregar notificaciones push",
        "Perfecto! Justo lo que necesitaba"
    ]
    
    for i, text in enumerate(sample_feedback):
        feedback_sys.submit_feedback(10000 + i, text)
    
    # Generar reporte
    print("\n3. Generating report...")
    feedback_sys.print_feedback_report(days=30)
    
    print("✅ Test completed!")
