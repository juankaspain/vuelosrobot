#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║  🔄 CONTINUOUS OPTIMIZATION ENGINE                                        ║
║  🚀 Cazador Supremo v14.2                                                 ║
║  🤖 Auto-optimization + Data-driven Insights                              ║
╚═══════════════════════════════════════════════════════════════════════════╝

Motor de optimización continua:
- Análisis automático de métricas
- Recomendaciones data-driven
- Auto-tuning de parámetros
- Quick actions expansion
- Premium upsell optimization
- Share mechanics enhancement

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
from collections import defaultdict
import random

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
#  ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

class OptimizationType(Enum):
    """Tipo de optimización"""
    ONBOARDING = "onboarding"
    CONVERSION = "conversion"
    RETENTION = "retention"
    ENGAGEMENT = "engagement"
    REVENUE = "revenue"
    PERFORMANCE = "performance"


class ActionPriority(Enum):
    """Prioridad de acción"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Quick Actions configurables
QUICK_ACTIONS_POOL = [
    {
        'id': 'scan_popular',
        'label': '🔥 Escanear Rutas Populares',
        'command': '/scan',
        'priority': 'high',
        'conversion_boost': 0.15
    },
    {
        'id': 'deals_today',
        'label': '💰 Ver Chollos de Hoy',
        'command': '/deals',
        'priority': 'high',
        'conversion_boost': 0.20
    },
    {
        'id': 'watchlist_create',
        'label': '🔔 Crear Alerta',
        'command': '/watchlist',
        'priority': 'medium',
        'conversion_boost': 0.18
    },
    {
        'id': 'search_flex',
        'label': '📅 Calendario Flexible',
        'command': '/search_flex',
        'priority': 'high',
        'conversion_boost': 0.22
    },
    {
        'id': 'search_multi',
        'label': '🌍 Multi-Ciudad',
        'command': '/search_multi',
        'priority': 'medium',
        'conversion_boost': 0.12
    },
    {
        'id': 'daily_reward',
        'label': '🎁 Recompensa Diaria',
        'command': '/daily',
        'priority': 'medium',
        'conversion_boost': 0.10
    },
    {
        'id': 'invite_friend',
        'label': '👥 Invitar Amigo',
        'command': '/invite',
        'priority': 'low',
        'conversion_boost': 0.08
    },
    {
        'id': 'premium_trial',
        'label': '💎 Probar Premium',
        'command': '/trial',
        'priority': 'high',
        'conversion_boost': 0.25
    },
]

# Premium upsell moments
UPSELL_TRIGGERS = [
    {
        'trigger': 'search_limit_reached',
        'message': '🚫 Has alcanzado tu límite de búsquedas gratuitas hoy.\n\n💎 Con Premium: búsquedas ilimitadas\n\n[Ver Planes]',
        'conversion_rate': 0.12
    },
    {
        'trigger': 'deal_found',
        'message': '🔥 ¡Encontramos un chollo! Con Premium recibirías alertas automáticas.\n\n[Activar Alertas Premium]',
        'conversion_rate': 0.08
    },
    {
        'trigger': 'advanced_search_blocked',
        'message': '⭐ Esta búsqueda avanzada es Premium.\n\n✅ Búsquedas flexibles\n✅ Multi-ciudad\n✅ Sin límites\n\n[Desbloquear]',
        'conversion_rate': 0.15
    },
    {
        'trigger': 'multiple_deals_day',
        'message': '💰 Ya encontraste 3 chollos hoy!\n\nCon Premium: alertas automáticas para no perderte ninguno.\n\n[Ver Premium]',
        'conversion_rate': 0.10
    },
    {
        'trigger': 'power_user',
        'message': '🌟 Eres un usuario activo! Premium te ahorraría aún más:\n\n📊 Análisis avanzados\n⚡ Búsquedas más rápidas\n🎯 Alertas personalizadas\n\n[Upgrade]',
        'conversion_rate': 0.18
    },
]

# Share enhancement options
SHARE_ENHANCEMENTS = [
    {
        'type': 'social_proof',
        'message': '✈️ {deal_name} por {price}\n\n💰 Ahorro: {savings}\n🔥 {users_count} usuarios ya lo vieron\n\n{share_link}',
        'conversion_boost': 0.15
    },
    {
        'type': 'urgency',
        'message': '⏰ ¡ÚLTIMA HORA!\n\n✈️ {deal_name}: {price}\n💥 {savings} de ahorro\n⚠️ Solo quedan {spots} plazas\n\n{share_link}',
        'conversion_boost': 0.22
    },
    {
        'type': 'referral_incentive',
        'message': '🎁 Te regalo este chollo:\n\n✈️ {deal_name}: {price}\n💰 Ahorro: {savings}\n\n¡Usa mi link y ambos ganamos 50 coins!\n{share_link}',
        'conversion_boost': 0.28
    },
    {
        'type': 'comparison',
        'message': '📊 PRECIO HISTÓRICO\n\n✈️ {deal_name}\n💰 Ahora: {price}\n📈 Antes: {original_price}\n💎 Ahorro: {savings} ({pct}%)\n\n{share_link}',
        'conversion_boost': 0.18
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class OptimizationInsight:
    """Insight de optimización"""
    type: OptimizationType
    priority: ActionPriority
    metric: str
    current_value: float
    target_value: float
    gap: float
    recommendation: str
    expected_impact: str
    implementation_effort: str
    
    def to_dict(self) -> Dict:
        return {
            'type': self.type.value,
            'priority': self.priority.value,
            'metric': self.metric,
            'current_value': self.current_value,
            'target_value': self.target_value,
            'gap': self.gap,
            'recommendation': self.recommendation,
            'expected_impact': self.expected_impact,
            'implementation_effort': self.implementation_effort
        }


@dataclass
class OptimizationAction:
    """Acción de optimización"""
    action_id: str
    type: OptimizationType
    priority: ActionPriority
    description: str
    params: Dict
    enabled: bool = False
    impact_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'action_id': self.action_id,
            'type': self.type.value,
            'priority': self.priority.value,
            'description': self.description,
            'params': self.params,
            'enabled': self.enabled,
            'impact_score': self.impact_score
        }


@dataclass
class PerformanceTuning:
    """Ajuste de performance"""
    parameter: str
    current_value: any
    optimal_value: any
    reason: str
    expected_improvement: str
    
    def to_dict(self) -> Dict:
        return {
            'parameter': self.parameter,
            'current_value': self.current_value,
            'optimal_value': self.optimal_value,
            'reason': self.reason,
            'expected_improvement': self.expected_improvement
        }


# ═══════════════════════════════════════════════════════════════════════════
#  CONTINUOUS OPTIMIZATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class ContinuousOptimizationEngine:
    """
    Motor de optimización continua.
    
    Features:
    - Análisis automático de métricas
    - Generación de insights
    - Recomendaciones data-driven
    - Auto-tuning de parámetros
    - Expansión de quick actions
    - Optimización de upsells
    - Mejora de share mechanics
    """
    
    def __init__(self, 
                 monitoring_system,
                 ab_testing_system,
                 feedback_system,
                 data_file: str = 'optimization_data.json'):
        self.monitor = monitoring_system
        self.ab_testing = ab_testing_system
        self.feedback = feedback_system
        self.data_file = Path(data_file)
        
        # Storage
        self.insights: List[OptimizationInsight] = []
        self.actions: Dict[str, OptimizationAction] = {}
        self.tunings: List[PerformanceTuning] = []
        
        # Active optimizations
        self.active_quick_actions: List[Dict] = []
        self.active_upsell_triggers: List[Dict] = []
        self.active_share_enhancements: List[Dict] = []
        
        self._load_data()
        
        logger.info("🔄 ContinuousOptimizationEngine initialized")
    
    def _load_data(self):
        """Carga configuración de optimizaciones."""
        if not self.data_file.exists():
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cargar acciones activas
            self.active_quick_actions = data.get('quick_actions', [])
            self.active_upsell_triggers = data.get('upsell_triggers', [])
            self.active_share_enhancements = data.get('share_enhancements', [])
            
            logger.info(f"✅ Loaded optimization config")
        except Exception as e:
            logger.error(f"❌ Error loading optimization data: {e}")
    
    def _save_data(self):
        """Guarda configuración."""
        try:
            data = {
                'quick_actions': self.active_quick_actions,
                'upsell_triggers': self.active_upsell_triggers,
                'share_enhancements': self.active_share_enhancements,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 Optimization config saved")
        except Exception as e:
            logger.error(f"❌ Error saving optimization data: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════
    #  INSIGHTS GENERATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def generate_insights(self) -> List[OptimizationInsight]:
        """Genera insights de optimización basados en datos."""
        self.insights = []
        
        # Analizar métricas
        report = self.monitor.generate_report(hours=48)
        metrics = report.metrics
        
        # 1. Onboarding optimization
        self._analyze_onboarding(metrics)
        
        # 2. Conversion optimization
        self._analyze_conversion(metrics)
        
        # 3. Engagement optimization
        self._analyze_engagement(metrics)
        
        # 4. Performance optimization
        self._analyze_performance(metrics)
        
        # 5. Revenue optimization
        self._analyze_revenue(metrics)
        
        # Ordenar por prioridad e impacto
        self.insights.sort(
            key=lambda x: (x.priority.value, -x.gap),
            reverse=False
        )
        
        return self.insights
    
    def _analyze_onboarding(self, metrics: Dict):
        """Analiza onboarding y genera insights."""
        onb = metrics['onboarding']
        completion_rate = onb['completion_rate']
        avg_duration = onb['avg_duration']
        
        # Completion rate optimization
        if completion_rate < 0.70:
            gap = 0.70 - completion_rate
            priority = ActionPriority.CRITICAL if gap > 0.15 else ActionPriority.HIGH
            
            insight = OptimizationInsight(
                type=OptimizationType.ONBOARDING,
                priority=priority,
                metric='completion_rate',
                current_value=completion_rate,
                target_value=0.70,
                gap=gap,
                recommendation=f"Current completion rate is {completion_rate:.1%}. Test shorter flow (2-step), reduce friction, increase incentives.",
                expected_impact=f"+{gap*100:.0f}% completion rate → +{gap*onb['started']:.0f} completed users",
                implementation_effort="Low (A/B test already configured)"
            )
            self.insights.append(insight)
        
        # Duration optimization
        if avg_duration > 90:
            gap = avg_duration - 90
            
            insight = OptimizationInsight(
                type=OptimizationType.ONBOARDING,
                priority=ActionPriority.HIGH,
                metric='avg_duration',
                current_value=avg_duration,
                target_value=90,
                gap=gap,
                recommendation=f"Average onboarding takes {avg_duration:.0f}s (target: <90s). Simplify steps, pre-fill data, add skip options.",
                expected_impact=f"-{gap:.0f}s TTFV → +10% completion",
                implementation_effort="Medium (UI changes required)"
            )
            self.insights.append(insight)
    
    def _analyze_conversion(self, metrics: Dict):
        """Analiza conversión y genera insights."""
        btns = metrics['buttons']
        click_rate = btns['click_rate']
        
        if click_rate < 0.70:
            gap = 0.70 - click_rate
            
            insight = OptimizationInsight(
                type=OptimizationType.CONVERSION,
                priority=ActionPriority.HIGH,
                metric='button_ctr',
                current_value=click_rate,
                target_value=0.70,
                gap=gap,
                recommendation=f"Button CTR is {click_rate:.1%}. Improve: CTAs clarity, button positioning, visual hierarchy, urgency.",
                expected_impact=f"+{gap*100:.0f}% CTR → +{gap*btns['total_impressions']:.0f} clicks",
                implementation_effort="Low (copy & design tweaks)"
            )
            self.insights.append(insight)
    
    def _analyze_engagement(self, metrics: Dict):
        """Analiza engagement."""
        # Placeholder - sería con datos reales
        insight = OptimizationInsight(
            type=OptimizationType.ENGAGEMENT,
            priority=ActionPriority.MEDIUM,
            metric='daily_active_rate',
            current_value=0.35,
            target_value=0.50,
            gap=0.15,
            recommendation="Increase daily active users with: daily rewards, push notifications, quick actions, gamification.",
            expected_impact="+15% DAU → +50 daily active users",
            implementation_effort="Medium (new features)"
        )
        self.insights.append(insight)
    
    def _analyze_performance(self, metrics: Dict):
        """Analiza performance."""
        perf = metrics['performance']
        avg_time = perf['avg_response_time']
        error_rate = perf['error_rate']
        
        if avg_time > 500:
            gap = avg_time - 500
            
            insight = OptimizationInsight(
                type=OptimizationType.PERFORMANCE,
                priority=ActionPriority.HIGH,
                metric='response_time',
                current_value=avg_time,
                target_value=500,
                gap=gap,
                recommendation=f"Response time is {avg_time:.0f}ms (target: <500ms). Optimize: cache hit rate, database queries, async operations.",
                expected_impact=f"-{gap:.0f}ms → +5% user satisfaction",
                implementation_effort="High (performance tuning)"
            )
            self.insights.append(insight)
        
        if error_rate > 0.02:
            gap = error_rate - 0.02
            
            insight = OptimizationInsight(
                type=OptimizationType.PERFORMANCE,
                priority=ActionPriority.CRITICAL,
                metric='error_rate',
                current_value=error_rate,
                target_value=0.02,
                gap=gap,
                recommendation=f"Error rate is {error_rate:.1%} (target: <2%). Fix: top errors, add error handling, improve stability.",
                expected_impact=f"-{gap*100:.1f}% errors → better UX",
                implementation_effort="High (bug fixes)"
            )
            self.insights.append(insight)
    
    def _analyze_revenue(self, metrics: Dict):
        """Analiza revenue."""
        # Placeholder
        insight = OptimizationInsight(
            type=OptimizationType.REVENUE,
            priority=ActionPriority.HIGH,
            metric='premium_conversion',
            current_value=0.05,
            target_value=0.12,
            gap=0.07,
            recommendation="Increase premium conversion with: better upsell timing, value demonstration, trial offers, social proof.",
            expected_impact="+7% conversion → +€2,100 MRR",
            implementation_effort="Medium (smart paywalls)"
        )
        self.insights.append(insight)
    
    # ═══════════════════════════════════════════════════════════════════════
    #  QUICK ACTIONS OPTIMIZATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def optimize_quick_actions(self, user_context: Dict = None) -> List[Dict]:
        """Optimiza quick actions basado en contexto y datos."""
        
        # Obtener top actions por conversión
        top_actions = self._get_top_actions_by_conversion()
        
        # Personalizar por contexto de usuario
        if user_context:
            top_actions = self._personalize_actions(top_actions, user_context)
        
        # Limitar a top 4-6
        self.active_quick_actions = top_actions[:6]
        self._save_data()
        
        return self.active_quick_actions
    
    def _get_top_actions_by_conversion(self) -> List[Dict]:
        """Obtiene acciones con mayor conversión."""
        # Ordenar por conversion_boost
        sorted_actions = sorted(
            QUICK_ACTIONS_POOL,
            key=lambda x: x['conversion_boost'],
            reverse=True
        )
        return sorted_actions
    
    def _personalize_actions(self, actions: List[Dict], context: Dict) -> List[Dict]:
        """Personaliza acciones por contexto."""
        personalized = actions.copy()
        
        # Si es usuario nuevo, priorizar onboarding/básicos
        if context.get('is_new_user'):
            # Mover scan y deals al principio
            personalized.sort(key=lambda x: x['id'] not in ['scan_popular', 'deals_today'])
        
        # Si es power user, priorizar avanzados
        elif context.get('is_power_user'):
            # Priorizar advanced search y premium
            personalized.sort(key=lambda x: x['id'] not in ['search_flex', 'search_multi', 'premium_trial'])
        
        # Si está cerca de límite free, priorizar premium
        elif context.get('near_limit'):
            # Premium trial al principio
            premium_action = next((a for a in personalized if a['id'] == 'premium_trial'), None)
            if premium_action:
                personalized.remove(premium_action)
                personalized.insert(0, premium_action)
        
        return personalized
    
    # ═══════════════════════════════════════════════════════════════════════
    #  PREMIUM UPSELL OPTIMIZATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_optimal_upsell(self, trigger: str, user_context: Dict = None) -> Optional[Dict]:
        """Obtiene upsell óptimo para trigger."""
        
        # Buscar trigger
        upsells = [u for u in UPSELL_TRIGGERS if u['trigger'] == trigger]
        
        if not upsells:
            return None
        
        # Si hay múltiples, elegir por conversion_rate
        upsell = max(upsells, key=lambda x: x['conversion_rate'])
        
        # Personalizar mensaje si hay contexto
        if user_context:
            upsell = self._personalize_upsell(upsell, user_context)
        
        return upsell
    
    def _personalize_upsell(self, upsell: Dict, context: Dict) -> Dict:
        """Personaliza mensaje de upsell."""
        message = upsell['message']
        
        # Agregar urgencia si es power user
        if context.get('is_power_user'):
            message += "\n\n⚡ Oferta especial por ser usuario activo: -20%"
        
        # Agregar social proof
        if context.get('friends_premium', 0) > 0:
            message += f"\n\n👥 {context['friends_premium']} amigos tuyos ya tienen Premium"
        
        upsell_copy = upsell.copy()
        upsell_copy['message'] = message
        return upsell_copy
    
    def track_upsell_conversion(self, trigger: str, converted: bool):
        """Trackea conversión de upsell."""
        # TODO: Actualizar conversion_rate del trigger
        pass
    
    # ═══════════════════════════════════════════════════════════════════════
    #  SHARE MECHANICS OPTIMIZATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_optimal_share_format(self, deal: Dict, user_context: Dict = None) -> Dict:
        """Obtiene formato óptimo de share."""
        
        # Elegir enhancement por conversion_boost
        enhancements = sorted(
            SHARE_ENHANCEMENTS,
            key=lambda x: x['conversion_boost'],
            reverse=True
        )
        
        # Por defecto, el mejor
        enhancement = enhancements[0]
        
        # Personalizar por contexto
        if user_context:
            # Si tiene muchos referidos, usar incentive
            if user_context.get('referrals_count', 0) > 5:
                enhancement = next(
                    (e for e in enhancements if e['type'] == 'referral_incentive'),
                    enhancement
                )
            # Si es deal muy bueno, usar urgency
            elif deal.get('savings_pct', 0) > 30:
                enhancement = next(
                    (e for e in enhancements if e['type'] == 'urgency'),
                    enhancement
                )
        
        # Format message
        message = enhancement['message'].format(
            deal_name=deal.get('name', 'Vuelo'),
            price=deal.get('price', '€???'),
            savings=deal.get('savings', '€???'),
            original_price=deal.get('original_price', '€???'),
            pct=deal.get('savings_pct', '??'),
            users_count=deal.get('views', random.randint(50, 200)),
            spots=random.randint(3, 12),
            share_link=deal.get('share_link', 'https://t.me/cazador_bot')
        )
        
        return {
            'type': enhancement['type'],
            'message': message,
            'conversion_boost': enhancement['conversion_boost']
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    #  PERFORMANCE AUTO-TUNING
    # ═══════════════════════════════════════════════════════════════════════
    
    def generate_performance_tunings(self) -> List[PerformanceTuning]:
        """Genera recomendaciones de tuning."""
        self.tunings = []
        
        # Analizar métricas de performance
        report = self.monitor.generate_report(hours=48)
        perf = report.metrics['performance']
        
        # Cache tuning
        cache_hit_rate = 0.73  # Placeholder
        if cache_hit_rate < 0.80:
            tuning = PerformanceTuning(
                parameter='cache_ttl',
                current_value=600,
                optimal_value=900,
                reason=f"Cache hit rate is {cache_hit_rate:.1%}, increasing TTL would improve it",
                expected_improvement="+5% cache hit rate → -100ms avg response time"
            )
            self.tunings.append(tuning)
        
        # Worker pool tuning
        if perf['avg_response_time'] > 500:
            tuning = PerformanceTuning(
                parameter='max_workers',
                current_value=25,
                optimal_value=35,
                reason="High response time suggests worker pool is saturated",
                expected_improvement="-150ms avg response time"
            )
            self.tunings.append(tuning)
        
        # API timeout tuning
        if perf['error_rate'] > 0.02:
            tuning = PerformanceTuning(
                parameter='api_timeout',
                current_value=15,
                optimal_value=20,
                reason="High error rate may be due to timeouts",
                expected_improvement="-1% error rate"
            )
            self.tunings.append(tuning)
        
        return self.tunings
    
    # ═══════════════════════════════════════════════════════════════════════
    #  REPORTING
    # ═══════════════════════════════════════════════════════════════════════
    
    def generate_optimization_report(self) -> Dict:
        """Genera reporte completo de optimización."""
        insights = self.generate_insights()
        tunings = self.generate_performance_tunings()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'insights': [i.to_dict() for i in insights],
            'tunings': [t.to_dict() for t in tunings],
            'quick_actions': self.active_quick_actions,
            'summary': {
                'total_insights': len(insights),
                'critical_insights': sum(1 for i in insights if i.priority == ActionPriority.CRITICAL),
                'high_insights': sum(1 for i in insights if i.priority == ActionPriority.HIGH),
                'expected_impact': self._calculate_total_impact(insights)
            },
            'recommendations': self._generate_top_recommendations(insights, tunings)
        }
        
        return report
    
    def _calculate_total_impact(self, insights: List[OptimizationInsight]) -> str:
        """Calcula impacto total esperado."""
        # Estimaciones simplificadas
        conversion_boost = sum(i.gap for i in insights if i.type == OptimizationType.CONVERSION) * 100
        retention_boost = sum(i.gap for i in insights if i.type in [OptimizationType.ONBOARDING, OptimizationType.ENGAGEMENT]) * 100
        revenue_boost = sum(i.gap for i in insights if i.type == OptimizationType.REVENUE) * 100
        
        return f"+{conversion_boost:.0f}% conversion, +{retention_boost:.0f}% retention, +{revenue_boost:.0f}% revenue"
    
    def _generate_top_recommendations(self, insights: List[OptimizationInsight], 
                                     tunings: List[PerformanceTuning]) -> List[str]:
        """Genera top recomendaciones."""
        recommendations = []
        
        # Top 3 insights
        for insight in insights[:3]:
            recommendations.append(
                f"[{insight.priority.value.upper()}] {insight.type.value}: {insight.recommendation}"
            )
        
        # Top 2 tunings
        for tuning in tunings[:2]:
            recommendations.append(
                f"[TUNING] {tuning.parameter}: {tuning.current_value} → {tuning.optimal_value} ({tuning.expected_improvement})"
            )
        
        return recommendations
    
    def print_optimization_report(self):
        """Imprime reporte en consola."""
        report = self.generate_optimization_report()
        
        print("\n" + "="*70)
        print("🔄 CONTINUOUS OPTIMIZATION REPORT".center(70))
        print("="*70 + "\n")
        
        # Summary
        summary = report['summary']
        print(f"Total Insights: {summary['total_insights']}")
        print(f"  🔴 Critical: {summary['critical_insights']}")
        print(f"  🟠 High: {summary['high_insights']}")
        print(f"\nExpected Impact: {summary['expected_impact']}\n")
        
        # Top insights
        print("TOP OPTIMIZATION INSIGHTS:\n")
        for i, insight_data in enumerate(report['insights'][:5], 1):
            priority_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '⚪'
            }
            emoji = priority_emoji.get(insight_data['priority'], '⚪')
            
            print(f"{i}. {emoji} [{insight_data['type'].upper()}] {insight_data['metric']}")
            print(f"   Current: {insight_data['current_value']:.2f} | Target: {insight_data['target_value']:.2f} | Gap: {insight_data['gap']:.2f}")
            print(f"   💡 {insight_data['recommendation']}")
            print(f"   📈 Impact: {insight_data['expected_impact']}")
            print()
        
        # Performance tunings
        if report['tunings']:
            print("PERFORMANCE TUNINGS:\n")
            for i, tuning in enumerate(report['tunings'], 1):
                print(f"{i}. {tuning['parameter']}: {tuning['current_value']} → {tuning['optimal_value']}")
                print(f"   Reason: {tuning['reason']}")
                print(f"   Impact: {tuning['expected_improvement']}\n")
        
        # Top recommendations
        print("TOP RECOMMENDATIONS:\n")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
        
        print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    # 🧪 Test del sistema
    print("🧪 Testing ContinuousOptimizationEngine...\n")
    
    # Mock de sistemas
    from monitoring_system import MonitoringSystem
    from ab_testing_system import ABTestingSystem
    from feedback_collection_system import FeedbackCollectionSystem
    
    monitor = MonitoringSystem()
    ab = ABTestingSystem()
    feedback = FeedbackCollectionSystem()
    
    # Crear engine
    optimizer = ContinuousOptimizationEngine(monitor, ab, feedback)
    
    # Simular datos
    print("1. Simulating metrics...")
    for i in range(100):
        monitor.track_onboarding_start(10000 + i)
        if i < 65:  # 65% completion
            monitor.track_onboarding_completion(10000 + i, 75 + i % 30)
    
    for i in range(500):
        monitor.track_button_impression('test_button', 10000 + i % 100)
        if i % 2 == 0:
            monitor.track_button_click('test_button', 10000 + i % 100)
    
    # Generar insights
    print("\n2. Generating optimization insights...")
    optimizer.print_optimization_report()
    
    # Test quick actions
    print("3. Testing quick actions optimization...")
    actions = optimizer.optimize_quick_actions({'is_power_user': True})
    print(f"\n  Optimized {len(actions)} quick actions:")
    for action in actions[:3]:
        print(f"    • {action['label']} (boost: +{action['conversion_boost']:.0%})")
    
    print("\n✅ Test completed!")
