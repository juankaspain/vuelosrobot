#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  🔄 CONTINUOUS OPTIMIZATION ENGINE                                   ║
║  🚀 Cazador Supremo v14.3                                           ║
║  🤖 AI-Powered Auto-Optimization System                             ║
╚══════════════════════════════════════════════════════════════════════╝

Motor de optimización continua:
- Análisis automático de métricas
- Recomendaciones data-driven
- Auto-expansión de quick actions
- Optimización de premium upsells
- Mejora de share mechanics
- Auto-tuning de performance
- Gestión automática de A/B tests

Autor: @Juanka_Spain
Version: 14.3.0
Date: 2026-01-17
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
#  ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════

class OptimizationArea(Enum):
    """Áreas de optimización"""
    ONBOARDING = "onboarding"
    BUTTONS = "buttons"
    MESSAGES = "messages"
    PREMIUM = "premium"
    SHARING = "sharing"
    PERFORMANCE = "performance"
    FEATURES = "features"


class ActionPriority(Enum):
    """Prioridad de acción"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionStatus(Enum):
    """Estado de acción"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# Quick actions predefinidas (expandidas)
QUICK_ACTIONS_LIBRARY = {
    'scan_favorites': {
        'label': '🔍 Escanear Favoritas',
        'callback': 'quick_scan_favorites',
        'description': 'Escanear tus rutas favoritas',
        'usage_count': 0
    },
    'last_deals': {
        'label': '🔥 Últimos Chollos',
        'callback': 'quick_last_deals',
        'description': 'Ver chollos más recientes',
        'usage_count': 0
    },
    'watchlist_alerts': {
        'label': '🔔 Mis Alertas',
        'callback': 'quick_watchlist',
        'description': 'Gestionar alertas activas',
        'usage_count': 0
    },
    'daily_reward': {
        'label': '🎁 Reward Diario',
        'callback': 'quick_daily',
        'description': 'Reclamar reward del día',
        'usage_count': 0
    },
    'premium_trial': {
        'label': '💎 Probar Premium',
        'callback': 'quick_premium_trial',
        'description': 'Activar prueba gratuita',
        'usage_count': 0
    },
    'invite_friend': {
        'label': '👥 Invitar Amigo',
        'callback': 'quick_invite',
        'description': 'Ganar bonus por referido',
        'usage_count': 0
    },
    'search_flexible': {
        'label': '📅 Búsqueda Flexible',
        'callback': 'quick_search_flex',
        'description': 'Calendario de precios',
        'usage_count': 0
    },
    'search_budget': {
        'label': '💰 Por Presupuesto',
        'callback': 'quick_search_budget',
        'description': 'Destinos en tu presupuesto',
        'usage_count': 0
    },
    'my_stats': {
        'label': '📊 Mis Stats',
        'callback': 'quick_profile',
        'description': 'Ver tu perfil y logros',
        'usage_count': 0
    },
    'leaderboard': {
        'label': '🏆 Rankings',
        'callback': 'quick_leaderboard',
        'description': 'Ver tabla de posiciones',
        'usage_count': 0
    },
    'share_last_deal': {
        'label': '📤 Compartir Chollo',
        'callback': 'quick_share_deal',
        'description': 'Compartir último chollo',
        'usage_count': 0
    },
    'help_support': {
        'label': '❓ Ayuda',
        'callback': 'quick_help',
        'description': 'Obtener ayuda rápida',
        'usage_count': 0
    }
}


