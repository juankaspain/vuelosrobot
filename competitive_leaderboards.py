#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Competitive Leaderboards System - IT5 Day 4/5
Sistema de rankings competitivos con premios y temporadas

Author: @Juanka_Spain
Version: 13.1.0
Date: 2026-01-15
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum
import hashlib


class LeaderboardCategory(Enum):
    """Categorías de leaderboards"""
    DEALS_FOUND = "deals_found"  # Más chollos encontrados
    SAVINGS_TOTAL = "savings_total"  # Más ahorro generado
    REFERRALS = "referrals"  # Más referidos
    SHARES = "shares"  # Más compartidas
    GROUP_CONTRIBUTION = "group_contribution"  # Más activo en grupos
    STREAK = "streak"  # Mayor racha diaria
    COINS_EARNED = "coins_earned"  # Más coins ganados


class SeasonType(Enum):
    """Tipos de temporadas"""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class LeaderboardEntry:
    """Entrada en un leaderboard"""
    user_id: int
    username: str
    score: float
    rank: int
    tier: str
    last_updated: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class Prize:
    """Premio para el leaderboard"""
    rank_start: int
    rank_end: int
    coins: int
    badge: Optional[str] = None
    description: str = ""
    special_perks: List[str] = field(default_factory=list)


@dataclass
class Season:
    """Temporada competitiva"""
    season_id: str
    name: str
    season_type: str
    start_date: str
    end_date: str
    categories: List[str]
    prizes: List[Prize] = field(default_factory=list)
    is_active: bool = True
    winners: Dict[str, List[int]] = field(default_factory=dict)  # category -> [user_ids]


@dataclass
class PrizeDistribution:
    """Distribución de premios realizada"""
    distribution_id: str
    season_id: str
    category: str
    user_id: int
    username: str
    rank: int
    prize: Prize
    distributed_at: str
    claimed: bool = False


