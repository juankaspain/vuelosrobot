#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║  🤖 CONTINUOUS OPTIMIZATION ENGINE                              ║
║  🚀 Cazador Supremo v14.3                                       ║
║  🔄 Auto-analysis + Auto-tuning + Auto-improvements             ║
╚══════════════════════════════════════════════════════════════════╝

Motor de optimización continua:
- Análisis automático de métricas
- Recomendaciones inteligentes
- Auto-tuning de parámetros
- Expansión automática de features
- Mejora continua sin intervención

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
import random

try:
    from monitoring_system import MonitoringSystem
    from ab_testing_system import ABTestingSystem
    from feedback_collection_system import FeedbackCollectionSystem
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════

class OptimizationArea(Enum):
    """Áreas de optimización"""
    ONBOARDING = "onboarding"
    QUICK_ACTIONS = "quick_actions"
    PREMIUM_UPSELL = "premium_upsell"
    SHARE_MECHANICS = "share_mechanics"
    PERFORMANCE = "performance"
    USER_ENGAGEMENT = "user_engagement"


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


# Quick Actions Templates
QUICK_ACTION_TEMPLATES = [
    {
        'id': 'qa_scan_deals',
        'label': '🔍 Escanear Chollos',
        'command': '/deals',
        'priority': 1,
        'context': ['home', 'search_complete']
    },
    {
        'id': 'qa_flexible_search',
        'label': '📅 Búsqueda Flexible',
        'command': '/search_flex',
        'priority': 2,
        'context': ['home', 'after_scan']
    },
    {
        'id': 'qa_my_watchlist',
        'label': '🔔 Mis Alertas',
        'command': '/watchlist',
        'priority': 3,
        'context': ['home', 'after_deal']
    },
    {
        'id': 'qa_daily_reward',
        'label': '🎁 Reward Diario',
        'command': '/daily',
        'priority': 4,
        'context': ['home']
    },
    {
        'id': 'qa_premium',
        'label': '💎 Ver Premium',
        'command': '/premium',
        'priority': 5,
        'context': ['after_limit', 'after_deal']
    },
    {
        'id': 'qa_invite',
        'label': '👥 Invitar Amigos',
        'command': '/invite',
        'priority': 6,
        'context': ['after_deal', 'after_premium']
    },
    {
        'id': 'qa_multi_city',
        'label': '🌍 Multi-Ciudad',
        'command': '/search_multi',
        'priority': 7,
        'context': ['home', 'after_search']
    },
    {
        'id': 'qa_budget_search',
        'label': '💰 Por Presupuesto',
        'command': '/search_budget',
        'priority': 8,
        'context': ['home', 'after_search']
    },
    {
        'id': 'qa_profile',
        'label': '👤 Mi Perfil',
        'command': '/profile',
        'priority': 9,
        'context': ['home']
    },
    {
        'id': 'qa_leaderboard',
        'label': '🏆 Rankings',
        'command': '/leaderboard',
        'priority': 10,
        'context': ['home', 'after_achievement']
    },
]

# Premium Upsell Messages
PREMIUM_UPSELL_VARIANTS = [
    {
        'id': 'value_prop_1',
        'title': '🚀 Upgrade a Premium',
        'message': (
            "💎 *Desbloquea Premium y ahorra más:*\n\n"
            "✅ Búsquedas ilimitadas\n"
            "✅ Alertas personalizadas\n"
            "✅ Sin anuncios\n"
            "✅ Soporte prioritario\n\n"
            "_Solo €9.99/mes - Cancela cuando quieras_"
        ),
        'cta': '💎 Probar Gratis 7 Días'
    },
    {
        'id': 'value_prop_2',
        'title': '💰 Ahorra €200+ al año',
        'message': (
            "*Usuarios Premium ahorran 30% más:*\n\n"
            "📊 Análisis avanzado de precios\n"
            "🔔 Alertas instant<|uáneas\n"
            "🎯 Búsquedas ilimitadas\n"
            "⚡ Acceso anticipado a deals\n\n"
            "_€9.99/mes se paga solo con 1 vuelo_"
        ),
        'cta': '🚀 Activar Premium'
    },
    {
        'id': 'value_prop_3',
        'title': '🎁 Oferta Especial',
        'message': (
            "*¡Solo por hoy!*\n\n"
            "💎 Premium por €6.99/mes\n"
            "🎁 +500 FlightCoins gratis\n"
            "✨ Todo ilimitado\n\n"
            "_⏰ Oferta termina en 24h_"
        ),
        'cta': '⚡ Aprovechar Oferta'
    },
]

