#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Value Metrics Dashboard - IT6 Day 3/5
Sistema de métricas de valor para demostrar ROI al usuario

Author: @Juanka_Spain
Version: 13.2.0
Date: 2026-01-16
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class MetricCategory(Enum):
    """Categorías de métricas"""
    SAVINGS = "savings"  # Ahorro en vuelos
    TIME = "time"  # Tiempo ahorrado
    PRODUCTIVITY = "productivity"  # Eficiencia de búsqueda
    OPPORTUNITIES = "opportunities"  # Deals encontrados
    ENGAGEMENT = "engagement"  # Uso del servicio


@dataclass
class SavingsRecord:
    """Registro de ahorro"""
    record_id: str
    user_id: int
    
    # Deal info
    route: str
    actual_price: float
    market_price: float  # Precio promedio del mercado
    savings_amount: float
    savings_pct: float
    
    # Timestamps
    found_at: str
    claimed: bool = False
    claimed_at: Optional[str] = None


@dataclass
class ValueMetrics:
    """Métricas de valor del usuario"""
    user_id: int
    
    # Savings
    total_savings: float = 0.0
    potential_savings: float = 0.0  # No reclamados aún
    avg_savings_per_deal: float = 0.0
    best_deal_savings: float = 0.0
    
    # Time
    time_saved_hours: float = 0.0  # Vs búsqueda manual
    searches_performed: int = 0
    avg_search_time: float = 2.0  # minutos
    
    # Productivity
    deals_found: int = 0
    deals_claimed: int = 0
    success_rate: float = 0.0  # % de deals que se convierten
    
    # ROI
    subscription_cost: float = 0.0
    roi_multiplier: float = 0.0  # savings / cost
    break_even_days: int = 0
    
    # Engagement
    days_active: int = 0
    total_sessions: int = 0
    avg_session_length: float = 0.0
    
    # Comparisons
    vs_free_users_pct: float = 0.0  # Cuánto mejor que usuarios free
    vs_market_avg_pct: float = 0.0  # Cuánto mejor que mercado
    
    # Timestamps
    first_activity: Optional[str] = None
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ValueInsight:
    """Insight de valor personalizado"""
    insight_type: str  # achievement, comparison, recommendation
    category: str
    title: str
    description: str
    value: float
    emoji: str
    priority: int  # 1-5, mayor = más importante