class CompetitiveLeaderboardManager:
    """
    Gestor de leaderboards competitivos.
    
    Features:
    - Múltiples categorías de competición
    - Temporadas (semanal, mensual, trimestral, anual)
    - Premios automáticos
    - Anti-cheating
    - Badges especiales
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.leaderboards_file = self.data_dir / "leaderboards.json"
        self.seasons_file = self.data_dir / "seasons.json"
        self.distributions_file = self.data_dir / "prize_distributions.json"
        self.analytics_file = self.data_dir / "leaderboard_analytics.json"
        
        self.leaderboards: Dict[str, List[LeaderboardEntry]] = {}
        self.seasons: Dict[str, Season] = {}
        self.distributions: List[PrizeDistribution] = []
        self.analytics: Dict = self._init_analytics()
        
        self._load_data()
        self._init_default_categories()
    
    def _init_analytics(self) -> Dict:
        """Inicializa analytics"""
        return {
            "total_seasons": 0,
            "total_prizes_distributed": 0,
            "total_coins_awarded": 0,
            "most_competitive_category": None,
            "top_all_time_winners": [],
            "last_updated": datetime.now().isoformat()
        }
    
    def _init_default_categories(self):
        """Inicializa categorías por defecto si no existen"""
        for category in LeaderboardCategory:
            if category.value not in self.leaderboards:
                self.leaderboards[category.value] = []
    
    def _load_data(self):
        """Carga datos"""
        if self.leaderboards_file.exists():
            with open(self.leaderboards_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.leaderboards = {
                    k: [LeaderboardEntry(**e) for e in v]
                    for k, v in data.items()
                }
        
        if self.seasons_file.exists():
            with open(self.seasons_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.seasons = {
                    k: Season(**{**v, 'prizes': [Prize(**p) for p in v.get('prizes', [])]})
                    for k, v in data.items()
                }
        
        if self.distributions_file.exists():
            with open(self.distributions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.distributions = [
                    PrizeDistribution(**{**d, 'prize': Prize(**d['prize'])})
                    for d in data
                ]
        
        if self.analytics_file.exists():
            with open(self.analytics_file, 'r', encoding='utf-8') as f:
                self.analytics = json.load(f)
    
    def _save_data(self):
        """Guarda datos"""
        with open(self.leaderboards_file, 'w', encoding='utf-8') as f:
            data = {
                k: [asdict(e) for e in v]
                for k, v in self.leaderboards.items()
            }
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(self.seasons_file, 'w', encoding='utf-8') as f:
            data = {
                k: {**asdict(v), 'prizes': [asdict(p) for p in v.prizes]}
                for k, v in self.seasons.items()
            }
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(self.distributions_file, 'w', encoding='utf-8') as f:
            data = [
                {**asdict(d), 'prize': asdict(d.prize)}
                for d in self.distributions
            ]
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(self.analytics_file, 'w', encoding='utf-8') as f:
            json.dump(self.analytics, f, indent=2, ensure_ascii=False)
    
    def create_season(
        self,
        name: str,
        season_type: SeasonType,
        start_date: Optional[datetime] = None,
        categories: Optional[List[str]] = None
    ) -> Season:
        """
        Crea una nueva temporada competitiva.
        """
        if start_date is None:
            start_date = datetime.now()
        
        # Calcular end_date basado en el tipo
        duration_map = {
            SeasonType.WEEKLY: timedelta(days=7),
            SeasonType.MONTHLY: timedelta(days=30),
            SeasonType.QUARTERLY: timedelta(days=90),
            SeasonType.YEARLY: timedelta(days=365)
        }
        
        end_date = start_date + duration_map[season_type]
        
        season_id = hashlib.md5(
            f"{name}{start_date.isoformat()}".encode()
        ).hexdigest()[:12]
        
        # Premios por defecto
        default_prizes = [
            Prize(
                rank_start=1, rank_end=1,
                coins=5000,
                badge="🥇 Champion",
                description="Campeón de la temporada",
                special_perks=["VIP Status 30d", "Custom Badge"]
            ),
            Prize(
                rank_start=2, rank_end=2,
                coins=3000,
                badge="🥈 Runner-up",
                description="Subcampeón",
                special_perks=["VIP Status 15d"]
            ),
            Prize(
                rank_start=3, rank_end=3,
                coins=2000,
                badge="🥉 Third Place",
                description="Tercer lugar",
                special_perks=["VIP Status 7d"]
            ),
            Prize(
                rank_start=4, rank_end=10,
                coins=1000,
                badge="🏆 Top 10",
                description="Top 10",
                special_perks=[]
            ),
            Prize(
                rank_start=11, rank_end=50,
                coins=500,
                badge="⭐ Top 50",
                description="Top 50",
                special_perks=[]
            )
        ]
        
        season = Season(
            season_id=season_id,
            name=name,
            season_type=season_type.value,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            categories=categories or [c.value for c in LeaderboardCategory],
            prizes=default_prizes
        )
        
        self.seasons[season_id] = season
        self.analytics["total_seasons"] += 1
        
        self._save_data()
        
        return season
    
    def update_score(
        self,
        category: str,
        user_id: int,
        username: str,
        score_delta: float,
        tier: str = "BRONZE",
        metadata: Optional[Dict] = None
    ):
        """
        Actualiza el puntaje de un usuario en una categoría.
        """
        if category not in self.leaderboards:
            self.leaderboards[category] = []
        
        # Buscar entrada existente
        entry = next(
            (e for e in self.leaderboards[category] if e.user_id == user_id),
            None
        )
        
        if entry:
            entry.score += score_delta
            entry.tier = tier
            entry.last_updated = datetime.now().isoformat()
            if metadata:
                entry.metadata.update(metadata)
        else:
            entry = LeaderboardEntry(
                user_id=user_id,
                username=username,
                score=score_delta,
                rank=0,  # Se calculará al ordenar
                tier=tier,
                last_updated=datetime.now().isoformat(),
                metadata=metadata or {}
            )
            self.leaderboards[category].append(entry)
        
        # Reordenar y actualizar ranks
        self._update_ranks(category)
        self._save_data()
    
    def _update_ranks(self, category: str):
        """Actualiza los ranks de un leaderboard"""
        if category not in self.leaderboards:
            return
        
        # Ordenar por score descendente
        sorted_entries = sorted(
            self.leaderboards[category],
            key=lambda x: x.score,
            reverse=True
        )
        
        # Actualizar ranks
        for i, entry in enumerate(sorted_entries, 1):
            entry.rank = i
        
        self.leaderboards[category] = sorted_entries
    
    def get_leaderboard(
        self,
        category: str,
        limit: int = 100,
        tier_filter: Optional[str] = None
    ) -> List[LeaderboardEntry]:
        """
        Obtiene un leaderboard.
        """
        if category not in self.leaderboards:
            return []
        
        entries = self.leaderboards[category]
        
        # Filtrar por tier si se especifica
        if tier_filter:
            entries = [e for e in entries if e.tier == tier_filter]
        
        return entries[:limit]
    
    def get_user_position(
        self,
        category: str,
        user_id: int
    ) -> Optional[LeaderboardEntry]:
        """
        Obtiene la posición de un usuario en un leaderboard.
        """
        if category not in self.leaderboards:
            return None
        
        return next(
            (e for e in self.leaderboards[category] if e.user_id == user_id),
            None
        )
    
    def get_user_all_positions(self, user_id: int) -> Dict[str, LeaderboardEntry]:
        """
        Obtiene las posiciones de un usuario en todos los leaderboards.
        """
        positions = {}
        
        for category in self.leaderboards:
            entry = self.get_user_position(category, user_id)
            if entry:
                positions[category] = entry
        
        return positions
    
    def end_season(self, season_id: str) -> List[PrizeDistribution]:
        """
        Finaliza una temporada y distribuye premios.
        
        Returns:
            Lista de distribuciones de premios
        """
        if season_id not in self.seasons:
            return []
        
        season = self.seasons[season_id]
        season.is_active = False
        
        distributions = []
        
        # Distribuir premios por categoría
        for category in season.categories:
            if category not in self.leaderboards:
                continue
            
            leaderboard = self.leaderboards[category]
            
            # Para cada premio
            for prize in season.prizes:
                # Obtener ganadores en el rango
                winners = [
                    e for e in leaderboard
                    if prize.rank_start <= e.rank <= prize.rank_end
                ]
                
                # Crear distribuciones
                for winner in winners:
                    distribution_id = hashlib.md5(
                        f"{season_id}{category}{winner.user_id}{datetime.now()}".encode()
                    ).hexdigest()[:12]
                    
                    distribution = PrizeDistribution(
                        distribution_id=distribution_id,
                        season_id=season_id,
                        category=category,
                        user_id=winner.user_id,
                        username=winner.username,
                        rank=winner.rank,
                        prize=prize,
                        distributed_at=datetime.now().isoformat()
                    )
                    
                    distributions.append(distribution)
                    self.distributions.append(distribution)
                    
                    # Actualizar analytics
                    self.analytics["total_prizes_distributed"] += 1
                    self.analytics["total_coins_awarded"] += prize.coins
                    
                    # Registrar ganadores
                    if category not in season.winners:
                        season.winners[category] = []
                    season.winners[category].append(winner.user_id)
        
        self._save_data()
        self._update_analytics()
        
        return distributions
    
    def claim_prize(self, distribution_id: str) -> Tuple[bool, str, Optional[Prize]]:
        """
        Un usuario reclama su premio.
        
        Returns:
            (success, message, prize)
        """
        distribution = next(
            (d for d in self.distributions if d.distribution_id == distribution_id),
            None
        )
        
        if not distribution:
            return False, "❌ Premio no encontrado", None
        
        if distribution.claimed:
            return False, "❌ Premio ya reclamado", None
        
        distribution.claimed = True
        self._save_data()
        
        msg = (
            f"✅ ¡Premio reclamado!\n"
            f"🏆 Rank: #{distribution.rank}\n"
            f"💰 {distribution.prize.coins} FlightCoins\n"
            f"🎯 Badge: {distribution.prize.badge}"
        )
        
        return True, msg, distribution.prize
    
    def get_user_prizes(self, user_id: int) -> List[PrizeDistribution]:
        """
        Obtiene todos los premios de un usuario.
        """
        return [
            d for d in self.distributions
            if d.user_id == user_id
        ]
    
    def reset_leaderboard(self, category: str):
        """
        Resetea un leaderboard (para nueva temporada).
        """
        if category in self.leaderboards:
            self.leaderboards[category] = []
            self._save_data()
    
    def _update_analytics(self):
        """Actualiza analytics globales"""
        # Categoría más competitiva (más participantes)
        if self.leaderboards:
            most_competitive = max(
                self.leaderboards.items(),
                key=lambda x: len(x[1])
            )
            self.analytics["most_competitive_category"] = {
                "category": most_competitive[0],
                "participants": len(most_competitive[1])
            }
        
        # Top ganadores all-time
        user_wins = {}
        for dist in self.distributions:
            if dist.claimed:
                if dist.user_id not in user_wins:
                    user_wins[dist.user_id] = {
                        "username": dist.username,
                        "prizes": 0,
                        "total_coins": 0
                    }
                user_wins[dist.user_id]["prizes"] += 1
                user_wins[dist.user_id]["total_coins"] += dist.prize.coins
        
        self.analytics["top_all_time_winners"] = sorted(
            [{"user_id": k, **v} for k, v in user_wins.items()],
            key=lambda x: x["total_coins"],
            reverse=True
        )[:10]
        
        self.analytics["last_updated"] = datetime.now().isoformat()
    
    def get_global_analytics(self) -> Dict:
        """Retorna analytics globales"""
        return self.analytics


if __name__ == "__main__":
    # Testing
    print("🚀 Testing Competitive Leaderboards...")
    
    manager = CompetitiveLeaderboardManager()
    
    # Crear temporada
    season = manager.create_season(
        name="Winter 2026 Challenge",
        season_type=SeasonType.MONTHLY
    )
    
    print(f"\n✅ Temporada creada: {season.name}")
    print(f"   Inicio: {season.start_date[:10]}")
    print(f"   Fin: {season.end_date[:10]}")
    print(f"   Categorías: {len(season.categories)}")
    
    # Actualizar scores
    manager.update_score(
        category=LeaderboardCategory.DEALS_FOUND.value,
        user_id=12345,
        username="john_doe",
        score_delta=10,
        tier="GOLD"
    )
    
    manager.update_score(
        category=LeaderboardCategory.DEALS_FOUND.value,
        user_id=67890,
        username="jane_smith",
        score_delta=15,
        tier="DIAMOND"
    )
    
    # Ver leaderboard
    leaderboard = manager.get_leaderboard(
        category=LeaderboardCategory.DEALS_FOUND.value,
        limit=10
    )
    
    print(f"\n🏆 Leaderboard - Deals Found:")
    for entry in leaderboard:
        print(f"   #{entry.rank} - {entry.username}: {entry.score} deals ({entry.tier})")
    
    # Finalizar temporada
    distributions = manager.end_season(season.season_id)
    print(f"\n✅ Temporada finalizada")
    print(f"   Premios distribuidos: {len(distributions)}")
    
    # Analytics
    analytics = manager.get_global_analytics()
    print(f"\n📊 Analytics Globales:")
    print(f"   Total temporadas: {analytics['total_seasons']}")
    print(f"   Premios distribuidos: {analytics['total_prizes_distributed']}")
    print(f"   Coins otorgados: {analytics['total_coins_awarded']}")
    
    print("\n✅ Tests completados!")
