#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════╗
║  📊 REAL-TIME MONITORING SYSTEM                                  ║
║  🚀 Cazador Supremo v14.2                                        ║
║  ⏱️ 48h Continuous Monitoring + Alerts                           ║
╚═══════════════════════════════════════════════════════════════════╝

Sistema completo de monitorización:
- Métricas en tiempo real
- Dashboards interactivos
- Alertas automáticas
- Reportes programados

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
from collections import defaultdict, deque
from enum import Enum
import threading
import time

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════

class MetricType(Enum):
    """Tipos de métricas"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    RATE = "rate"


class AlertSeverity(Enum):
    """Severidad de alertas"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Thresholds para alertas
ALERT_THRESHOLDS = {
    'onboarding_completion_rate': {'min': 0.60, 'target': 0.70},  # <60% alerta
    'button_click_rate': {'min': 0.50, 'target': 0.70},
    'error_rate': {'max': 0.05, 'target': 0.02},  # >5% alerta
    'user_satisfaction': {'min': 4.0, 'target': 4.5},  # <4.0 alerta
    'response_time_ms': {'max': 2000, 'target': 500},
    'cache_hit_rate': {'min': 0.60, 'target': 0.75},
}

# Intervalos de reporte
REPORT_INTERVALS = {
    'realtime': 60,      # 1 minuto
    'hourly': 3600,      # 1 hora
    'daily': 86400,      # 24 horas
    '48h': 172800,       # 48 horas
}


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class Metric:
    """Métrica individual"""
    name: str
    type: MetricType
    value: float
    timestamp: str
    tags: Dict[str, str] = None
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'type': self.type.value,
            'value': self.value,
            'timestamp': self.timestamp,
            'tags': self.tags or {}
        }


@dataclass
class Alert:
    """Alerta de monitorización"""
    severity: AlertSeverity
    metric: str
    message: str
    value: float
    threshold: float
    timestamp: str
    resolved: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'severity': self.severity.value,
            'metric': self.metric,
            'message': self.message,
            'value': self.value,
            'threshold': self.threshold,
            'timestamp': self.timestamp,
            'resolved': self.resolved
        }


@dataclass
class MonitoringReport:
    """Reporte de monitorización"""
    start_time: str
    end_time: str
    duration_hours: float
    metrics: Dict[str, Dict]
    alerts: List[Alert]
    summary: Dict[str, any]
    recommendations: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_hours': self.duration_hours,
            'metrics': self.metrics,
            'alerts': [a.to_dict() for a in self.alerts],
            'summary': self.summary,
            'recommendations': self.recommendations
        }


# ═══════════════════════════════════════════════════════════════
#  MONITORING SYSTEM
# ═══════════════════════════════════════════════════════════════