# Share Success Messages
SHARE_VARIANTS = [
    {
        'id': 'share_1',
        'message': (
            "🔥 *¡Chollo encontrado!*\n\n"
            "{deal_details}\n\n"
            "📤 Comparte este chollo:\n"
            "• +50 FlightCoins por cada amigo\n"
            "• Tu amigo recibe +100 FlightCoins\n"
            "• Win-win para todos 🎉"
        )
    },
    {
        'id': 'share_2',
        'message': (
            "💎 *Deal exclusivo*\n\n"
            "{deal_details}\n\n"
            "👥 Invita amigos y gana:\n"
            "🎁 50 coins por referido\n"
            "🏆 Sube en el ranking\n"
            "💰 Desbloquea rewards"
        )
    },
]


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class OptimizationAction:
    """Acción de optimización"""
    action_id: str
    area: OptimizationArea
    priority: ActionPriority
    title: str
    description: str
    impact_estimate: float  # 0-100
    effort_estimate: int    # 1-5
    status: ActionStatus
    created_at: str
    completed_at: Optional[str] = None
    results: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            'action_id': self.action_id,
            'area': self.area.value,
            'priority': self.priority.value,
            'title': self.title,
            'description': self.description,
            'impact_estimate': self.impact_estimate,
            'effort_estimate': self.effort_estimate,
            'status': self.status.value,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'results': self.results
        }


@dataclass
class OptimizationReport:
    """Reporte de optimización"""
    timestamp: str
    actions_identified: int
    actions_completed: int
    total_impact: float
    areas_optimized: List[str]
    key_improvements: List[str]
    next_actions: List[OptimizationAction]
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'actions_identified': self.actions_identified,
            'actions_completed': self.actions_completed,
            'total_impact': self.total_impact,
            'areas_optimized': self.areas_optimized,
            'key_improvements': self.key_improvements,
            'next_actions': [a.to_dict() for a in self.next_actions]
        }


# ═══════════════════════════════════════════════════════════════
#  CONTINUOUS OPTIMIZATION ENGINE
# ═══════════════════════════════════════════════════════════════

