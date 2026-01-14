#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  🎮 RETENTION SYSTEM - Hook Model Implementation              │
│  🚀 Cazador Supremo v13.0 Enterprise                          │
│  📊 Target: Day 7 Retention 35% → 60%                         │
└────────────────────────────────────────────────────────────────┘

Sistema completo de retención basado en Hook Model:
- TRIGGER: Daily notifications, price alerts
- ACTION: Simple commands (/daily, /watchlist)
- REWARD: Variable rewards (coins, deals)
- INVESTMENT: Streak building, profile growth

Autor: @Juanka_Spain
Version: 13.0.0
Date: 2026-01-14
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import random

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════

class UserTier(Enum):
    """Niveles de usuario basados en FlightCoins"""
    BRONZE = "bronze"      # 0-500 coins
    SILVER = "silver"      # 500-2000 coins
    GOLD = "gold"          # 2000-5000 coins
    DIAMOND = "diamond"    # 5000+ coins


class AchievementType(Enum):
    """Tipos de logros desbloqueables"""
    EARLY_BIRD = "early_bird"          # Primera búsqueda antes 7am
    DEAL_HUNTER = "deal_hunter"        # 10 deals encontrados
    GLOBE_TROTTER = "globe_trotter"    # 20 rutas diferentes
    SPEED_DEMON = "speed_demon"        # 100 búsquedas en 1 mes
    MONEY_SAVER = "money_saver"        # Ahorraste €1000+ total
    WEEK_WARRIOR = "week_warrior"      # 7 días de streak
    MONTH_MASTER = "month_master"      # 30 días de streak
    REFERRAL_KING = "referral_king"    # 10 referidos
    POWER_USER = "power_user"          # 500 comandos totales


# Rewards configuration
COIN_REWARDS = {
    'daily_login': (50, 200),      # Random entre 50-200
    'first_search': 10,
    'deal_found': 100,
    'deal_used': 500,
    'referral': 500,
    'achievement': 1000,
    'share_deal': 50,
    'group_create': 100,
}

TIER_LIMITS = {
    UserTier.BRONZE: 0,
    UserTier.SILVER: 500,
    UserTier.GOLD: 2000,
    UserTier.DIAMOND: 5000,
}

TIER_BENEFITS = {
    UserTier.BRONZE: {
        'daily_searches': 3,
        'watchlist_slots': 5,
        'custom_alerts': 2,
    },
    UserTier.SILVER: {
        'daily_searches': 10,
        'watchlist_slots': 15,
        'custom_alerts': 5,
    },
    UserTier.GOLD: {
        'daily_searches': -1,  # Unlimited
        'watchlist_slots': 30,
        'custom_alerts': 15,
    },
    UserTier.DIAMOND: {
        'daily_searches': -1,
        'watchlist_slots': 50,
        'custom_alerts': -1,  # Unlimited
    },
}


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class WatchlistItem:
    """Item de watchlist personal del usuario"""
    route: str              # "MAD-MIA"
    threshold: float        # €450.0
    created_at: str         # ISO timestamp
    last_price: float = 0.0
    notifications_sent: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WatchlistItem':
        return cls(**data)


