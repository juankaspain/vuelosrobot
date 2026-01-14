#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  🏆 COMPETITIVE LEADERBOARDS + VIRAL ANALYTICS           │
│  🚀 Cazador Supremo v13.1 Enterprise                          │
│  🎯 Complete Viral Growth System                           │
└────────────────────────────────────────────────────────────────┘

Leaderboards competitivos y analytics virales avanzados.

Autor: @Juanka_Spain
Version: 13.1.0
Date: 2026-01-14
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class LeaderboardType(Enum):
    REFERRALS = "referrals"
    DEALS = "deals"
    SAVINGS = "savings"
    COINS = "coins"


class TimeFrame(Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"


# Premios por posición
WEEKLY_PRIZES = {
    1: 5000, 2: 3000, 3: 2000, 4: 1000, 5: 750,
    6: 600, 7: 550, 8: 525, 9: 510, 10: 500
}

MONTHLY_PRIZES = {
    1: 20000, 2: 10000, 3: 5000
}


@dataclass
class LeaderboardEntry:
    user_id: int
    username: str
    score: float
    rank: int
    badge: Optional[str] = None
    country: Optional[str] = None


@dataclass
class ViralMetrics:
    """Métricas virales agregadas"""
    period_start: str
    period_end: str
    
    # Core metrics
    total_users: int = 0
    new_users: int = 0
    active_users: int = 0
    
    # Viral metrics
    total_invites: int = 0
    conversions: int = 0
    viral_coefficient: float = 0.0
    
    # Channels
    signups_by_channel: Dict[str, int] = None
    
    # Engagement
    share_rate: float = 0.0
    referral_rate: float = 0.0
    
    def __post_init__(self):
        if self.signups_by_channel is None:
            self.signups_by_channel = {}
    
    def calculate_k_coefficient(self, avg_invites_per_user: float):
        """Calcula coeficiente viral K."""
        if self.total_invites > 0:
            conversion_rate = self.conversions / self.total_invites
            self.viral_coefficient = avg_invites_per_user * conversion_rate
        else:
            self.viral_coefficient = 0.0


class CompetitiveLeaderboardManager:
    """
    Gestor de leaderboards y analytics virales.
    """
    
    def __init__(self,
                 leaderboards_file: str = 'leaderboards.json',
                 metrics_file: str = 'viral_metrics.json'):
        self.leaderboards_file = Path(leaderboards_file)
        self.metrics_file = Path(metrics_file)
        
        self.leaderboards: Dict[str, List[LeaderboardEntry]] = {}
        self.metrics_history: List[ViralMetrics] = []
        
        self._load_data()
        
        logger.info("🏆 CompetitiveLeaderboardManager initialized")
    
    def _load_data(self):
        """Carga datos."""
        if self.leaderboards_file.exists():
            try:
                with open(self.leaderboards_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for key, entries in data.items():
                    self.leaderboards[key] = [
                        LeaderboardEntry(**e) for e in entries
                    ]
                logger.info(f"✅ Loaded {len(self.leaderboards)} leaderboards")
            except Exception as e:
                logger.error(f"❌ Error loading leaderboards: {e}")
        
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.metrics_history = [ViralMetrics(**m) for m in data]
                logger.info(f"✅ Loaded {len(self.metrics_history)} metrics periods")
            except Exception as e:
                logger.error(f"❌ Error loading metrics: {e}")
    
    def _save_data(self):
        """Guarda datos."""
        try:
            # Leaderboards
            data = {
                key: [asdict(e) for e in entries]
                for key, entries in self.leaderboards.items()
            }
            with open(self.leaderboards_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Metrics
            metrics_data = [asdict(m) for m in self.metrics_history]
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 Leaderboard data saved")
        except Exception as e:
            logger.error(f"❌ Error saving data: {e}")
    
    def update_leaderboard(self,
                          lb_type: LeaderboardType,
                          timeframe: TimeFrame,
                          entries: List[Tuple[int, str, float]]):
        """
        Actualiza leaderboard.
        
        Args:
            lb_type: Tipo de leaderboard
            timeframe: Período
            entries: Lista de (user_id, username, score)
        """
        key = f"{lb_type.value}_{timeframe.value}"
        
        # Ordenar por score
        sorted_entries = sorted(entries, key=lambda x: x[2], reverse=True)
        
        # Crear entries con ranking
        leaderboard = []
        for rank, (user_id, username, score) in enumerate(sorted_entries[:100], 1):
            entry = LeaderboardEntry(
                user_id=user_id,
                username=username,
                score=score,
                rank=rank
            )
            leaderboard.append(entry)
        
        self.leaderboards[key] = leaderboard
        self._save_data()
        
        logger.info(f"🏆 Updated leaderboard: {key} ({len(leaderboard)} entries)")
    
    def get_leaderboard(self,
                       lb_type: LeaderboardType,
                       timeframe: TimeFrame,
                       limit: int = 10) -> List[LeaderboardEntry]:
        """Obtiene top N del leaderboard."""
        key = f"{lb_type.value}_{timeframe.value}"
        leaderboard = self.leaderboards.get(key, [])
        return leaderboard[:limit]
    
    def get_user_rank(self,
                     user_id: int,
                     lb_type: LeaderboardType,
                     timeframe: TimeFrame) -> Optional[int]:
        """Obtiene ranking del usuario."""
        key = f"{lb_type.value}_{timeframe.value}"
        leaderboard = self.leaderboards.get(key, [])
        
        for entry in leaderboard:
            if entry.user_id == user_id:
                return entry.rank
        
        return None
    
    def calculate_viral_metrics(self,
                               start_date: datetime,
                               end_date: datetime,
                               user_data: Dict) -> ViralMetrics:
        """
        Calcula métricas virales para período.
        
        Args:
            start_date: Fecha inicio
            end_date: Fecha fin
            user_data: Dict con datos de usuarios
        
        Returns:
            ViralMetrics calculadas
        """
        metrics = ViralMetrics(
            period_start=start_date.isoformat(),
            period_end=end_date.isoformat()
        )
        
        # Calcular métricas (simplificado)
        metrics.total_users = user_data.get('total_users', 0)
        metrics.new_users = user_data.get('new_users', 0)
        metrics.active_users = user_data.get('active_users', 0)
        
        metrics.total_invites = user_data.get('total_invites', 0)
        metrics.conversions = user_data.get('conversions', 0)
        
        # K coefficient
        avg_invites = user_data.get('avg_invites_per_user', 2.5)
        metrics.calculate_k_coefficient(avg_invites)
        
        # Rates
        if metrics.active_users > 0:
            total_shares = user_data.get('total_shares', 0)
            metrics.share_rate = total_shares / metrics.active_users
            
            total_referrals = user_data.get('total_referrals', 0)
            metrics.referral_rate = total_referrals / metrics.active_users
        
        self.metrics_history.append(metrics)
        self._save_data()
        
        logger.info(
            f"📊 Viral metrics calculated: K={metrics.viral_coefficient:.2f}, "
            f"Share rate={metrics.share_rate:.1%}"
        )
        
        return metrics
    
    def get_latest_metrics(self) -> Optional[ViralMetrics]:
        """Obtiene últimas métricas."""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_growth_trend(self, periods: int = 4) -> List[float]:
        """Obtiene tendencia de crecimiento (K coefficient)."""
        if len(self.metrics_history) < periods:
            periods = len(self.metrics_history)
        
        recent = self.metrics_history[-periods:]
        return [m.viral_coefficient for m in recent]
    
    def generate_leaderboard_message(self,
                                    lb_type: LeaderboardType,
                                    timeframe: TimeFrame,
                                    user_id: Optional[int] = None) -> str:
        """
        Genera mensaje formateado de leaderboard.
        
        Args:
            lb_type: Tipo de leaderboard
            timeframe: Período
            user_id: ID usuario (para destacar su posición)
        
        Returns:
            Mensaje Markdown formateado
        """
        top10 = self.get_leaderboard(lb_type, timeframe, 10)
        
        if not top10:
            return "⚠️ No hay datos de leaderboard aún"
        
        # Header
        timeframe_str = {
            TimeFrame.WEEKLY: "SEMANAL",
            TimeFrame.MONTHLY: "MENSUAL",
            TimeFrame.ALL_TIME: "TODO EL TIEMPO"
        }[timeframe]
        
        type_str = {
            LeaderboardType.REFERRALS: "👥 REFERIDOS",
            LeaderboardType.DEALS: "💰 DEALS",
            LeaderboardType.SAVINGS: "💸 AHORROS",
            LeaderboardType.COINS: "🪙 COINS"
        }[lb_type]
        
        msg = f"🏆 *LEADERBOARD {type_str}*\n"
        msg += f"📅 {timeframe_str}\n"
        msg += "="*30 + "\n\n"
        
        # Top 10
        medals = ["🥇", "🥈", "🥉"]
        for entry in top10:
            medal = medals[entry.rank-1] if entry.rank <= 3 else f"{entry.rank}."
            
            highlight = "" if entry.user_id != user_id else " ⭐"
            
            msg += f"{medal} @{entry.username}: {entry.score:.0f}{highlight}\n"
        
        # User position si no está en top 10
        if user_id:
            user_rank = self.get_user_rank(user_id, lb_type, timeframe)
            if user_rank and user_rank > 10:
                msg += f"\n..\n"
                msg += f"{user_rank}. Tú ⭐\n"
        
        # Premios
        if timeframe == TimeFrame.WEEKLY:
            msg += f"\n🎁 *Premios Top 10:* 5K-500 coins\n"
        elif timeframe == TimeFrame.MONTHLY:
            msg += f"\n🎁 *Premios Top 3:* 20K-5K coins\n"
        
        return msg


if __name__ == '__main__':
    # 🧪 Tests
    print("🧪 Testing CompetitiveLeaderboardManager...\n")
    
    mgr = CompetitiveLeaderboardManager(
        'test_leaderboards.json',
        'test_metrics.json'
    )
    
    # Test 1: Update leaderboard
    print("1. Updating leaderboard...")
    entries = [
        (12345, "alice", 150),
        (67890, "bob", 120),
        (11111, "charlie", 100)
    ]
    mgr.update_leaderboard(LeaderboardType.REFERRALS, TimeFrame.WEEKLY, entries)
    print("   ✅ Leaderboard updated\n")
    
    # Test 2: Get top 3
    print("2. Getting top 3...")
    top3 = mgr.get_leaderboard(LeaderboardType.REFERRALS, TimeFrame.WEEKLY, 3)
    for entry in top3:
        print(f"   {entry.rank}. @{entry.username}: {entry.score}")
    print()
    
    # Test 3: Generate message
    print("3. Generating leaderboard message...")
    msg = mgr.generate_leaderboard_message(
        LeaderboardType.REFERRALS,
        TimeFrame.WEEKLY,
        user_id=12345
    )
    print(msg)
    print()
    
    # Test 4: Viral metrics
    print("4. Calculating viral metrics...")
    user_data = {
        'total_users': 1000,
        'new_users': 125,
        'active_users': 700,
        'total_invites': 250,
        'conversions': 112,
        'avg_invites_per_user': 2.5
    }
    metrics = mgr.calculate_viral_metrics(
        datetime.now() - timedelta(days=7),
        datetime.now(),
        user_data
    )
    print(f"   K coefficient: {metrics.viral_coefficient:.2f}")
    print(f"   Conversions: {metrics.conversions}")
    print()
    
    print("✅ All tests completed!")