class ContinuousOptimizationEngine:
    """
    Motor de optimización continua.
    
    Features:
    - Análisis automático de métricas
    - Identificación de oportunidades
    - Recomendaciones inteligentes
    - Auto-tuning de parámetros
    - Expansión de features
    - Mejora continua
    """
    
    def __init__(self,
                 monitor: 'MonitoringSystem' = None,
                 ab_testing: 'ABTestingSystem' = None,
                 feedback: 'FeedbackCollectionSystem' = None,
                 data_file: str = 'optimization_data.json'):
        
        self.monitor = monitor
        self.ab_testing = ab_testing
        self.feedback = feedback
        self.data_file = Path(data_file)
        
        # Storage
        self.actions: List[OptimizationAction] = []
        self.action_history: List[OptimizationAction] = []
        self.optimization_params: Dict[str, any] = self._get_default_params()
        
        self._load_data()
        
        logger.info("🤖 ContinuousOptimizationEngine initialized")
    
    def _get_default_params(self) -> Dict:
        """Parámetros por defecto."""
        return {
            'onboarding': {
                'max_duration_seconds': 90,
                'completion_target': 0.75,
                'bonus_coins': 200,
            },
            'quick_actions': {
                'max_visible': 4,
                'personalization_enabled': True,
                'context_aware': True,
            },
            'premium_upsell': {
                'show_after_deals': 3,
                'cooldown_hours': 24,
                'trial_days': 7,
            },
            'share_mechanics': {
                'coins_per_referral': 50,
                'min_viral_coefficient': 0.3,
            },
            'performance': {
                'target_response_ms': 500,
                'cache_ttl_seconds': 300,
            }
        }
    
    def _load_data(self):
        """Carga datos de optimización."""
        if not self.data_file.exists():
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruir acciones
            for action_data in data.get('actions', []):
                action = OptimizationAction(
                    action_id=action_data['action_id'],
                    area=OptimizationArea(action_data['area']),
                    priority=ActionPriority(action_data['priority']),
                    title=action_data['title'],
                    description=action_data['description'],
                    impact_estimate=action_data['impact_estimate'],
                    effort_estimate=action_data['effort_estimate'],
                    status=ActionStatus(action_data['status']),
                    created_at=action_data['created_at'],
                    completed_at=action_data.get('completed_at'),
                    results=action_data.get('results')
                )
                
                if action.status == ActionStatus.COMPLETED:
                    self.action_history.append(action)
                else:
                    self.actions.append(action)
            
            # Cargar parámetros
            if 'params' in data:
                self.optimization_params.update(data['params'])
            
            logger.info(f"✅ Loaded {len(self.actions)} active actions")
        except Exception as e:
            logger.error(f"❌ Error loading optimization data: {e}")
    
    def _save_data(self):
        """Guarda datos."""
        try:
            data = {
                'actions': [
                    *[a.to_dict() for a in self.actions],
                    *[a.to_dict() for a in self.action_history[-100:]]  # Últimas 100
                ],
                'params': self.optimization_params,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 Optimization data saved")
        except Exception as e:
            logger.error(f"❌ Error saving optimization data: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    #  ANALYSIS & IDENTIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def analyze_and_optimize(self) -> OptimizationReport:
        """Análisis completo y optimización."""
        logger.info("🔍 Starting optimization analysis...")
        
        # Identificar oportunidades por área
        opportunities = []
        
        if self.monitor:
            opportunities.extend(self._analyze_onboarding())
            opportunities.extend(self._analyze_performance())
            opportunities.extend(self._analyze_engagement())
        
        if self.feedback:
            opportunities.extend(self._analyze_feedback())
        
        if self.ab_testing:
            opportunities.extend(self._analyze_ab_tests())
        
        # Priorizar
        opportunities.sort(
            key=lambda x: (x.priority.value, -x.impact_estimate)
        )
        
        # Crear acciones
        actions_created = 0
        for opp in opportunities[:10]:  # Top 10
            if not self._action_exists(opp.action_id):
                self.actions.append(opp)
                actions_created += 1
        
        # Auto-ejecutar acciones de bajo esfuerzo
        auto_executed = self._auto_execute_low_effort_actions()
        
        # Generar reporte
        report = OptimizationReport(
            timestamp=datetime.now().isoformat(),
            actions_identified=actions_created,
            actions_completed=auto_executed,
            total_impact=sum(a.impact_estimate for a in self.actions),
            areas_optimized=[a.area.value for a in self.action_history[-10:]],
            key_improvements=self._get_key_improvements(),
            next_actions=self.actions[:5]
        )
        
        self._save_data()
        
        logger.info(f"✅ Analysis complete: {actions_created} opportunities identified")
        return report
    
    def _action_exists(self, action_id: str) -> bool:
        """Verifica si acción ya existe."""
        return any(a.action_id == action_id for a in self.actions)
    
    def _analyze_onboarding(self) -> List[OptimizationAction]:
        """Analiza onboarding."""
        actions = []
        
        # Obtener métricas
        completion_rate = self.monitor.get_onboarding_completion_rate(hours=48)
        avg_duration = self.monitor._get_avg_metric('onboarding.total_duration', 48)
        
        # Baja completion rate
        if completion_rate < 0.70:
            actions.append(OptimizationAction(
                action_id='opt_onb_completion',
                area=OptimizationArea.ONBOARDING,
                priority=ActionPriority.HIGH,
                title='Mejorar Completion Rate del Onboarding',
                description=f'Tasa actual: {completion_rate:.1%} (target: 70%)',
                impact_estimate=25,
                effort_estimate=3,
                status=ActionStatus.PENDING,
                created_at=datetime.now().isoformat()
            ))
        
        # Duración alta
        if avg_duration > 90:
            actions.append(OptimizationAction(
                action_id='opt_onb_duration',
                area=OptimizationArea.ONBOARDING,
                priority=ActionPriority.MEDIUM,
                title='Reducir Duración del Onboarding',
                description=f'Duración actual: {avg_duration:.0f}s (target: <90s)',
                impact_estimate=15,
                effort_estimate=2,
                status=ActionStatus.PENDING,
                created_at=datetime.now().isoformat()
            ))
        
        return actions
    
    def _analyze_performance(self) -> List[OptimizationAction]:
        """Analiza performance."""
        actions = []
        
        avg_response = self.monitor.get_avg_response_time(hours=48)
        error_rate = self.monitor.get_error_rate(hours=48)
        
        # Response time alto
        if avg_response > 500:
            actions.append(OptimizationAction(
                action_id='opt_perf_response',
                area=OptimizationArea.PERFORMANCE,
                priority=ActionPriority.HIGH,
                title='Optimizar Tiempo de Respuesta',
                description=f'Tiempo actual: {avg_response:.0f}ms (target: <500ms)',
                impact_estimate=30,
                effort_estimate=4,
                status=ActionStatus.PENDING,
                created_at=datetime.now().isoformat()
            ))
        
        # Error rate alto
        if error_rate > 0.02:
            actions.append(OptimizationAction(
                action_id='opt_perf_errors',
                area=OptimizationArea.PERFORMANCE,
                priority=ActionPriority.CRITICAL,
                title='Reducir Tasa de Errores',
                description=f'Tasa actual: {error_rate:.1%} (target: <2%)',
                impact_estimate=40,
                effort_estimate=3,
                status=ActionStatus.PENDING,
                created_at=datetime.now().isoformat()
            ))
        
        return actions
    
    def _analyze_engagement(self) -> List[OptimizationAction]:
        """Analiza engagement."""
        actions = []
        
        button_ctr = self.monitor.get_button_click_rate(hours=48)
        
        # CTR bajo
        if button_ctr < 0.60:
            actions.append(OptimizationAction(
                action_id='opt_eng_buttons',
                area=OptimizationArea.USER_ENGAGEMENT,
                priority=ActionPriority.MEDIUM,
                title='Mejorar Click-Through Rate',
                description=f'CTR actual: {button_ctr:.1%} (target: >60%)',
                impact_estimate=20,
                effort_estimate=2,
                status=ActionStatus.PENDING,
                created_at=datetime.now().isoformat()
            ))
        
        return actions
    
    def _analyze_feedback(self) -> List[OptimizationAction]:
        """Analiza feedback."""
        actions = []
        
        # NPS
        nps = self.feedback.calculate_nps(days=30)
        
        if nps.score < 40:
            actions.append(OptimizationAction(
                action_id='opt_fb_nps',
                area=OptimizationArea.USER_ENGAGEMENT,
                priority=ActionPriority.HIGH,
                title='Mejorar Net Promoter Score',
                description=f'NPS actual: {nps.score:.1f} (target: >50)',
                impact_estimate=35,
                effort_estimate=4,
                status=ActionStatus.PENDING,
                created_at=datetime.now().isoformat()
            ))
        
        # Feedback negativo
        summary = self.feedback.get_feedback_summary(days=30)
        if summary:
            negative_pct = summary['by_sentiment'].get('negative', 0) / summary['total_feedback']
            
            if negative_pct > 0.25:
                actions.append(OptimizationAction(
                    action_id='opt_fb_sentiment',
                    area=OptimizationArea.USER_ENGAGEMENT,
                    priority=ActionPriority.HIGH,
                    title='Reducir Feedback Negativo',
                    description=f'Negativo: {negative_pct:.1%} (target: <20%)',
                    impact_estimate=30,
                    effort_estimate=3,
                    status=ActionStatus.PENDING,
                    created_at=datetime.now().isoformat()
                ))
        
        return actions
    
    def _analyze_ab_tests(self) -> List[OptimizationAction]:
        """Analiza resultados de A/B tests."""
        actions = []
        
        # Verificar cada experimento
        for exp_id, exp in self.ab_testing.experiments.items():
            if exp.status.value != 'running':
                continue
            
            # Detectar winner
            winner = self.ab_testing.detect_winner(exp_id)
            
            if winner:
                actions.append(OptimizationAction(
                    action_id=f'opt_ab_{exp_id}',
                    area=OptimizationArea.USER_ENGAGEMENT,
                    priority=ActionPriority.MEDIUM,
                    title=f'Rollout Winner: {exp.name}',
                    description=f'Winner: {winner}',
                    impact_estimate=25,
                    effort_estimate=1,
                    status=ActionStatus.PENDING,
                    created_at=datetime.now().isoformat()
                ))
        
        return actions
    
    # ═══════════════════════════════════════════════════════════════
    #  AUTO-EXECUTION
    # ═══════════════════════════════════════════════════════════════
    
    def _auto_execute_low_effort_actions(self) -> int:
        """Auto-ejecuta acciones de bajo esfuerzo."""
        executed = 0
        
        for action in self.actions[:]:
            if action.effort_estimate <= 2 and action.status == ActionStatus.PENDING:
                if self._execute_action(action):
                    executed += 1
        
        return executed
    
    def _execute_action(self, action: OptimizationAction) -> bool:
        """Ejecuta una acción."""
        logger.info(f"⚡ Executing: {action.title}")
        
        action.status = ActionStatus.IN_PROGRESS
        success = False
        
        try:
            # Ejecutar según área
            if 'opt_ab_' in action.action_id:
                # Rollout A/B test winner
                exp_id = action.action_id.replace('opt_ab_', '')
                winner = self.ab_testing.detect_winner(exp_id)
                if winner:
                    self.ab_testing.rollout_winner(exp_id, winner)
                    action.results = {'winner': winner, 'rolled_out': True}
                    success = True
            
            elif action.area == OptimizationArea.PERFORMANCE:
                # Auto-tune performance
                if 'response' in action.action_id:
                    # Aumentar cache TTL
                    self.optimization_params['performance']['cache_ttl_seconds'] += 60
                    action.results = {'cache_ttl_increased': True}
                    success = True
            
            elif action.area == OptimizationArea.QUICK_ACTIONS:
                # Expand quick actions
                success = self._expand_quick_actions()
                action.results = {'quick_actions_expanded': success}
            
            if success:
                action.status = ActionStatus.COMPLETED
                action.completed_at = datetime.now().isoformat()
                self.actions.remove(action)
                self.action_history.append(action)
                logger.info(f"✅ Action completed: {action.title}")
            else:
                action.status = ActionStatus.PENDING
        
        except Exception as e:
            logger.error(f"❌ Action failed: {action.title} - {e}")
            action.status = ActionStatus.FAILED
        
        return success
    
    def _expand_quick_actions(self) -> bool:
        """Expande quick actions basado en uso."""
        # Obtener top buttons
        top_buttons = self.monitor.get_top_buttons(hours=168, limit=10)  # Última semana
        
        # Agregar más quick actions populares
        # TODO: Implementar lógica de expansión
        
        return True
    
    # ═══════════════════════════════════════════════════════════════
    #  HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def _get_key_improvements(self) -> List[str]:
        """Obtiene mejoras clave recientes."""
        improvements = []
        
        for action in self.action_history[-10:]:
            if action.status == ActionStatus.COMPLETED:
                improvements.append(
                    f"{action.area.value}: {action.title} (+{action.impact_estimate:.0f}% impact)"
                )
        
        return improvements
    
    def get_quick_actions_for_context(self, context: str, user_id: int = None) -> List[Dict]:
        """Obtiene quick actions para contexto."""
        # Filtrar por contexto
        actions = [
            qa for qa in QUICK_ACTION_TEMPLATES
            if context in qa['context']
        ]
        
        # Ordenar por prioridad
        actions.sort(key=lambda x: x['priority'])
        
        # Personalizar si hay user_id
        if user_id and self.monitor:
            # TODO: Personalización basada en comportamiento
            pass
        
        # Retornar top N
        max_visible = self.optimization_params['quick_actions']['max_visible']
        return actions[:max_visible]
    
    def get_premium_upsell_message(self, user_id: int, trigger_context: str) -> Optional[Dict]:
        """Obtiene mensaje de upsell premium."""
        # Verificar cooldown
        # TODO: Implementar cooldown por usuario
        
        # Seleccionar variante (A/B test)
        if self.ab_testing:
            variant_config = self.ab_testing.get_variant_config(user_id, 'premium_upsell_message')
            variant_id = variant_config.get('variant_id', 'value_prop_1')
        else:
            variant_id = random.choice([v['id'] for v in PREMIUM_UPSELL_VARIANTS])
        
        # Obtener mensaje
        for variant in PREMIUM_UPSELL_VARIANTS:
            if variant['id'] == variant_id:
                return variant
        
        return PREMIUM_UPSELL_VARIANTS[0]
    
    def get_share_message(self, deal_details: str, user_id: int) -> str:
        """Obtiene mensaje de compartir."""
        # Seleccionar variante
        if self.ab_testing:
            variant_config = self.ab_testing.get_variant_config(user_id, 'share_message')
            variant_id = variant_config.get('variant_id', 'share_1')
        else:
            variant_id = random.choice([v['id'] for v in SHARE_VARIANTS])
        
        # Obtener mensaje
        for variant in SHARE_VARIANTS:
            if variant['id'] == variant_id:
                return variant['message'].format(deal_details=deal_details)
        
        return SHARE_VARIANTS[0]['message'].format(deal_details=deal_details)
    
    def print_optimization_report(self):
        """Imprime reporte de optimización."""
        report = self.analyze_and_optimize()
        
        print("\n" + "="*70)
        print("🤖 CONTINUOUS OPTIMIZATION REPORT".center(70))
        print("="*70 + "\n")
        
        print(f"Timestamp: {report.timestamp}\n")
        
        print("SUMMARY:")
        print(f"  • Actions Identified: {report.actions_identified}")
        print(f"  • Actions Completed: {report.actions_completed}")
        print(f"  • Total Impact: +{report.total_impact:.0f}%\n")
        
        if report.areas_optimized:
            print("AREAS OPTIMIZED:")
            for area in set(report.areas_optimized):
                count = report.areas_optimized.count(area)
                print(f"  • {area}: {count} improvements")
            print()
        
        if report.key_improvements:
            print("KEY IMPROVEMENTS:")
            for improvement in report.key_improvements[-5:]:
                print(f"  ✅ {improvement}")
            print()
        
        if report.next_actions:
            print("NEXT ACTIONS (Priority Order):")
            for i, action in enumerate(report.next_actions, 1):
                priority_emoji = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '⚪'
                }
                emoji = priority_emoji.get(action.priority.value, '⚪')
                print(f"  {i}. {emoji} {action.title}")
                print(f"     Impact: +{action.impact_estimate:.0f}% | Effort: {action.effort_estimate}/5")
                print(f"     {action.description}")
            print()
        
        print("="*70 + "\n")


if __name__ == '__main__':
    # 🧪 Test del motor
    print("🧪 Testing ContinuousOptimizationEngine...\n")
    
    if not DEPENDENCIES_AVAILABLE:
        print("⚠️ Dependencies not available. Install monitoring, ab_testing, feedback systems.")
    else:
        # Crear instancias
        from monitoring_system import MonitoringSystem
        from ab_testing_system import ABTestingSystem
        from feedback_collection_system import FeedbackCollectionSystem
        
        monitor = MonitoringSystem()
        ab = ABTestingSystem()
        feedback = FeedbackCollectionSystem()
        
        # Simular datos
        print("1. Simulating metrics...")
        for i in range(50):
            monitor.track_onboarding_start(20000 + i)
            if i < 35:  # 70% completion
                monitor.track_onboarding_completion(20000 + i, 75 + i % 20)
        
        for i in range(100):
            monitor.track_button_impression('scan', 20000 + i)
            if i % 2 == 0:
                monitor.track_button_click('scan', 20000 + i)
        
        # Crear motor
        print("2. Creating optimization engine...")
        engine = ContinuousOptimizationEngine(monitor, ab, feedback)
        
        # Análisis
        print("\n3. Running optimization analysis...")
        engine.print_optimization_report()
    
    print("✅ Test completed!")