# Premium upsell contexts
PREMIUM_UPSELL_CONTEXTS = {
    'scan_limit': {
        'trigger': 'daily_scan_limit_reached',
        'message': (
            "🔥 *¡Has alcanzado tu límite de búsquedas gratis hoy!*\n\n"
            "Con Premium obtienes:\n"
            "✅ Búsquedas ilimitadas\n"
            "✅ Alertas personalizadas\n"
            "✅ Sin anuncios\n"
            "✅ Soporte prioritario\n\n"
            "💎 *Upgrade desde €4.99/mes*"
        ),
        'cta': 'Upgrade Now',
        'conversion_rate': 0.0
    },
    'deal_found': {
        'trigger': 'high_value_deal_found',
        'message': (
            "🎉 *¡Encontramos un chollo increíble para ti!*\n\n"
            "Con Premium nunca te perderás chollos como este:\n"
            "✅ Alertas instantáneas\n"
            "✅ Acceso 24h antes que free users\n"
            "✅ Chollos exclusivos\n\n"
            "💎 *Prueba gratis 7 días*"
        ),
        'cta': 'Start Free Trial',
        'conversion_rate': 0.0
    },
    'advanced_search': {
        'trigger': 'advanced_search_attempt',
        'message': (
            "🚀 *Búsquedas Avanzadas = Premium Feature*\n\n"
            "Desbloquea:\n"
            "✅ Calendario flexible\n"
            "✅ Multi-ciudad\n"
            "✅ Búsqueda por presupuesto\n"
            "✅ Filtros avanzados\n\n"
            "💎 *Solo €4.99/mes*"
        ),
        'cta': 'Unlock Now',
        'conversion_rate': 0.0
    },
    'week_1_active': {
        'trigger': 'day_7_active_user',
        'message': (
            "🎊 *¡Llevas 1 semana con nosotros!*\n\n"
            "Te regalamos 20% OFF en Premium:\n"
            "✅ Todas las features PRO\n"
            "✅ Sin límites\n"
            "✅ Soporte VIP\n\n"
            "💎 *Upgrade con 20% OFF*"
        ),
        'cta': 'Claim Discount',
        'conversion_rate': 0.0
    },
    'share_deal': {
        'trigger': 'deal_share_action',
        'message': (
            "📤 *¡Compartir chollos es más fácil con Premium!*\n\n"
            "Premium incluye:\n"
            "✅ Links personalizados\n"
            "✅ Bonus por compartir\n"
            "✅ Stats de shares\n\n"
            "💎 *Upgrade ahora*"
        ),
        'cta': 'Go Premium',
        'conversion_rate': 0.0
    }
}


# Share mechanics variations
SHARE_MECHANICS = {
    'social_proof': {
        'enabled': True,
        'message_template': (
            "🔥 *¡{user_name} encontró un chollo increíble!*\n\n"
            "{deal_details}\n\n"
            "👥 Ya lo compartieron {share_count} personas\n"
            "⏰ Expira en {time_left}\n\n"
            "👉 Usa Cazador Supremo tú también: {bot_link}"
        )
    },
    'gamification': {
        'enabled': True,
        'rewards': {
            'share_1': {'coins': 50, 'message': '🎁 +50 coins por tu primer share!'},
            'share_5': {'coins': 100, 'message': '🎉 +100 coins! 5 shares completados!'},
            'share_10': {'coins': 200, 'badge': 'Influencer', 'message': '🏆 Badge Influencer desbloqueado!'},
        }
    },
    'viral_loop': {
        'enabled': True,
        'incentive': '💎 Invita 3 amigos = 1 mes Premium GRATIS',
        'tracking': True
    },
    'one_click_share': {
        'enabled': True,
        'platforms': ['whatsapp', 'telegram', 'twitter', 'facebook'],
        'templates': {
            'whatsapp': '🔥 Mira este chollo: {deal_summary} - {link}',
            'telegram': '✈️ Chollo encontrado: {deal_summary}\n{link}',
            'twitter': '🎉 Vuelo a {destination} por solo {price}! {link} #Chollos #Vuelos',
            'facebook': 'Encontré este increíble chollo de vuelos 🔥 {deal_summary}'
        }
    }
}


# ═══════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class OptimizationAction:
    """Acción de optimización"""
    action_id: str
    area: OptimizationArea
    priority: ActionPriority
    title: str
    description: str
    expected_impact: str
    status: ActionStatus
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'action_id': self.action_id,
            'area': self.area.value,
            'priority': self.priority.value,
            'title': self.title,
            'description': self.description,
            'expected_impact': self.expected_impact,
            'status': self.status.value,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'result': self.result
        }