class MonitoringSystem:
    """
    Sistema completo de monitorización.
    
    Features:
    - Tracking de métricas en tiempo real
    - Detección de anomalías
    - Alertas automáticas
    - Reportes programados
    - Dashboards interactivos
    """
    
    def __init__(self, 
                 data_file: str = 'monitoring_data.json',
                 alerts_file: str = 'monitoring_alerts.json'):
        self.data_file = Path(data_file)
        self.alerts_file = Path(alerts_file)
        
        # Storage de métricas
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.alerts: List[Alert] = []
        
        # Tracking state
        self.monitoring_start = datetime.now()
        self.last_report = datetime.now()
        
        # Thread-safe
        self.lock = threading.Lock()
        
        self._load_data()
        
        logger.info("📊 MonitoringSystem initialized")
    
    def _load_data(self):
        """Carga datos históricos."""
        if not self.data_file.exists():
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruir métricas
            for metric_name, values in data.get('metrics', {}).items():
                for value_data in values:
                    metric = Metric(
                        name=metric_name,
                        type=MetricType(value_data['type']),
                        value=value_data['value'],
                        timestamp=value_data['timestamp'],
                        tags=value_data.get('tags', {})
                    )
                    self.metrics[metric_name].append(metric)
            
            logger.info(f"✅ Loaded {len(self.metrics)} metric types")
        except Exception as e:
            logger.error(f"❌ Error loading monitoring data: {e}")
    
    def _save_data(self):
        """Guarda datos a archivo."""
        try:
            data = {
                'monitoring_start': self.monitoring_start.isoformat(),
                'last_updated': datetime.now().isoformat(),
                'metrics': {}
            }
            
            # Serializar métricas
            for metric_name, values in self.metrics.items():
                data['metrics'][metric_name] = [
                    m.to_dict() for m in list(values)[-1000:]  # Últimas 1000
                ]
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 Monitoring data saved")
        except Exception as e:
            logger.error(f"❌ Error saving monitoring data: {e}")
    
    # ═══════════════════════════════════════════════════════════
    #  METRIC RECORDING
    # ═══════════════════════════════════════════════════════════
    
    def record_counter(self, name: str, value: float = 1, tags: Dict = None):
        """Registra métrica de contador."""
        metric = Metric(
            name=name,
            type=MetricType.COUNTER,
            value=value,
            timestamp=datetime.now().isoformat(),
            tags=tags
        )
        
        with self.lock:
            self.metrics[name].append(metric)
    
    def record_gauge(self, name: str, value: float, tags: Dict = None):
        """Registra métrica de gauge."""
        metric = Metric(
            name=name,
            type=MetricType.GAUGE,
            value=value,
            timestamp=datetime.now().isoformat(),
            tags=tags
        )
        
        with self.lock:
            self.metrics[name].append(metric)
    
    def record_histogram(self, name: str, value: float, tags: Dict = None):
        """Registra valor en histograma."""
        metric = Metric(
            name=name,
            type=MetricType.HISTOGRAM,
            value=value,
            timestamp=datetime.now().isoformat(),
            tags=tags
        )
        
        with self.lock:
            self.metrics[name].append(metric)
    
    # ═══════════════════════════════════════════════════════════
    #  ONBOARDING METRICS
    # ═══════════════════════════════════════════════════════════
    
    def track_onboarding_start(self, user_id: int):
        """Track inicio de onboarding."""
        self.record_counter('onboarding.started', tags={'user_id': str(user_id)})
    
    def track_onboarding_step(self, user_id: int, step: int, duration_seconds: float):
        """Track completación de step."""
        self.record_counter(f'onboarding.step{step}.completed', tags={'user_id': str(user_id)})
        self.record_histogram(f'onboarding.step{step}.duration', duration_seconds)
    
    def track_onboarding_completion(self, user_id: int, total_duration: float, skipped: bool = False):
        """Track completación de onboarding."""
        if skipped:
            self.record_counter('onboarding.skipped', tags={'user_id': str(user_id)})
        else:
            self.record_counter('onboarding.completed', tags={'user_id': str(user_id)})
            self.record_histogram('onboarding.total_duration', total_duration)
            
            # Alert si excede TTFV target
            if total_duration > 90:
                self._create_alert(
                    AlertSeverity.WARNING,
                    'onboarding.ttfv',
                    f'TTFV exceeded target: {total_duration:.0f}s > 90s',
                    total_duration,
                    90
                )
    
    def get_onboarding_completion_rate(self, hours: int = 24) -> float:
        """Calcula tasa de completación de onboarding."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        started = sum(1 for m in self.metrics['onboarding.started'] 
                     if datetime.fromisoformat(m.timestamp) >= cutoff)
        completed = sum(1 for m in self.metrics['onboarding.completed'] 
                       if datetime.fromisoformat(m.timestamp) >= cutoff)
        
        if started == 0:
            return 0.0
        
        rate = completed / started
        
        # Check threshold
        if rate < ALERT_THRESHOLDS['onboarding_completion_rate']['min']:
            self._create_alert(
                AlertSeverity.WARNING,
                'onboarding_completion_rate',
                f'Low completion rate: {rate:.1%} < 60%',
                rate,
                ALERT_THRESHOLDS['onboarding_completion_rate']['min']
            )
        
        return rate
    
    # ═══════════════════════════════════════════════════════════
    #  BUTTON CLICK METRICS
    # ═══════════════════════════════════════════════════════════
    
    def track_button_click(self, button_id: str, user_id: int, context: str = None):
        """Track click en botón."""
        self.record_counter(
            'button.clicked',
            tags={
                'button_id': button_id,
                'user_id': str(user_id),
                'context': context or 'unknown'
            }
        )
    
    def track_button_impression(self, button_id: str, user_id: int):
        """Track impresión de botón."""
        self.record_counter(
            'button.impression',
            tags={
                'button_id': button_id,
                'user_id': str(user_id)
            }
        )
    
    def get_button_click_rate(self, button_id: str = None, hours: int = 24) -> float:
        """Calcula CTR de botones."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        clicks_metric = 'button.clicked'
        impressions_metric = 'button.impression'
        
        if button_id:
            clicks = sum(1 for m in self.metrics[clicks_metric]
                        if datetime.fromisoformat(m.timestamp) >= cutoff
                        and m.tags.get('button_id') == button_id)
            impressions = sum(1 for m in self.metrics[impressions_metric]
                            if datetime.fromisoformat(m.timestamp) >= cutoff
                            and m.tags.get('button_id') == button_id)
        else:
            clicks = sum(1 for m in self.metrics[clicks_metric]
                        if datetime.fromisoformat(m.timestamp) >= cutoff)
            impressions = sum(1 for m in self.metrics[impressions_metric]
                            if datetime.fromisoformat(m.timestamp) >= cutoff)
        
        if impressions == 0:
            return 0.0
        
        ctr = clicks / impressions
        
        # Check threshold
        if ctr < ALERT_THRESHOLDS['button_click_rate']['min']:
            self._create_alert(
                AlertSeverity.INFO,
                'button_click_rate',
                f'Low CTR: {ctr:.1%} < 50%',
                ctr,
                ALERT_THRESHOLDS['button_click_rate']['min']
            )
        
        return ctr
    
    def get_top_buttons(self, hours: int = 24, limit: int = 10) -> List[Tuple[str, int]]:
        """Obtiene botones más clickeados."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        button_clicks = defaultdict(int)
        
        for metric in self.metrics['button.clicked']:
            if datetime.fromisoformat(metric.timestamp) >= cutoff:
                button_id = metric.tags.get('button_id', 'unknown')
                button_clicks[button_id] += 1
        
        return sorted(button_clicks.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    # ═══════════════════════════════════════════════════════════
    #  ERROR TRACKING
    # ═══════════════════════════════════════════════════════════
    
    def track_error(self, error_type: str, error_message: str, user_id: int = None):
        """Track error."""
        self.record_counter(
            'error.occurred',
            tags={
                'type': error_type,
                'user_id': str(user_id) if user_id else 'system'
            }
        )
        
        logger.error(f"Error tracked: {error_type} - {error_message}")
    
    def get_error_rate(self, hours: int = 24) -> float:
        """Calcula tasa de errores."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        errors = sum(1 for m in self.metrics['error.occurred']
                    if datetime.fromisoformat(m.timestamp) >= cutoff)
        
        # Total de requests (aproximado por comandos)
        total_requests = sum(
            sum(1 for m in metrics
                if datetime.fromisoformat(m.timestamp) >= cutoff)
            for metric_name, metrics in self.metrics.items()
            if metric_name.startswith('command.')
        )
        
        if total_requests == 0:
            return 0.0
        
        error_rate = errors / total_requests
        
        # Check threshold
        if error_rate > ALERT_THRESHOLDS['error_rate']['max']:
            self._create_alert(
                AlertSeverity.ERROR,
                'error_rate',
                f'High error rate: {error_rate:.1%} > 5%',
                error_rate,
                ALERT_THRESHOLDS['error_rate']['max']
            )
        
        return error_rate
    
    # ═══════════════════════════════════════════════════════════
    #  PERFORMANCE METRICS
    # ═══════════════════════════════════════════════════════════
    
    def track_response_time(self, command: str, duration_ms: float):
        """Track tiempo de respuesta."""
        self.record_histogram(
            'response_time',
            duration_ms,
            tags={'command': command}
        )
        
        # Alert si excede threshold
        if duration_ms > ALERT_THRESHOLDS['response_time_ms']['max']:
            self._create_alert(
                AlertSeverity.WARNING,
                'response_time',
                f'Slow response: {duration_ms:.0f}ms > 2000ms',
                duration_ms,
                ALERT_THRESHOLDS['response_time_ms']['max']
            )
    
    def get_avg_response_time(self, hours: int = 24) -> float:
        """Calcula tiempo de respuesta promedio."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        times = [m.value for m in self.metrics['response_time']
                if datetime.fromisoformat(m.timestamp) >= cutoff]
        
        return sum(times) / len(times) if times else 0.0
    
    def get_p95_response_time(self, hours: int = 24) -> float:
        """Calcula p95 de tiempo de respuesta."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        times = sorted([m.value for m in self.metrics['response_time']
                       if datetime.fromisoformat(m.timestamp) >= cutoff])
        
        if not times:
            return 0.0
        
        p95_index = int(len(times) * 0.95)
        return times[p95_index]
    
    # ═══════════════════════════════════════════════════════════
    #  ALERTS
    # ═══════════════════════════════════════════════════════════
    
    def _create_alert(self, severity: AlertSeverity, metric: str, 
                     message: str, value: float, threshold: float):
        """Crea alerta."""
        alert = Alert(
            severity=severity,
            metric=metric,
            message=message,
            value=value,
            threshold=threshold,
            timestamp=datetime.now().isoformat()
        )
        
        with self.lock:
            self.alerts.append(alert)
        
        logger.warning(f"🚨 Alert: {message}")
    
    def get_active_alerts(self, severity: AlertSeverity = None) -> List[Alert]:
        """Obtiene alertas activas."""
        alerts = [a for a in self.alerts if not a.resolved]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return alerts
    
    def resolve_alert(self, alert: Alert):
        """Marca alerta como resuelta."""
        alert.resolved = True
    
    # ═══════════════════════════════════════════════════════════
    #  REPORTS
    # ═══════════════════════════════════════════════════════════
    
    def generate_report(self, hours: int = 48) -> MonitoringReport:
        """Genera reporte de monitorización."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Calcular métricas
        metrics = {
            'onboarding': {
                'completion_rate': self.get_onboarding_completion_rate(hours),
                'avg_duration': self._get_avg_metric('onboarding.total_duration', hours),
                'started': self._count_metric('onboarding.started', hours),
                'completed': self._count_metric('onboarding.completed', hours),
                'skipped': self._count_metric('onboarding.skipped', hours),
            },
            'buttons': {
                'click_rate': self.get_button_click_rate(hours=hours),
                'total_clicks': self._count_metric('button.clicked', hours),
                'total_impressions': self._count_metric('button.impression', hours),
                'top_buttons': self.get_top_buttons(hours),
            },
            'performance': {
                'avg_response_time': self.get_avg_response_time(hours),
                'p95_response_time': self.get_p95_response_time(hours),
                'error_rate': self.get_error_rate(hours),
                'total_errors': self._count_metric('error.occurred', hours),
            },
        }
        
        # Generar resumen
        summary = self._generate_summary(metrics)
        
        # Generar recomendaciones
        recommendations = self._generate_recommendations(metrics)
        
        report = MonitoringReport(
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration_hours=hours,
            metrics=metrics,
            alerts=self.get_active_alerts(),
            summary=summary,
            recommendations=recommendations
        )
        
        return report
    
    def _count_metric(self, metric_name: str, hours: int) -> int:
        """Cuenta ocurrencias de métrica."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return sum(1 for m in self.metrics[metric_name]
                  if datetime.fromisoformat(m.timestamp) >= cutoff)
    
    def _get_avg_metric(self, metric_name: str, hours: int) -> float:
        """Calcula promedio de métrica."""
        cutoff = datetime.now() - timedelta(hours=hours)
        values = [m.value for m in self.metrics[metric_name]
                 if datetime.fromisoformat(m.timestamp) >= cutoff]
        return sum(values) / len(values) if values else 0.0
    
    def _generate_summary(self, metrics: Dict) -> Dict:
        """Genera resumen ejecutivo."""
        onb_rate = metrics['onboarding']['completion_rate']
        btn_rate = metrics['buttons']['click_rate']
        error_rate = metrics['performance']['error_rate']
        
        status = 'healthy'
        if error_rate > 0.05 or onb_rate < 0.60 or btn_rate < 0.50:
            status = 'warning'
        if error_rate > 0.10 or onb_rate < 0.50:
            status = 'critical'
        
        return {
            'overall_status': status,
            'health_score': self._calculate_health_score(metrics),
            'key_metrics': {
                'onboarding_completion': f"{onb_rate:.1%}",
                'button_ctr': f"{btn_rate:.1%}",
                'error_rate': f"{error_rate:.1%}",
            },
            'alerts_count': len(self.get_active_alerts()),
        }
    
    def _calculate_health_score(self, metrics: Dict) -> float:
        """Calcula health score (0-100)."""
        score = 100.0
        
        # Onboarding (30 points)
        onb_rate = metrics['onboarding']['completion_rate']
        if onb_rate < 0.70:
            score -= (0.70 - onb_rate) * 100
        
        # Buttons (20 points)
        btn_rate = metrics['buttons']['click_rate']
        if btn_rate < 0.70:
            score -= (0.70 - btn_rate) * 50
        
        # Performance (30 points)
        error_rate = metrics['performance']['error_rate']
        if error_rate > 0.02:
            score -= (error_rate - 0.02) * 500
        
        # Response time (20 points)
        avg_time = metrics['performance']['avg_response_time']
        if avg_time > 500:
            score -= (avg_time - 500) / 100
        
        return max(0.0, min(100.0, score))
    
    def _generate_recommendations(self, metrics: Dict) -> List[str]:
        """Genera recomendaciones basadas en métricas."""
        recommendations = []
        
        # Onboarding
        onb_rate = metrics['onboarding']['completion_rate']
        if onb_rate < 0.70:
            recommendations.append(
                f"⚠️ Onboarding completion rate is {onb_rate:.1%}. "
                f"Consider: shorter flow, better UX, more incentives."
            )
        
        avg_duration = metrics['onboarding']['avg_duration']
        if avg_duration > 90:
            recommendations.append(
                f"⏱️ Onboarding takes {avg_duration:.0f}s (target: <90s). "
                f"Optimize: reduce steps, pre-fill data, skip options."
            )
        
        # Buttons
        btn_rate = metrics['buttons']['click_rate']
        if btn_rate < 0.70:
            recommendations.append(
                f"🔘 Button CTR is {btn_rate:.1%}. "
                f"Improve: better CTAs, positioning, visual hierarchy."
            )
        
        # Performance
        error_rate = metrics['performance']['error_rate']
        if error_rate > 0.02:
            recommendations.append(
                f"🐛 Error rate is {error_rate:.1%} (target: <2%). "
                f"Action: review logs, fix bugs, add error handling."
            )
        
        avg_time = metrics['performance']['avg_response_time']
        if avg_time > 500:
            recommendations.append(
                f"⚡ Response time is {avg_time:.0f}ms (target: <500ms). "
                f"Optimize: cache, database queries, async operations."
            )
        
        if not recommendations:
            recommendations.append("✅ All metrics are healthy! Keep monitoring.")
        
        return recommendations
    
    def save_report(self, report: MonitoringReport, filename: str = None):
        """Guarda reporte a archivo."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"monitoring_report_{timestamp}.json"
        
        filepath = Path('reports') / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Report saved: {filepath}")
        return filepath
    
    def print_dashboard(self, hours: int = 24):
        """Imprime dashboard en consola."""
        report = self.generate_report(hours)
        
        print("\n" + "="*70)
        print(f"📊 MONITORING DASHBOARD - Last {hours}h".center(70))
        print("="*70 + "\n")
        
        # Summary
        summary = report.summary
        status_emoji = {'healthy': '✅', 'warning': '⚠️', 'critical': '🚨'}
        print(f"Status: {status_emoji[summary['overall_status']]} {summary['overall_status'].upper()}")
        print(f"Health Score: {summary['health_score']:.1f}/100\n")
        
        # Key metrics
        print("KEY METRICS:")
        for metric, value in summary['key_metrics'].items():
            print(f"  • {metric}: {value}")
        print()
        
        # Onboarding
        onb = report.metrics['onboarding']
        print("ONBOARDING:")
        print(f"  • Started: {onb['started']}")
        print(f"  • Completed: {onb['completed']}")
        print(f"  • Completion Rate: {onb['completion_rate']:.1%}")
        print(f"  • Avg Duration: {onb['avg_duration']:.0f}s\n")
        
        # Buttons
        btns = report.metrics['buttons']
        print("BUTTONS:")
        print(f"  • Click Rate: {btns['click_rate']:.1%}")
        print(f"  • Total Clicks: {btns['total_clicks']}")
        print(f"  • Top 5:")
        for btn_id, clicks in btns['top_buttons'][:5]:
            print(f"    - {btn_id}: {clicks} clicks")
        print()
        
        # Performance
        perf = report.metrics['performance']
        print("PERFORMANCE:")
        print(f"  • Avg Response: {perf['avg_response_time']:.0f}ms")
        print(f"  • P95 Response: {perf['p95_response_time']:.0f}ms")
        print(f"  • Error Rate: {perf['error_rate']:.1%}\n")
        
        # Alerts
        if report.alerts:
            print(f"ACTIVE ALERTS ({len(report.alerts)}):")
            for alert in report.alerts[:5]:
                severity_emoji = {
                    AlertSeverity.INFO: 'ℹ️',
                    AlertSeverity.WARNING: '⚠️',
                    AlertSeverity.ERROR: '❌',
                    AlertSeverity.CRITICAL: '🚨'
                }
                print(f"  {severity_emoji[alert.severity]} {alert.message}")
            print()
        
        # Recommendations
        print("RECOMMENDATIONS:")
        for rec in report.recommendations:
            print(f"  {rec}")
        
        print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    # 🧪 Test del sistema
    print("🧪 Testing MonitoringSystem...\n")
    
    monitor = MonitoringSystem()
    
    # Simular métricas
    print("1. Simulating onboarding...")
    for i in range(100):
        monitor.track_onboarding_start(10000 + i)
        if i < 75:  # 75% completion
            monitor.track_onboarding_completion(10000 + i, 60 + i % 30)
    
    print("2. Simulating button clicks...")
    buttons = ['onb_region_europe', 'onb_budget_medium', 'scan', 'deals', 'premium']
    for i in range(500):
        button = buttons[i % len(buttons)]
        monitor.track_button_impression(button, 10000 + i % 100)
        if i % 2 == 0:  # 50% CTR
            monitor.track_button_click(button, 10000 + i % 100)
    
    print("3. Simulating performance...")
    for i in range(200):
        monitor.track_response_time('scan', 300 + i % 500)
    
    print("4. Generating report...\n")
    monitor.print_dashboard(hours=24)
    
    print("\n✅ Test completed!")