class ValueMetricsManager:
    """
    Gestor de métricas de valor.
    
    Responsabilidades:
    - Tracking de ahorros
    - Cálculo de ROI
    - Comparaciones vs mercado
    - Generación de insights
    - Dashboard personalizado
    """
    
    # Benchmarks del mercado
    MARKET_BENCHMARKS = {
        "avg_manual_search_time": 45,  # minutos
        "avg_deals_per_month_free": 2.5,
        "avg_deals_per_month_paid": 15.3,
        "avg_savings_per_deal": 127.0,  # euros
        "avg_search_efficiency": 0.12,  # deals encontrados / búsquedas
    }
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.metrics_file = self.data_dir / "value_metrics.json"
        self.savings_file = self.data_dir / "savings_records.json"
        self.insights_file = self.data_dir / "value_insights.json"
        
        self.metrics: Dict[int, ValueMetrics] = {}
        self.savings_records: List[SavingsRecord] = []
        self.cached_insights: Dict[int, List[ValueInsight]] = {}
        
        self._load_data()
        logger.info("📊 ValueMetricsManager initialized")
    
    def _load_data(self):
        """Carga datos"""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.metrics = {
                    int(k): ValueMetrics(**v) for k, v in data.items()
                }
        
        if self.savings_file.exists():
            with open(self.savings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.savings_records = [SavingsRecord(**r) for r in data]
        
        if self.insights_file.exists():
            with open(self.insights_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cached_insights = {
                    int(k): [ValueInsight(**i) for i in v]
                    for k, v in data.items()
                }
    
    def _save_data(self):
        """Guarda datos"""
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            data = {str(k): asdict(v) for k, v in self.metrics.items()}
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(self.savings_file, 'w', encoding='utf-8') as f:
            data = [asdict(r) for r in self.savings_records]
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(self.insights_file, 'w', encoding='utf-8') as f:
            data = {
                str(k): [asdict(i) for i in v]
                for k, v in self.cached_insights.items()
            }
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def initialize_user(self, user_id: int) -> ValueMetrics:
        """Inicializa métricas para un usuario nuevo"""
        if user_id in self.metrics:
            return self.metrics[user_id]
        
        metrics = ValueMetrics(
            user_id=user_id,
            first_activity=datetime.now().isoformat()
        )
        
        self.metrics[user_id] = metrics
        self._save_data()
        
        return metrics
    
    def record_savings(
        self,
        user_id: int,
        route: str,
        actual_price: float,
        market_price: float
    ) -> SavingsRecord:
        """
        Registra un ahorro encontrado.
        """
        import hashlib
        
        if user_id not in self.metrics:
            self.initialize_user(user_id)
        
        # Calcular ahorro
        savings_amount = market_price - actual_price
        savings_pct = (savings_amount / market_price) * 100 if market_price > 0 else 0
        
        # Crear registro
        record_id = hashlib.md5(
            f"{user_id}{route}{actual_price}{datetime.now()}".encode()
        ).hexdigest()[:12]
        
        record = SavingsRecord(
            record_id=record_id,
            user_id=user_id,
            route=route,
            actual_price=actual_price,
            market_price=market_price,
            savings_amount=savings_amount,
            savings_pct=savings_pct,
            found_at=datetime.now().isoformat()
        )
        
        self.savings_records.append(record)
        
        # Actualizar métricas
        metrics = self.metrics[user_id]
        metrics.potential_savings += savings_amount
        metrics.deals_found += 1
        
        # Actualizar best deal
        if savings_amount > metrics.best_deal_savings:
            metrics.best_deal_savings = savings_amount
        
        self._recalculate_metrics(user_id)
        self._save_data()
        
        logger.info(
            f"💰 Savings recorded for user {user_id}: "
            f"€{savings_amount:.2f} ({savings_pct:.1f}%)"
        )
        
        return record
    
    def claim_savings(self, record_id: str) -> Tuple[bool, str]:
        """
        Marca un ahorro como reclamado (usuario compró el vuelo).
        """
        record = next(
            (r for r in self.savings_records if r.record_id == record_id),
            None
        )
        
        if not record:
            return False, "Registro no encontrado"
        
        if record.claimed:
            return False, "Ya fue reclamado"
        
        # Marcar como claimed
        record.claimed = True
        record.claimed_at = datetime.now().isoformat()
        
        # Actualizar métricas
        metrics = self.metrics[record.user_id]
        metrics.total_savings += record.savings_amount
        metrics.potential_savings -= record.savings_amount
        metrics.deals_claimed += 1
        
        self._recalculate_metrics(record.user_id)
        self._save_data()
        
        msg = f"✅ ¡Ahorro confirmado! Has ahorrado €{record.savings_amount:.2f}"
        return True, msg
    
    def track_search(
        self,
        user_id: int,
        search_time_seconds: Optional[float] = None
    ):
        """Registra una búsqueda realizada"""
        if user_id not in self.metrics:
            self.initialize_user(user_id)
        
        metrics = self.metrics[user_id]
        metrics.searches_performed += 1
        
        # Estimar tiempo ahorrado vs búsqueda manual
        manual_time = self.MARKET_BENCHMARKS["avg_manual_search_time"]
        actual_time = search_time_seconds / 60 if search_time_seconds else 2.0
        time_saved = (manual_time - actual_time) / 60  # en horas
        
        metrics.time_saved_hours += max(0, time_saved)
        
        self._save_data()
    
    def track_session(
        self,
        user_id: int,
        duration_seconds: float
    ):
        """Registra una sesión de uso"""
        if user_id not in self.metrics:
            self.initialize_user(user_id)
        
        metrics = self.metrics[user_id]
        metrics.total_sessions += 1
        
        # Actualizar promedio de duración
        total_time = metrics.avg_session_length * (metrics.total_sessions - 1)
        total_time += duration_seconds
        metrics.avg_session_length = total_time / metrics.total_sessions
        
        self._save_data()
    
    def set_subscription_cost(
        self,
        user_id: int,
        monthly_cost: float
    ):
        """Establece el costo de suscripción para cálculo de ROI"""
        if user_id not in self.metrics:
            self.initialize_user(user_id)
        
        metrics = self.metrics[user_id]
        metrics.subscription_cost = monthly_cost
        
        self._recalculate_metrics(user_id)
        self._save_data()
    
    def _recalculate_metrics(self, user_id: int):
        """Recalcula métricas derivadas"""
        metrics = self.metrics[user_id]
        
        # Avg savings per deal
        if metrics.deals_claimed > 0:
            metrics.avg_savings_per_deal = (
                metrics.total_savings / metrics.deals_claimed
            )
        
        # Success rate
        if metrics.deals_found > 0:
            metrics.success_rate = (
                metrics.deals_claimed / metrics.deals_found * 100
            )
        
        # ROI multiplier
        if metrics.subscription_cost > 0:
            metrics.roi_multiplier = (
                metrics.total_savings / metrics.subscription_cost
            )
            
            # Break-even days
            if metrics.total_savings > 0:
                days_since_start = self._days_since_first_activity(user_id)
                if days_since_start > 0:
                    daily_savings = metrics.total_savings / days_since_start
                    if daily_savings > 0:
                        metrics.break_even_days = int(
                            metrics.subscription_cost / daily_savings
                        )
        
        # Days active
        metrics.days_active = self._days_since_first_activity(user_id)
        
        # Comparaciones
        metrics.vs_free_users_pct = self._calculate_vs_free_users(metrics)
        metrics.vs_market_avg_pct = self._calculate_vs_market(metrics)
        
        metrics.last_updated = datetime.now().isoformat()
    
    def _days_since_first_activity(self, user_id: int) -> int:
        """Calcula días desde primera actividad"""
        metrics = self.metrics[user_id]
        if not metrics.first_activity:
            return 0
        
        first = datetime.fromisoformat(metrics.first_activity)
        return (datetime.now() - first).days
    
    def _calculate_vs_free_users(self, metrics: ValueMetrics) -> float:
        """
        Calcula cuánto mejor es que usuarios free.
        
        Retorna porcentaje de mejora.
        """
        if metrics.days_active == 0:
            return 0.0
        
        # Deals per month
        months = max(1, metrics.days_active / 30)
        user_deals_per_month = metrics.deals_found / months
        
        free_avg = self.MARKET_BENCHMARKS["avg_deals_per_month_free"]
        
        if free_avg > 0:
            improvement = ((user_deals_per_month - free_avg) / free_avg) * 100
            return max(0, improvement)
        
        return 0.0
    
    def _calculate_vs_market(self, metrics: ValueMetrics) -> float:
        """
        Calcula cuánto mejor es que el promedio del mercado.
        """
        if metrics.deals_claimed == 0:
            return 0.0
        
        user_avg = metrics.avg_savings_per_deal
        market_avg = self.MARKET_BENCHMARKS["avg_savings_per_deal"]
        
        if market_avg > 0:
            improvement = ((user_avg - market_avg) / market_avg) * 100
            return improvement  # Puede ser negativo
        
        return 0.0
    
    def generate_insights(self, user_id: int) -> List[ValueInsight]:
        """
        Genera insights personalizados de valor.
        """
        if user_id not in self.metrics:
            return []
        
        metrics = self.metrics[user_id]
        insights = []
        
        # Insight 1: Total savings
        if metrics.total_savings > 0:
            insights.append(ValueInsight(
                insight_type="achievement",
                category=MetricCategory.SAVINGS.value,
                title="Ahorro Total",
                description=f"Has ahorrado €{metrics.total_savings:.2f} en total",
                value=metrics.total_savings,
                emoji="💰",
                priority=5
            ))
        
        # Insight 2: ROI
        if metrics.roi_multiplier > 0:
            insights.append(ValueInsight(
                insight_type="comparison",
                category=MetricCategory.SAVINGS.value,
                title="Retorno de Inversión",
                description=f"Por cada €1 invertido, ahorras €{metrics.roi_multiplier:.1f}",
                value=metrics.roi_multiplier,
                emoji="📈",
                priority=5 if metrics.roi_multiplier > 1 else 3
            ))
        
        # Insight 3: Time saved
        if metrics.time_saved_hours > 1:
            insights.append(ValueInsight(
                insight_type="achievement",
                category=MetricCategory.TIME.value,
                title="Tiempo Ahorrado",
                description=f"Has ahorrado {metrics.time_saved_hours:.1f} horas vs búsqueda manual",
                value=metrics.time_saved_hours,
                emoji="⏱️",
                priority=4
            ))
        
        # Insight 4: Best deal
        if metrics.best_deal_savings > 0:
            insights.append(ValueInsight(
                insight_type="achievement",
                category=MetricCategory.SAVINGS.value,
                title="Mejor Chollo",
                description=f"Tu mejor ahorro: €{metrics.best_deal_savings:.2f}",
                value=metrics.best_deal_savings,
                emoji="🏆",
                priority=3
            ))
        
        # Insight 5: vs Free users
        if metrics.vs_free_users_pct > 0:
            insights.append(ValueInsight(
                insight_type="comparison",
                category=MetricCategory.OPPORTUNITIES.value,
                title="vs Usuarios Free",
                description=f"Encuentras {metrics.vs_free_users_pct:.0f}% más deals que usuarios free",
                value=metrics.vs_free_users_pct,
                emoji="🚀",
                priority=4
            ))
        
        # Insight 6: Potential savings
        if metrics.potential_savings > 0:
            insights.append(ValueInsight(
                insight_type="recommendation",
                category=MetricCategory.OPPORTUNITIES.value,
                title="Ahorro Potencial",
                description=f"¡Tienes €{metrics.potential_savings:.2f} en chollos sin reclamar!",
                value=metrics.potential_savings,
                emoji="🎁",
                priority=5
            ))
        
        # Insight 7: Success rate
        if metrics.success_rate > 0:
            insights.append(ValueInsight(
                insight_type="achievement",
                category=MetricCategory.PRODUCTIVITY.value,
                title="Tasa de Éxito",
                description=f"Aprovechas el {metrics.success_rate:.0f}% de los chollos que encuentras",
                value=metrics.success_rate,
                emoji="🎯",
                priority=2
            ))
        
        # Insight 8: Break-even
        if metrics.break_even_days > 0 and metrics.days_active >= metrics.break_even_days:
            insights.append(ValueInsight(
                insight_type="achievement",
                category=MetricCategory.SAVINGS.value,
                title="¡Recuperaste la Inversión!",
                description=f"Alcanzaste break-even en {metrics.break_even_days} días",
                value=metrics.break_even_days,
                emoji="✨",
                priority=5
            ))
        
        # Ordenar por prioridad
        insights.sort(key=lambda x: x.priority, reverse=True)
        
        # Cachear
        self.cached_insights[user_id] = insights
        self._save_data()
        
        return insights
    
    def format_dashboard(self, user_id: int) -> str:
        """
        Genera texto del dashboard completo.
        """
        if user_id not in self.metrics:
            return "⚠️ No hay datos disponibles"
        
        metrics = self.metrics[user_id]
        insights = self.generate_insights(user_id)
        
        # Header
        text = "📊 **Tu Dashboard de Valor**\n\n"
        
        # Key metrics
        text += "**💰 Ahorro**\n"
        text += f"• Total: €{metrics.total_savings:.2f}\n"
        text += f"• Promedio/deal: €{metrics.avg_savings_per_deal:.2f}\n"
        text += f"• Mejor chollo: €{metrics.best_deal_savings:.2f}\n\n"
        
        # ROI
        if metrics.subscription_cost > 0:
            text += "**📈 ROI**\n"
            text += f"• Multiplier: {metrics.roi_multiplier:.1f}x\n"
            text += f"• Break-even: {metrics.break_even_days} días\n"
            profit = metrics.total_savings - metrics.subscription_cost
            text += f"• Beneficio neto: €{profit:.2f}\n\n"
        
        # Activity
        text += "**📅 Actividad**\n"
        text += f"• Días activo: {metrics.days_active}\n"
        text += f"• Búsquedas: {metrics.searches_performed}\n"
        text += f"• Deals encontrados: {metrics.deals_found}\n"
        text += f"• Deals aprovechados: {metrics.deals_claimed}\n\n"
        
        # Top insights (primeros 3)
        if insights:
            text += "**✨ Insights Destacados**\n"
            for insight in insights[:3]:
                text += f"{insight.emoji} {insight.title}: {insight.description}\n"
            text += "\n"
        
        # Comparisons
        if metrics.vs_free_users_pct > 0 or metrics.vs_market_avg_pct != 0:
            text += "**🏆 Comparativas**\n"
            if metrics.vs_free_users_pct > 0:
                text += f"• vs Free: +{metrics.vs_free_users_pct:.0f}%\n"
            if metrics.vs_market_avg_pct != 0:
                sign = "+" if metrics.vs_market_avg_pct > 0 else ""
                text += f"• vs Mercado: {sign}{metrics.vs_market_avg_pct:.0f}%\n"
        
        return text
    
    def get_metrics(self, user_id: int) -> Optional[ValueMetrics]:
        """Obtiene métricas de un usuario"""
        return self.metrics.get(user_id)
    
    def get_user_savings_records(
        self,
        user_id: int,
        limit: Optional[int] = None
    ) -> List[SavingsRecord]:
        """Obtiene registros de ahorro de un usuario"""
        records = [
            r for r in self.savings_records
            if r.user_id == user_id
        ]
        
        # Ordenar por fecha descendente
        records.sort(key=lambda x: x.found_at, reverse=True)
        
        if limit:
            return records[:limit]
        
        return records


if __name__ == "__main__":
    # Testing
    print("🚀 Testing ValueMetricsManager...\n")
    
    manager = ValueMetricsManager()
    
    # Test 1: Initialize user
    print("1. Initializing user...")
    metrics = manager.initialize_user(12345)
    print(f"   User {metrics.user_id} initialized\n")
    
    # Test 2: Record savings
    print("2. Recording savings...")
    record = manager.record_savings(
        12345,
        "MAD-BCN",
        actual_price=89.99,
        market_price=150.00
    )
    print(f"   Saved: €{record.savings_amount:.2f}\n")
    
    # Test 3: Claim savings
    print("3. Claiming savings...")
    success, msg = manager.claim_savings(record.record_id)
    print(f"   {msg}\n")
    
    # Test 4: Track activity
    print("4. Tracking activity...")
    manager.track_search(12345, search_time_seconds=30)
    manager.track_session(12345, duration_seconds=300)
    manager.set_subscription_cost(12345, 9.99)
    print("   Activity tracked\n")
    
    # Test 5: Generate insights
    print("5. Generating insights...")
    insights = manager.generate_insights(12345)
    print(f"   Generated {len(insights)} insights\n")
    
    # Test 6: Format dashboard
    print("6. Formatting dashboard...")
    dashboard = manager.format_dashboard(12345)
    print(dashboard)
    
    print("\n✅ Tests completados!")