@dataclass
class OptimizationInsight:
    """Insight de optimización"""
    insight_id: str
    area: OptimizationArea
    title: str
    description: str
    data: Dict
    recommendations: List[str]
    created_at: str
    
    def to_dict(self) -> Dict:
        return {
            'insight_id': self.insight_id,
            'area': self.area.value,
            'title': self.title,
            'description': self.description,
            'data': self.data,
            'recommendations': self.recommendations,
            'created_at': self.created_at
        }


# ═══════════════════════════════════════════════════════════════════════
#  CONTINUOUS OPTIMIZATION ENGINE
# ═══════════════════════════════════════════════════════════════════════

class ContinuousOptimizationEngine:
    """
    Motor de optimización continua.
    
    Features:
    - Análisis automático de métricas
    - Generación de insights
    - Recomendaciones data-driven
    - Auto-expansión de features
    - Gestión de A/B tests
    - Optimización de conversiones
    """
    
    def __init__(self, 
                 monitoring_system=None,
                 ab_testing_system=None,
                 feedback_system=None,
                 data_file: str = 'optimization_data.json'):
        self.monitoring = monitoring_system
        self.ab_testing = ab_testing_system
        self.feedback = feedback_system
        self.data_file = Path(data_file)
        
        # Storage
        self.actions: List[OptimizationAction] = []
        self.insights: List[OptimizationInsight] = []
        self.quick_actions = QUICK_ACTIONS_LIBRARY.copy()
        self.premium_upsells = PREMIUM_UPSELL_CONTEXTS.copy()
        self.share_mechanics = SHARE_MECHANICS.copy()
        
        self._load_data()
        
        logger.info("🔄 ContinuousOptimizationEngine initialized")
    
    def _load_data(self):
        """Carga datos de optimización."""
        if not self.data_file.exists():
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cargar actions
            for action_data in data.get('actions', []):
                action = OptimizationAction(
                    action_id=action_data['action_id'],
                    area=OptimizationArea(action_data['area']),
                    priority=ActionPriority(action_data['priority']),
                    title=action_data['title'],
                    description=action_data['description'],
                    expected_impact=action_data['expected_impact'],
                    status=ActionStatus(action_data['status']),
                    created_at=action_data['created_at'],
                    completed_at=action_data.get('completed_at'),
                    result=action_data.get('result')
                )
                self.actions.append(action)
            
            # Cargar insights
            for insight_data in data.get('insights', []):
                insight = OptimizationInsight(
                    insight_id=insight_data['insight_id'],
                    area=OptimizationArea(insight_data['area']),
                    title=insight_data['title'],
                    description=insight_data['description'],
                    data=insight_data['data'],
                    recommendations=insight_data['recommendations'],
                    created_at=insight_data['created_at']
                )
                self.insights.append(insight)
            
            # Cargar configuraciones
            if 'quick_actions' in data:
                self.quick_actions.update(data['quick_actions'])
            if 'premium_upsells' in data:
                self.premium_upsells.update(data['premium_upsells'])
            
            logger.info(f"✅ Loaded {len(self.actions)} actions, {len(self.insights)} insights")
        except Exception as e:
            logger.error(f"❌ Error loading optimization data: {e}")
    
    def _save_data(self):
        """Guarda datos de optimización."""
        try:
            data = {
                'actions': [a.to_dict() for a in self.actions],
                'insights': [i.to_dict() for i in self.insights],
                'quick_actions': self.quick_actions,
                'premium_upsells': self.premium_upsells,
                'share_mechanics': self.share_mechanics,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 Optimization data saved")
        except Exception as e:
            logger.error(f"❌ Error saving optimization data: {e}")
    
    # ═══════════════════════════════════════════════════════════════════
    #  ANALYSIS & INSIGHTS
    # ═══════════════════════════════════════════════════════════════════
    
    def analyze_metrics(self) -> List[OptimizationInsight]:
        """Analiza métricas y genera insights."""
        insights = []
        
        if not self.monitoring:
            return insights
        
        # Analizar onboarding
        onb_insights = self._analyze_onboarding()
        insights.extend(onb_insights)
        
        # Analizar botones
        btn_insights = self._analyze_buttons()
        insights.extend(btn_insights)
        
        # Analizar premium conversion
        premium_insights = self._analyze_premium()
        insights.extend(premium_insights)
        
        # Analizar performance
        perf_insights = self._analyze_performance()
        insights.extend(perf_insights)
        
        # Guardar insights
        self.insights.extend(insights)
        self._save_data()
        
        return insights
    
    def _analyze_onboarding(self) -> List[OptimizationInsight]:
        """Analiza onboarding."""
        insights = []
        
        completion_rate = self.monitoring.get_onboarding_completion_rate(hours=24)
        avg_duration = self.monitoring._get_avg_metric('onboarding.total_duration', hours=24)
        
        # Insight 1: Low completion rate
        if completion_rate < 0.70:
            insight = OptimizationInsight(
                insight_id=f"INS_{int(datetime.now().timestamp())}_ONB_COMPLETION",
                area=OptimizationArea.ONBOARDING,
                title="Low Onboarding Completion Rate",
                description=f"Only {completion_rate:.1%} of users complete onboarding",
                data={'completion_rate': completion_rate, 'target': 0.70},
                recommendations=[
                    "Test 2-step vs 3-step flow (A/B test already running)",
                    "Reduce text length in each step",
                    "Add progress indicators",
                    "Increase welcome bonus to 250 coins",
                    "Make skip button less prominent"
                ],
                created_at=datetime.now().isoformat()
            )
            insights.append(insight)
        
        # Insight 2: Slow TTFV
        if avg_duration > 90:
            insight = OptimizationInsight(
                insight_id=f"INS_{int(datetime.now().timestamp())}_ONB_TTFV",
                area=OptimizationArea.ONBOARDING,
                title="Time To First Value Exceeds Target",
                description=f"Average onboarding takes {avg_duration:.0f}s (target: <90s)",
                data={'avg_duration': avg_duration, 'target': 90},
                recommendations=[
                    "Reduce number of steps",
                    "Pre-fill common options",
                    "Parallelize API calls",
                    "Cache initial data"
                ],
                created_at=datetime.now().isoformat()
            )
            insights.append(insight)
        
        return insights
    
    def _analyze_buttons(self) -> List[OptimizationInsight]:
        """Analiza performance de botones."""
        insights = []
        
        overall_ctr = self.monitoring.get_button_click_rate(hours=24)
        top_buttons = self.monitoring.get_top_buttons(hours=24, limit=10)
        
        # Insight: Low CTR
        if overall_ctr < 0.60:
            underperforming = [btn for btn, clicks in top_buttons if clicks < 50]
            
            insight = OptimizationInsight(
                insight_id=f"INS_{int(datetime.now().timestamp())}_BTN_CTR",
                area=OptimizationArea.BUTTONS,
                title="Low Button Click-Through Rate",
                description=f"Overall CTR is {overall_ctr:.1%} (target: >60%)",
                data={
                    'overall_ctr': overall_ctr,
                    'underperforming_buttons': underperforming[:5]
                },
                recommendations=[
                    "Test different CTA copy",
                    "Add emoji to button labels",
                    "Improve button positioning",
                    "Use contrasting colors",
                    "Add urgency indicators"
                ],
                created_at=datetime.now().isoformat()
            )
            insights.append(insight)
        
        return insights
    
    def _analyze_premium(self) -> List[OptimizationInsight]:
        """Analiza conversión premium."""
        insights = []
        
        # Analizar conversión por contexto
        best_context = None
        best_rate = 0.0
        
        for context_id, context in self.premium_upsells.items():
            if context['conversion_rate'] > best_rate:
                best_rate = context['conversion_rate']
                best_context = context_id
        
        if best_context and best_rate > 0.10:
            insight = OptimizationInsight(
                insight_id=f"INS_{int(datetime.now().timestamp())}_PREMIUM_CONTEXT",
                area=OptimizationArea.PREMIUM,
                title="High-Converting Premium Context Found",
                description=f"{best_context} converts at {best_rate:.1%}",
                data={'best_context': best_context, 'conversion_rate': best_rate},
                recommendations=[
                    f"Show {best_context} upsell more frequently",
                    "Apply similar messaging to other contexts",
                    "A/B test variations of winning message"
                ],
                created_at=datetime.now().isoformat()
            )
            insights.append(insight)
        
        return insights
    
    def _analyze_performance(self) -> List[OptimizationInsight]:
        """Analiza performance."""
        insights = []
        
        avg_response = self.monitoring.get_avg_response_time(hours=24)
        p95_response = self.monitoring.get_p95_response_time(hours=24)
        
        if avg_response > 1000:
            insight = OptimizationInsight(
                insight_id=f"INS_{int(datetime.now().timestamp())}_PERF_RESPONSE",
                area=OptimizationArea.PERFORMANCE,
                title="Slow Response Times Detected",
                description=f"Avg: {avg_response:.0f}ms, P95: {p95_response:.0f}ms",
                data={'avg_response': avg_response, 'p95_response': p95_response},
                recommendations=[
                    "Enable caching for frequent queries",
                    "Optimize database queries",
                    "Add CDN for static assets",
                    "Implement async operations"
                ],
                created_at=datetime.now().isoformat()
            )
            insights.append(insight)
        
        return insights
    
    # ═══════════════════════════════════════════════════════════════════
    #  ACTION GENERATION & MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════
    
    def generate_actions(self) -> List[OptimizationAction]:
        """Genera acciones de optimización desde insights."""
        actions = []
        
        # Generar desde insights recientes
        recent_insights = [i for i in self.insights 
                          if datetime.fromisoformat(i.created_at) > datetime.now() - timedelta(days=1)]
        
        for insight in recent_insights:
            for i, rec in enumerate(insight.recommendations[:2]):  # Top 2 recomendaciones
                action = OptimizationAction(
                    action_id=f"ACT_{int(datetime.now().timestamp())}_{i}",
                    area=insight.area,
                    priority=self._determine_priority(insight),
                    title=rec,
                    description=f"Based on: {insight.title}",
                    expected_impact=self._estimate_impact(insight, rec),
                    status=ActionStatus.PENDING,
                    created_at=datetime.now().isoformat()
                )
                actions.append(action)
        
        self.actions.extend(actions)
        self._save_data()
        
        return actions
    
    def _determine_priority(self, insight: OptimizationInsight) -> ActionPriority:
        """Determina prioridad de acción."""
        # Basado en área e impacto
        if insight.area == OptimizationArea.ONBOARDING:
            return ActionPriority.CRITICAL
        elif insight.area == OptimizationArea.PREMIUM:
            return ActionPriority.HIGH
        elif insight.area == OptimizationArea.PERFORMANCE:
            return ActionPriority.HIGH
        else:
            return ActionPriority.MEDIUM
    
    def _estimate_impact(self, insight: OptimizationInsight, recommendation: str) -> str:
        """Estima impacto de recomendación."""
        if insight.area == OptimizationArea.ONBOARDING:
            return "+5-10% completion rate"
        elif insight.area == OptimizationArea.BUTTONS:
            return "+10-15% CTR"
        elif insight.area == OptimizationArea.PREMIUM:
            return "+2-5% conversion"
        elif insight.area == OptimizationArea.PERFORMANCE:
            return "-30-50% response time"
        else:
            return "Moderate improvement"
    
    # ═══════════════════════════════════════════════════════════════════
    #  AUTO-OPTIMIZATION
    # ═══════════════════════════════════════════════════════════════════
    
    def auto_optimize_quick_actions(self):
        """Optimiza quick actions basado en uso."""
        # Obtener top botones
        if not self.monitoring:
            return
        
        top_buttons = self.monitoring.get_top_buttons(hours=168, limit=20)  # Última semana
        
        # Identificar quick actions con bajo uso
        low_usage = {k: v for k, v in self.quick_actions.items() 
                    if v['usage_count'] < 10}
        
        # Reemplazar con versiones de top buttons
        for button_id, _ in top_buttons[:4]:
            if button_id not in [qa['callback'] for qa in self.quick_actions.values()]:
                # Agregar como quick action si no existe
                action_id = f"quick_{button_id}"
                if action_id not in self.quick_actions:
                    self.quick_actions[action_id] = {
                        'label': f"⚡ {button_id.replace('_', ' ').title()}",
                        'callback': button_id,
                        'description': f"Quick access to {button_id}",
                        'usage_count': 0
                    }
        
        self._save_data()
        logger.info(f"🔄 Quick actions optimized: {len(self.quick_actions)} total")
    
    def auto_optimize_premium_upsells(self):
        """Optimiza premium upsells basado en conversión."""
        # Encontrar mejor contexto
        best = max(self.premium_upsells.items(), 
                  key=lambda x: x[1]['conversion_rate'])
        
        best_context, best_data = best
        
        if best_data['conversion_rate'] > 0.05:
            # Aumentar frecuencia del mejor contexto
            logger.info(f"💎 Best premium context: {best_context} ({best_data['conversion_rate']:.1%})")
            
            # TODO: Ajustar frecuencia de display
    
    def auto_manage_ab_tests(self):
        """Gestiona A/B tests automáticamente."""
        if not self.ab_testing:
            return
        
        for exp_id, experiment in self.ab_testing.experiments.items():
            if experiment.status.value != 'running':
                continue
            
            # Detectar winner
            winner = self.ab_testing.detect_winner(exp_id)
            
            if winner:
                # Auto-rollout
                self.ab_testing.rollout_winner(exp_id, winner)
                logger.info(f"🏆 Auto-rolled out winner for {exp_id}: {winner}")
                
                # Crear action
                action = OptimizationAction(
                    action_id=f"ACT_{int(datetime.now().timestamp())}_ROLLOUT",
                    area=OptimizationArea.FEATURES,
                    priority=ActionPriority.HIGH,
                    title=f"Rollout A/B test winner: {exp_id}",
                    description=f"Winner variant '{winner}' rolled out automatically",
                    expected_impact="Improved metrics based on test results",
                    status=ActionStatus.COMPLETED,
                    created_at=datetime.now().isoformat(),
                    completed_at=datetime.now().isoformat(),
                    result=f"Successfully rolled out {winner}"
                )
                self.actions.append(action)
        
        self._save_data()
    
    def auto_tune_performance(self):
        """Auto-tunea performance basado en métricas."""
        if not self.monitoring:
            return
        
        avg_response = self.monitoring.get_avg_response_time(hours=24)
        
        recommendations = []
        
        if avg_response > 1000:
            recommendations.append("Enable aggressive caching")
            recommendations.append("Optimize slow queries")
        
        if recommendations:
            action = OptimizationAction(
                action_id=f"ACT_{int(datetime.now().timestamp())}_PERF",
                area=OptimizationArea.PERFORMANCE,
                priority=ActionPriority.HIGH,
                title="Auto-tune performance",
                description="Automated performance optimizations",
                expected_impact="-30% response time",
                status=ActionStatus.PENDING,
                created_at=datetime.now().isoformat()
            )
            self.actions.append(action)
            self._save_data()
    
    # ═══════════════════════════════════════════════════════════════════
    #  REPORTING
    # ═══════════════════════════════════════════════════════════════════
    
    def generate_optimization_report(self) -> Dict:
        """Genera reporte de optimización."""
        # Recent insights
        recent_insights = [i for i in self.insights
                          if datetime.fromisoformat(i.created_at) > datetime.now() - timedelta(days=7)]
        
        # Pending actions
        pending_actions = [a for a in self.actions if a.status == ActionStatus.PENDING]
        
        # Completed actions
        completed_actions = [a for a in self.actions if a.status == ActionStatus.COMPLETED]
        
        return {
            'insights': {
                'total': len(self.insights),
                'recent': len(recent_insights),
                'by_area': self._count_by_area(recent_insights)
            },
            'actions': {
                'total': len(self.actions),
                'pending': len(pending_actions),
                'completed': len(completed_actions),
                'by_priority': self._count_by_priority(pending_actions)
            },
            'quick_actions': {
                'total': len(self.quick_actions),
                'most_used': sorted(
                    self.quick_actions.items(),
                    key=lambda x: x[1]['usage_count'],
                    reverse=True
                )[:5]
            },
            'premium_upsells': {
                'contexts': len(self.premium_upsells),
                'best_performing': max(
                    self.premium_upsells.items(),
                    key=lambda x: x[1]['conversion_rate']
                )[0] if self.premium_upsells else None
            }
        }
    
    def _count_by_area(self, insights: List[OptimizationInsight]) -> Dict:
        """Cuenta insights por área."""
        counts = defaultdict(int)
        for insight in insights:
            counts[insight.area.value] += 1
        return dict(counts)
    
    def _count_by_priority(self, actions: List[OptimizationAction]) -> Dict:
        """Cuenta actions por prioridad."""
        counts = defaultdict(int)
        for action in actions:
            counts[action.priority.value] += 1
        return dict(counts)
    
    def print_optimization_report(self):
        """Imprime reporte de optimización."""
        report = self.generate_optimization_report()
        
        print("\n" + "="*70)
        print("🔄 CONTINUOUS OPTIMIZATION REPORT".center(70))
        print("="*70 + "\n")
        
        # Insights
        print("INSIGHTS GENERATED:")
        print(f"  • Total: {report['insights']['total']}")
        print(f"  • Recent (7d): {report['insights']['recent']}")
        print(f"  • By Area:")
        for area, count in report['insights']['by_area'].items():
            print(f"    - {area}: {count}")
        print()
        
        # Actions
        print("OPTIMIZATION ACTIONS:")
        print(f"  • Total: {report['actions']['total']}")
        print(f"  • Pending: {report['actions']['pending']}")
        print(f"  • Completed: {report['actions']['completed']}")
        print(f"  • By Priority:")
        for priority, count in report['actions']['by_priority'].items():
            print(f"    - {priority}: {count}")
        print()
        
        # Quick Actions
        print("QUICK ACTIONS:")
        print(f"  • Total: {report['quick_actions']['total']}")
        print(f"  • Most Used:")
        for action_id, data in report['quick_actions']['most_used']:
            print(f"    - {action_id}: {data['usage_count']} uses")
        print()
        
        # Premium
        if report['premium_upsells']['best_performing']:
            print("PREMIUM OPTIMIZATION:")
            print(f"  • Best Context: {report['premium_upsells']['best_performing']}")
            best_data = self.premium_upsells[report['premium_upsells']['best_performing']]
            print(f"  • Conversion Rate: {best_data['conversion_rate']:.1%}")
        print()
        
        print("="*70 + "\n")


if __name__ == '__main__':
    # 🧪 Test del engine
    print("🧪 Testing ContinuousOptimizationEngine...\n")
    
    engine = ContinuousOptimizationEngine()
    
    print("1. Generating insights...")
    # Simular algunos insights
    insight = OptimizationInsight(
        insight_id="INS_TEST_1",
        area=OptimizationArea.ONBOARDING,
        title="Test Insight",
        description="Testing optimization engine",
        data={'test': True},
        recommendations=["Test recommendation 1", "Test recommendation 2"],
        created_at=datetime.now().isoformat()
    )
    engine.insights.append(insight)
    
    print("2. Generating actions...")
    actions = engine.generate_actions()
    print(f"   Generated {len(actions)} actions")
    
    print("\n3. Optimization report:")
    engine.print_optimization_report()
    
    print("\n✅ Test completed!")
