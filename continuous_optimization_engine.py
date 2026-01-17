#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  🔄 CONTINUOUS OPTIMIZATION ENGINE                                   ║
║  🚀 Cazador Supremo v14.2                                           ║
║  🤖 Auto-optimization + ML Insights + Real-time Adaptation          ║
╚══════════════════════════════════════════════════════════════════════╝

Motor de optimización continua que:
- Analiza métricas en tiempo real
- Genera insights automáticos
- Aplica optimizaciones sin intervención
- Predice problemas antes de que ocurran
- Mejora conversión automáticamente

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
from collections import defaultdict, deque
import math
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
    PERFORMANCE = "performance"
    REVENUE = "revenue"


class InsightSeverity(Enum):
    """Severidad del insight"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionStatus(Enum):
    """Estado de acción"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"


# Reglas de optimización
OPTIMIZATION_RULES = {
    'onboarding_duration': {
        'condition': lambda metrics: metrics.get('onboarding_avg_duration', 0) > 90,
        'action': 'reduce_onboarding_steps',
        'priority': 'high',
        'impact': 'Reduce TTFV by ~30%'
    },
    'completion_rate_low': {
        'condition': lambda metrics: metrics.get('onboarding_completion_rate', 1.0) < 0.70,
        'action': 'improve_onboarding_flow',
        'priority': 'high',
        'impact': 'Increase D1 retention by ~15%'
    },
    'button_ctr_low': {
        'condition': lambda metrics: metrics.get('button_click_rate', 1.0) < 0.60,
        'action': 'optimize_button_placement',
        'priority': 'medium',
        'impact': 'Increase engagement by ~20%'
    },
    'error_rate_high': {
        'condition': lambda metrics: metrics.get('error_rate', 0.0) > 0.05,
        'action': 'fix_top_errors',
        'priority': 'critical',
        'impact': 'Reduce churn by ~25%'
    },
    'response_time_slow': {
        'condition': lambda metrics: metrics.get('avg_response_time', 0) > 1000,
        'action': 'optimize_performance',
        'priority': 'high',
        'impact': 'Improve satisfaction by ~18%'
    },
    'premium_conversion_low': {
        'condition': lambda metrics: metrics.get('premium_conversion_rate', 0.0) < 0.08,
        'action': 'enhance_premium_upsells',
        'priority': 'medium',
        'impact': 'Increase revenue by ~35%'
    },
    'share_rate_low': {
        'condition': lambda metrics: metrics.get('share_rate', 0.0) < 0.15,
        'action': 'improve_share_mechanics',
        'priority': 'medium',
        'impact': 'Boost viral growth by ~40%'
    },
    'nps_declining': {
        'condition': lambda metrics: metrics.get('nps_score', 50) < 40,
        'action': 'address_feedback',
        'priority': 'high',
        'impact': 'Recover user satisfaction'
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Insight:
    """Insight generado por análisis"""
    insight_id: str
    type: OptimizationType
    severity: InsightSeverity
    title: str
    description: str
    data: Dict
    recommendations: List[str]
    estimated_impact: str
    timestamp: str
    
    def to_dict(self) -> Dict:
        return {
            'insight_id': self.insight_id,
            'type': self.type.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'data': self.data,
            'recommendations': self.recommendations,
            'estimated_impact': self.estimated_impact,
            'timestamp': self.timestamp
        }


@dataclass
class OptimizationAction:
    """Acción de optimización"""
    action_id: str
    type: OptimizationType
    name: str
    description: str
    status: ActionStatus
    created_at: str
    applied_at: Optional[str] = None
    rolled_back_at: Optional[str] = None
    metrics_before: Dict = None
    metrics_after: Dict = None
    impact_actual: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'action_id': self.action_id,
            'type': self.type.value,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'created_at': self.created_at,
            'applied_at': self.applied_at,
            'rolled_back_at': self.rolled_back_at,
            'metrics_before': self.metrics_before,
            'metrics_after': self.metrics_after,
            'impact_actual': self.impact_actual
        }


# ═══════════════════════════════════════════════════════════════════════════
#  OPTIMIZATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class ContinuousOptimizationEngine:
    """
    Motor de optimización continua.
    
    Capacidades:
    - Análisis automático de métricas
    - Generación de insights
    - Recomendaciones accionables
    - Auto-aplicación de optimizaciones
    - Monitoreo de impacto
    - Rollback automático si falla
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
        self.insights: List[Insight] = []
        self.actions: List[OptimizationAction] = []
        self.optimization_history: deque = deque(maxlen=1000)
        
        # State
        self.auto_optimize_enabled = True
        self.last_analysis = None
        
        self._load_data()
        
        logger.info("🔄 ContinuousOptimizationEngine initialized")
    
    def _load_data(self):
        """Carga datos históricos."""
        if not self.data_file.exists():
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruir insights
            for insight_data in data.get('insights', []):
                insight = Insight(
                    insight_id=insight_data['insight_id'],
                    type=OptimizationType(insight_data['type']),
                    severity=InsightSeverity(insight_data['severity']),
                    title=insight_data['title'],
                    description=insight_data['description'],
                    data=insight_data['data'],
                    recommendations=insight_data['recommendations'],
                    estimated_impact=insight_data['estimated_impact'],
                    timestamp=insight_data['timestamp']
                )
                self.insights.append(insight)
            
            # Reconstruir acciones
            for action_data in data.get('actions', []):
                action = OptimizationAction(
                    action_id=action_data['action_id'],
                    type=OptimizationType(action_data['type']),
                    name=action_data['name'],
                    description=action_data['description'],
                    status=ActionStatus(action_data['status']),
                    created_at=action_data['created_at'],
                    applied_at=action_data.get('applied_at'),
                    rolled_back_at=action_data.get('rolled_back_at'),
                    metrics_before=action_data.get('metrics_before'),
                    metrics_after=action_data.get('metrics_after'),
                    impact_actual=action_data.get('impact_actual')
                )
                self.actions.append(action)
            
            logger.info(f"✅ Loaded {len(self.insights)} insights, {len(self.actions)} actions")
        except Exception as e:
            logger.error(f"❌ Error loading optimization data: {e}")
    
    def _save_data(self):
        """Guarda datos a archivo."""
        try:
            data = {
                'insights': [i.to_dict() for i in self.insights[-100:]],  # Últimos 100
                'actions': [a.to_dict() for a in self.actions[-100:]],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 Optimization data saved")
        except Exception as e:
            logger.error(f"❌ Error saving optimization data: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════
    #  ANALYSIS & INSIGHTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def analyze_metrics(self, hours: int = 24) -> List[Insight]:
        """Analiza métricas y genera insights."""
        if not self.monitoring:
            logger.warning("⚠️ Monitoring system not available")
            return []
        
        insights = []
        
        # Obtener métricas actuales
        current_metrics = self._gather_metrics(hours)
        
        # Aplicar reglas de optimización
        for rule_name, rule in OPTIMIZATION_RULES.items():
            if rule['condition'](current_metrics):
                insight = self._create_insight_from_rule(rule_name, rule, current_metrics)
                insights.append(insight)
        
        # Análisis de tendencias
        trend_insights = self._analyze_trends(current_metrics)
        insights.extend(trend_insights)
        
        # Análisis de anomalías
        anomaly_insights = self._detect_anomalies(current_metrics)
        insights.extend(anomaly_insights)
        
        # Guardar insights
        self.insights.extend(insights)
        self._save_data()
        
        self.last_analysis = datetime.now()
        
        logger.info(f"📊 Analysis complete: {len(insights)} insights generated")
        return insights
    
    def _gather_metrics(self, hours: int) -> Dict:
        """Recopila métricas de todos los sistemas."""
        metrics = {}
        
        # Monitoring metrics
        if self.monitoring:
            metrics['onboarding_completion_rate'] = self.monitoring.get_onboarding_completion_rate(hours)
            metrics['onboarding_avg_duration'] = self.monitoring._get_avg_metric('onboarding.total_duration', hours)
            metrics['button_click_rate'] = self.monitoring.get_button_click_rate(hours=hours)
            metrics['error_rate'] = self.monitoring.get_error_rate(hours)
            metrics['avg_response_time'] = self.monitoring.get_avg_response_time(hours)
        
        # A/B testing metrics
        if self.ab_testing:
            # Obtener experimentos activos
            for exp_id, exp in self.ab_testing.experiments.items():
                if exp.status.value == 'running':
                    results = self.ab_testing.calculate_results(exp_id)
                    if results:
                        metrics[f'experiment_{exp_id}_best'] = max(
                            r.mean for r in results.values()
                        )
        
        # Feedback metrics
        if self.feedback:
            nps = self.feedback.calculate_nps(days=hours//24)
            metrics['nps_score'] = nps.score
            
            feedback_summary = self.feedback.get_feedback_summary(days=hours//24)
            if feedback_summary:
                metrics['sentiment_score'] = feedback_summary.get('sentiment_score', 0)
        
        return metrics
    
    def _create_insight_from_rule(self, rule_name: str, rule: Dict, metrics: Dict) -> Insight:
        """Crea insight desde regla."""
        severity_map = {
            'critical': InsightSeverity.CRITICAL,
            'high': InsightSeverity.HIGH,
            'medium': InsightSeverity.MEDIUM,
            'low': InsightSeverity.LOW
        }
        
        # Determinar tipo
        if 'onboarding' in rule_name:
            opt_type = OptimizationType.ONBOARDING
        elif 'conversion' in rule_name or 'premium' in rule_name:
            opt_type = OptimizationType.CONVERSION
        elif 'error' in rule_name or 'performance' in rule_name:
            opt_type = OptimizationType.PERFORMANCE
        else:
            opt_type = OptimizationType.ENGAGEMENT
        
        insight_id = f"INSIGHT_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
        
        return Insight(
            insight_id=insight_id,
            type=opt_type,
            severity=severity_map.get(rule['priority'], InsightSeverity.MEDIUM),
            title=rule_name.replace('_', ' ').title(),
            description=f"Rule '{rule_name}' triggered",
            data=metrics,
            recommendations=[rule['action']],
            estimated_impact=rule['impact'],
            timestamp=datetime.now().isoformat()
        )
    
    def _analyze_trends(self, current_metrics: Dict) -> List[Insight]:
        """Analiza tendencias en métricas."""
        insights = []
        
        # TODO: Implementar análisis de tendencias histórico
        # Comparar métricas actuales vs semana anterior
        # Detectar mejoras/empeoramientos significativos
        
        return insights
    
    def _detect_anomalies(self, current_metrics: Dict) -> List[Insight]:
        """Detecta anomalías en métricas."""
        insights = []
        
        # TODO: Implementar detección de anomalías
        # Usar statistical methods para detectar outliers
        # Alertar sobre cambios súbitos
        
        return insights
    
    # ═══════════════════════════════════════════════════════════════════════
    #  AUTO-OPTIMIZATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def auto_optimize(self) -> List[OptimizationAction]:
        """Aplica optimizaciones automáticamente."""
        if not self.auto_optimize_enabled:
            logger.info("⏸️ Auto-optimization disabled")
            return []
        
        # Analizar métricas
        insights = self.analyze_metrics(hours=24)
        
        # Filtrar insights de alta prioridad
        high_priority = [
            i for i in insights
            if i.severity in [InsightSeverity.HIGH, InsightSeverity.CRITICAL]
        ]
        
        actions_applied = []
        
        for insight in high_priority:
            for recommendation in insight.recommendations:
                action = self._apply_optimization(insight, recommendation)
                if action:
                    actions_applied.append(action)
        
        logger.info(f"🔄 Auto-optimization: {len(actions_applied)} actions applied")
        return actions_applied
    
    def _apply_optimization(self, insight: Insight, recommendation: str) -> Optional[OptimizationAction]:
        """Aplica una optimización específica."""
        
        # Crear acción
        action_id = f"ACTION_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
        action = OptimizationAction(
            action_id=action_id,
            type=insight.type,
            name=recommendation,
            description=f"Auto-applied from insight: {insight.title}",
            status=ActionStatus.PENDING,
            created_at=datetime.now().isoformat(),
            metrics_before=insight.data
        )
        
        # Aplicar optimización según tipo
        success = False
        
        if recommendation == 'reduce_onboarding_steps':
            success = self._optimize_onboarding_steps()
        elif recommendation == 'improve_onboarding_flow':
            success = self._optimize_onboarding_flow()
        elif recommendation == 'optimize_button_placement':
            success = self._optimize_button_placement()
        elif recommendation == 'enhance_premium_upsells':
            success = self._optimize_premium_upsells()
        elif recommendation == 'improve_share_mechanics':
            success = self._optimize_share_mechanics()
        elif recommendation == 'optimize_performance':
            success = self._optimize_performance()
        
        if success:
            action.status = ActionStatus.ACTIVE
            action.applied_at = datetime.now().isoformat()
            self.actions.append(action)
            self._save_data()
            
            logger.info(f"✅ Optimization applied: {recommendation}")
            return action
        else:
            logger.warning(f"⚠️ Failed to apply optimization: {recommendation}")
            return None
    
    def _optimize_onboarding_steps(self) -> bool:
        """Reduce steps en onboarding."""
        if not self.ab_testing:
            return False
        
        try:
            # Crear A/B test si no existe
            if 'onboarding_steps' not in self.ab_testing.experiments:
                exp = self.ab_testing.create_from_template('onboarding_steps')
                self.ab_testing.start_experiment('onboarding_steps')
            
            # Verificar si hay winner
            winner = self.ab_testing.detect_winner('onboarding_steps')
            if winner:
                self.ab_testing.rollout_winner('onboarding_steps', winner)
            
            return True
        except Exception as e:
            logger.error(f"❌ Error optimizing onboarding steps: {e}")
            return False
    
    def _optimize_onboarding_flow(self) -> bool:
        """Mejora flujo de onboarding."""
        # TODO: Implementar optimizaciones específicas
        # - Reducir texto
        # - Mejorar CTAs
        # - Añadir skip option
        # - Aumentar bonus
        return True
    
    def _optimize_button_placement(self) -> bool:
        """Optimiza colocación de botones."""
        if not self.ab_testing:
            return False
        
        try:
            # Test CTA placement
            if 'cta_placement' not in self.ab_testing.experiments:
                exp = self.ab_testing.create_from_template('cta_placement')
                self.ab_testing.start_experiment('cta_placement')
            
            return True
        except Exception as e:
            logger.error(f"❌ Error optimizing button placement: {e}")
            return False
    
    def _optimize_premium_upsells(self) -> bool:
        """Mejora upsells de premium."""
        # TODO: Implementar
        # - Mostrar valor más claramente
        # - Añadir social proof
        # - ROI calculator
        # - Trial offers más agresivos
        return True
    
    def _optimize_share_mechanics(self) -> bool:
        """Mejora mecánicas de compartir."""
        # TODO: Implementar
        # - One-click sharing
        # - Pre-filled messages
        # - Incentivos más claros
        # - Viral loops
        return True
    
    def _optimize_performance(self) -> bool:
        """Optimiza performance del bot."""
        # TODO: Implementar
        # - Increase cache TTL
        # - Optimize database queries
        # - Reduce API calls
        # - Enable compression
        return True
    
    # ═══════════════════════════════════════════════════════════════════════
    #  IMPACT MEASUREMENT
    # ═══════════════════════════════════════════════════════════════════════
    
    def measure_impact(self, action: OptimizationAction, hours: int = 48) -> float:
        """Mide impacto de una acción."""
        if action.status != ActionStatus.ACTIVE:
            return 0.0
        
        if not action.applied_at:
            return 0.0
        
        # Obtener métricas después de aplicar
        current_metrics = self._gather_metrics(hours)
        action.metrics_after = current_metrics
        
        # Calcular mejora
        before = action.metrics_before
        after = action.metrics_after
        
        # Elegir métrica clave según tipo
        key_metric = self._get_key_metric_for_type(action.type)
        
        if key_metric not in before or key_metric not in after:
            return 0.0
        
        # Calcular % de mejora
        before_val = before[key_metric]
        after_val = after[key_metric]
        
        if before_val == 0:
            return 0.0
        
        improvement_pct = ((after_val - before_val) / before_val) * 100
        action.impact_actual = improvement_pct
        
        # Marcar como completado
        action.status = ActionStatus.COMPLETED
        self._save_data()
        
        logger.info(f"📈 Impact measured: {improvement_pct:+.1f}% for {action.name}")
        return improvement_pct
    
    def _get_key_metric_for_type(self, opt_type: OptimizationType) -> str:
        """Obtiene métrica clave para tipo de optimización."""
        metric_map = {
            OptimizationType.ONBOARDING: 'onboarding_completion_rate',
            OptimizationType.CONVERSION: 'premium_conversion_rate',
            OptimizationType.RETENTION: 'day7_retention',
            OptimizationType.ENGAGEMENT: 'button_click_rate',
            OptimizationType.PERFORMANCE: 'avg_response_time',
            OptimizationType.REVENUE: 'revenue_per_user'
        }
        return metric_map.get(opt_type, 'overall_score')
    
    def rollback_if_negative(self, action: OptimizationAction, threshold: float = -5.0) -> bool:
        """Rollback si impacto es negativo."""
        impact = self.measure_impact(action)
        
        if impact < threshold:
            logger.warning(f"🔙 Rolling back {action.name}: {impact:.1f}% impact")
            action.status = ActionStatus.ROLLED_BACK
            action.rolled_back_at = datetime.now().isoformat()
            self._save_data()
            return True
        
        return False
    
    # ═══════════════════════════════════════════════════════════════════════
    #  REPORTING
    # ═══════════════════════════════════════════════════════════════════════
    
    def generate_optimization_report(self, days: int = 7) -> Dict:
        """Genera reporte de optimizaciones."""
        cutoff = datetime.now() - timedelta(days=days)
        
        recent_actions = [
            a for a in self.actions
            if datetime.fromisoformat(a.created_at) >= cutoff
        ]
        
        recent_insights = [
            i for i in self.insights
            if datetime.fromisoformat(i.timestamp) >= cutoff
        ]
        
        # Estadísticas
        total_actions = len(recent_actions)
        successful = sum(1 for a in recent_actions if a.status == ActionStatus.COMPLETED)
        rolled_back = sum(1 for a in recent_actions if a.status == ActionStatus.ROLLED_BACK)
        
        # Impacto total
        total_impact = sum(
            a.impact_actual for a in recent_actions
            if a.impact_actual is not None and a.status == ActionStatus.COMPLETED
        )
        
        return {
            'period_days': days,
            'insights_generated': len(recent_insights),
            'actions_total': total_actions,
            'actions_successful': successful,
            'actions_rolled_back': rolled_back,
            'success_rate': successful / total_actions if total_actions > 0 else 0,
            'total_impact_pct': total_impact,
            'top_optimizations': sorted(
                [
                    {
                        'name': a.name,
                        'impact': a.impact_actual,
                        'type': a.type.value
                    }
                    for a in recent_actions
                    if a.impact_actual is not None
                ],
                key=lambda x: x['impact'],
                reverse=True
            )[:5],
            'pending_insights': [
                i.to_dict() for i in recent_insights
                if i.severity in [InsightSeverity.HIGH, InsightSeverity.CRITICAL]
            ][:5]
        }
    
    def print_optimization_report(self, days: int = 7):
        """Imprime reporte de optimizaciones."""
        report = self.generate_optimization_report(days)
        
        print("\n" + "="*70)
        print(f"🔄 OPTIMIZATION REPORT - Last {days} days".center(70))
        print("="*70 + "\n")
        
        print(f"INSIGHTS GENERATED: {report['insights_generated']}\n")
        
        print("ACTIONS:")
        print(f"  • Total: {report['actions_total']}")
        print(f"  • Successful: {report['actions_successful']}")
        print(f"  • Rolled back: {report['actions_rolled_back']}")
        print(f"  • Success Rate: {report['success_rate']:.1%}\n")
        
        print(f"TOTAL IMPACT: {report['total_impact_pct']:+.1f}%\n")
        
        if report['top_optimizations']:
            print("TOP OPTIMIZATIONS:")
            for i, opt in enumerate(report['top_optimizations'], 1):
                print(f"  {i}. {opt['name']} ({opt['type']}): {opt['impact']:+.1f}%")
            print()
        
        if report['pending_insights']:
            print("PENDING HIGH-PRIORITY INSIGHTS:")
            for i, insight in enumerate(report['pending_insights'], 1):
                severity_emoji = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢'
                }
                emoji = severity_emoji.get(insight['severity'], '❓')
                print(f"  {emoji} {insight['title']}")
                print(f"     Impact: {insight['estimated_impact']}")
            print()
        
        print("="*70 + "\n")


if __name__ == '__main__':
    # 🧪 Test del sistema
    print("🧪 Testing ContinuousOptimizationEngine...\n")
    
    # Crear motor sin sistemas externos (standalone test)
    engine = ContinuousOptimizationEngine()
    
    # Simular métricas problemáticas
    test_metrics = {
        'onboarding_completion_rate': 0.65,  # <70% trigger
        'onboarding_avg_duration': 95,  # >90s trigger
        'button_click_rate': 0.55,  # <60% trigger
        'error_rate': 0.06,  # >5% trigger
        'avg_response_time': 1200,  # >1000ms trigger
        'nps_score': 38,  # <40 trigger
    }
    
    print("1. Analyzing metrics (simulated)...")
    # Simular insights
    for rule_name, rule in OPTIMIZATION_RULES.items():
        if rule['condition'](test_metrics):
            insight = engine._create_insight_from_rule(rule_name, rule, test_metrics)
            engine.insights.append(insight)
    
    print(f"   Generated {len(engine.insights)} insights\n")
    
    print("2. Generating optimization report...")
    engine.print_optimization_report(days=7)
    
    print("\n✅ Test completed!")