@dataclass
class Achievement:
    """Logro desbloqueable"""
    type: AchievementType
    unlocked_at: str
    coins_earned: int = 1000
    
    def to_dict(self) -> dict:
        return {
            'type': self.type.value,
            'unlocked_at': self.unlocked_at,
            'coins_earned': self.coins_earned
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Achievement':
        return cls(
            type=AchievementType(data['type']),
            unlocked_at=data['unlocked_at'],
            coins_earned=data.get('coins_earned', 1000)
        )


@dataclass
class UserProfile:
    """Perfil completo del usuario"""
    user_id: int
    username: str
    coins: int = 0
    tier: UserTier = UserTier.BRONZE
    
    # Streak tracking
    current_streak: int = 0
    longest_streak: int = 0
    last_daily_claim: Optional[str] = None
    
    # Stats
    total_searches: int = 0
    total_deals_found: int = 0
    total_savings: float = 0.0
    routes_searched: List[str] = None
    
    # Watchlist
    watchlist: List[WatchlistItem] = None
    
    # Achievements
    achievements: List[Achievement] = None
    
    # Metadata
    created_at: str = None
    last_active: str = None
    
    def __post_init__(self):
        if self.routes_searched is None:
            self.routes_searched = []
        if self.watchlist is None:
            self.watchlist = []
        if self.achievements is None:
            self.achievements = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.last_active is None:
            self.last_active = datetime.now().isoformat()
    
    def update_tier(self) -> bool:
        """Actualiza tier basado en coins. Retorna True si subió de nivel."""
        old_tier = self.tier
        
        if self.coins >= TIER_LIMITS[UserTier.DIAMOND]:
            self.tier = UserTier.DIAMOND
        elif self.coins >= TIER_LIMITS[UserTier.GOLD]:
            self.tier = UserTier.GOLD
        elif self.coins >= TIER_LIMITS[UserTier.SILVER]:
            self.tier = UserTier.SILVER
        else:
            self.tier = UserTier.BRONZE
        
        return old_tier != self.tier
    
    def add_coins(self, amount: int, reason: str = None) -> int:
        """Añade coins y actualiza tier. Retorna nuevo balance."""
        self.coins += amount
        leveled_up = self.update_tier()
        
        logger.info(f"💰 User {self.user_id} earned {amount} coins ({reason}). Balance: {self.coins}")
        
        if leveled_up:
            logger.info(f"🎉 User {self.user_id} leveled up to {self.tier.value.upper()}!")
        
        return self.coins
    
    def can_claim_daily(self) -> bool:
        """Verifica si puede reclamar reward diario."""
        if not self.last_daily_claim:
            return True
        
        last_claim = datetime.fromisoformat(self.last_daily_claim)
        now = datetime.now()
        
        # Puede reclamar si pasó 1+ día
        return (now - last_claim).days >= 1
    
    def claim_daily_reward(self) -> Tuple[int, int, bool]:
        """
        Reclama reward diario.
        
        Returns:
            Tuple[reward, streak, is_new_streak]
        """
        if not self.can_claim_daily():
            raise ValueError("Ya reclamaste el reward diario hoy")
        
        # Calcular reward base aleatorio
        min_reward, max_reward = COIN_REWARDS['daily_login']
        base_reward = random.randint(min_reward, max_reward)
        
        # Calcular streak
        now = datetime.now()
        is_new_streak = False
        
        if self.last_daily_claim:
            last_claim = datetime.fromisoformat(self.last_daily_claim)
            days_diff = (now - last_claim).days
            
            if days_diff == 1:
                # Continúa streak
                self.current_streak += 1
                if self.current_streak > self.longest_streak:
                    self.longest_streak = self.current_streak
            else:
                # Perdió streak
                self.current_streak = 1
                is_new_streak = True
        else:
            # Primera vez
            self.current_streak = 1
            is_new_streak = True
        
        # Bonus por streak
        streak_bonus = self.current_streak * 10
        total_reward = base_reward + streak_bonus
        
        # Actualizar
        self.last_daily_claim = now.isoformat()
        self.add_coins(total_reward, "daily_reward")
        
        # Check achievements
        self._check_streak_achievements()
        
        return total_reward, self.current_streak, is_new_streak
    
    def add_to_watchlist(self, route: str, threshold: float) -> bool:
        """Añade ruta a watchlist. Retorna True si exitoso."""
        # Check limit
        tier_benefits = TIER_BENEFITS[self.tier]
        max_slots = tier_benefits['watchlist_slots']
        
        if len(self.watchlist) >= max_slots:
            raise ValueError(f"Watchlist llena ({max_slots} slots para tier {self.tier.value})")
        
        # Check duplicados
        if any(item.route == route for item in self.watchlist):
            raise ValueError(f"La ruta {route} ya está en tu watchlist")
        
        # Añadir
        item = WatchlistItem(
            route=route,
            threshold=threshold,
            created_at=datetime.now().isoformat()
        )
        self.watchlist.append(item)
        
        logger.info(f"📌 User {self.user_id} added {route} to watchlist (threshold: €{threshold})")
        return True
    
    def remove_from_watchlist(self, route: str) -> bool:
        """Elimina ruta de watchlist."""
        original_len = len(self.watchlist)
        self.watchlist = [item for item in self.watchlist if item.route != route]
        
        removed = len(self.watchlist) < original_len
        if removed:
            logger.info(f"🗑️ User {self.user_id} removed {route} from watchlist")
        
        return removed
    
    def unlock_achievement(self, achievement_type: AchievementType) -> bool:
        """Desbloquea achievement. Retorna True si es nuevo."""
        # Check si ya lo tiene
        if any(a.type == achievement_type for a in self.achievements):
            return False
        
        # Desbloquear
        achievement = Achievement(
            type=achievement_type,
            unlocked_at=datetime.now().isoformat()
        )
        self.achievements.append(achievement)
        self.add_coins(achievement.coins_earned, f"achievement_{achievement_type.value}")
        
        logger.info(f"🏆 User {self.user_id} unlocked achievement: {achievement_type.value}")
        return True
    
    def _check_streak_achievements(self):
        """Verifica achievements relacionados con streak."""
        if self.current_streak >= 7:
            self.unlock_achievement(AchievementType.WEEK_WARRIOR)
        if self.current_streak >= 30:
            self.unlock_achievement(AchievementType.MONTH_MASTER)
    
    def to_dict(self) -> dict:
        """Convierte a dict para serialización."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'coins': self.coins,
            'tier': self.tier.value,
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'last_daily_claim': self.last_daily_claim,
            'total_searches': self.total_searches,
            'total_deals_found': self.total_deals_found,
            'total_savings': self.total_savings,
            'routes_searched': self.routes_searched,
            'watchlist': [item.to_dict() for item in self.watchlist],
            'achievements': [a.to_dict() for a in self.achievements],
            'created_at': self.created_at,
            'last_active': self.last_active,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserProfile':
        """Crea instancia desde dict."""
        # Parse watchlist
        watchlist = [WatchlistItem.from_dict(item) for item in data.get('watchlist', [])]
        
        # Parse achievements
        achievements = [Achievement.from_dict(a) for a in data.get('achievements', [])]
        
        return cls(
            user_id=data['user_id'],
            username=data['username'],
            coins=data.get('coins', 0),
            tier=UserTier(data.get('tier', 'bronze')),
            current_streak=data.get('current_streak', 0),
            longest_streak=data.get('longest_streak', 0),
            last_daily_claim=data.get('last_daily_claim'),
            total_searches=data.get('total_searches', 0),
            total_deals_found=data.get('total_deals_found', 0),
            total_savings=data.get('total_savings', 0.0),
            routes_searched=data.get('routes_searched', []),
            watchlist=watchlist,
            achievements=achievements,
            created_at=data.get('created_at'),
            last_active=data.get('last_active'),
        )


# ═══════════════════════════════════════════════════════════════
#  RETENTION MANAGER
# ═══════════════════════════════════════════════════════════════

class RetentionManager:
    """
    Gestor central del sistema de retención.
    
    Responsabilidades:
    - Gestión de perfiles de usuario
    - Daily rewards
    - Watchlist monitoring
    - Achievement tracking
    - Persistencia de datos
    """
    
    def __init__(self, data_file: str = 'user_profiles.json'):
        self.data_file = Path(data_file)
        self.profiles: Dict[int, UserProfile] = {}
        self._load_profiles()
        
        logger.info(f"🎮 RetentionManager initialized with {len(self.profiles)} profiles")
    
    def _load_profiles(self):
        """Carga perfiles desde JSON."""
        if not self.data_file.exists():
            logger.warning(f"⚠️ Profile file not found: {self.data_file}")
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for user_id_str, profile_data in data.items():
                user_id = int(user_id_str)
                self.profiles[user_id] = UserProfile.from_dict(profile_data)
            
            logger.info(f"✅ Loaded {len(self.profiles)} user profiles")
        
        except Exception as e:
            logger.error(f"❌ Error loading profiles: {e}")
    
    def _save_profiles(self):
        """Guarda perfiles a JSON."""
        try:
            data = {str(user_id): profile.to_dict() 
                   for user_id, profile in self.profiles.items()}
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"💾 Saved {len(self.profiles)} profiles")
        
        except Exception as e:
            logger.error(f"❌ Error saving profiles: {e}")
    
    def get_or_create_profile(self, user_id: int, username: str) -> UserProfile:
        """Obtiene perfil existente o crea uno nuevo."""
        if user_id not in self.profiles:
            profile = UserProfile(user_id=user_id, username=username)
            self.profiles[user_id] = profile
            self._save_profiles()
            logger.info(f"🆕 Created new profile for user {user_id} (@{username})")
        
        # Update last active
        self.profiles[user_id].last_active = datetime.now().isoformat()
        
        return self.profiles[user_id]
    
    def claim_daily(self, user_id: int, username: str) -> dict:
        """Procesa daily reward claim."""
        profile = self.get_or_create_profile(user_id, username)
        
        if not profile.can_claim_daily():
            hours_until = self._hours_until_next_claim(profile)
            return {
                'success': False,
                'error': 'already_claimed',
                'hours_until': hours_until
            }
        
        reward, streak, is_new = profile.claim_daily_reward()
        self._save_profiles()
        
        return {
            'success': True,
            'reward': reward,
            'streak': streak,
            'is_new_streak': is_new,
            'total_coins': profile.coins,
            'tier': profile.tier.value
        }
    
    def _hours_until_next_claim(self, profile: UserProfile) -> float:
        """Calcula horas hasta próximo claim disponible."""
        if not profile.last_daily_claim:
            return 0.0
        
        last_claim = datetime.fromisoformat(profile.last_daily_claim)
        next_claim = last_claim + timedelta(days=1)
        now = datetime.now()
        
        if now >= next_claim:
            return 0.0
        
        delta = next_claim - now
        return delta.total_seconds() / 3600
    
    def add_to_watchlist(self, user_id: int, username: str, 
                        route: str, threshold: float) -> dict:
        """Añade ruta a watchlist del usuario."""
        profile = self.get_or_create_profile(user_id, username)
        
        try:
            profile.add_to_watchlist(route, threshold)
            self._save_profiles()
            
            return {
                'success': True,
                'watchlist_count': len(profile.watchlist),
                'max_slots': TIER_BENEFITS[profile.tier]['watchlist_slots']
            }
        
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def remove_from_watchlist(self, user_id: int, route: str) -> bool:
        """Elimina ruta de watchlist."""
        if user_id not in self.profiles:
            return False
        
        removed = self.profiles[user_id].remove_from_watchlist(route)
        if removed:
            self._save_profiles()
        
        return removed
    
    def get_watchlist(self, user_id: int) -> List[WatchlistItem]:
        """Obtiene watchlist del usuario."""
        if user_id not in self.profiles:
            return []
        
        return self.profiles[user_id].watchlist
    
    def track_search(self, user_id: int, username: str, route: str):
        """Registra búsqueda de usuario."""
        profile = self.get_or_create_profile(user_id, username)
        profile.total_searches += 1
        
        # Track unique routes
        if route not in profile.routes_searched:
            profile.routes_searched.append(route)
        
        # Award coins (first search of day)
        if profile.total_searches % 10 == 1:  # Cada 10 búsquedas
            profile.add_coins(COIN_REWARDS['first_search'], 'search_milestone')
        
        # Check achievements
        self._check_search_achievements(profile)
        
        self._save_profiles()
    
    def track_deal_found(self, user_id: int, username: str, savings: float):
        """Registra deal encontrado."""
        profile = self.get_or_create_profile(user_id, username)
        profile.total_deals_found += 1
        profile.total_savings += savings
        
        profile.add_coins(COIN_REWARDS['deal_found'], 'deal_found')
        
        # Check achievements
        self._check_deal_achievements(profile)
        
        self._save_profiles()
    
    def _check_search_achievements(self, profile: UserProfile):
        """Verifica achievements de búsqueda."""
        if len(profile.routes_searched) >= 20:
            profile.unlock_achievement(AchievementType.GLOBE_TROTTER)
        
        if profile.total_searches >= 100:
            profile.unlock_achievement(AchievementType.SPEED_DEMON)
    
    def _check_deal_achievements(self, profile: UserProfile):
        """Verifica achievements de deals."""
        if profile.total_deals_found >= 10:
            profile.unlock_achievement(AchievementType.DEAL_HUNTER)
        
        if profile.total_savings >= 1000:
            profile.unlock_achievement(AchievementType.MONEY_SAVER)


if __name__ == '__main__':
    # 🧪 Tests rápidos
    print("🧪 Testing RetentionManager...\n")
    
    mgr = RetentionManager('test_profiles.json')
    
    # Test 1: Crear perfil
    print("1. Creating profile...")
    result = mgr.claim_daily(12345, 'testuser')
    print(f"   Daily claim: {result}\n")
    
    # Test 2: Watchlist
    print("2. Adding to watchlist...")
    result = mgr.add_to_watchlist(12345, 'testuser', 'MAD-MIA', 450.0)
    print(f"   Watchlist: {result}\n")
    
    # Test 3: Track search
    print("3. Tracking search...")
    mgr.track_search(12345, 'testuser', 'MAD-BCN')
    profile = mgr.profiles[12345]
    print(f"   Total searches: {profile.total_searches}")
    print(f"   Coins: {profile.coins}\n")
    
    print("✅ All tests completed!")
